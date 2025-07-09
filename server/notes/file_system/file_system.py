import glob
import os
import re
import shutil
import string
import time
from datetime import datetime
from typing import List, Literal, Set, Tuple
import random

import whoosh
from whoosh import writing
from whoosh.analysis import CharsetFilter, StemmingAnalyzer, StandardAnalyzer
from whoosh.fields import DATETIME, ID, KEYWORD, TEXT, SchemaClass
from whoosh.highlight import ContextFragmenter, WholeFragmenter
from whoosh.index import Index, LockError
from whoosh.qparser import MultifieldParser
from whoosh.qparser.dateparse import DateParserPlugin
from whoosh.query import Every
from whoosh.searching import Hit
from whoosh.support.charset import accent_map

from helpers import get_env, parse_markdown_with_frontmatter, create_markdown_with_frontmatter
from logger import logger

from ..base import BaseNotes
from ..models import Note, NoteCreate, NoteUpdate, SearchResult

MARKDOWN_EXT = ".md"
INDEX_SCHEMA_VERSION = "9"

# Use StandardAnalyzer for more flexible matching
StemmingFoldingAnalyzer = StandardAnalyzer() | CharsetFilter(accent_map)


def generate_random_filename(length: int = 8) -> str:
    """Generate a random filename with specified length."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


class IndexSchema(SchemaClass):
    filename = ID(unique=True, stored=True)
    last_modified = DATETIME(stored=True, sortable=True)
    created_date = DATETIME(stored=True, sortable=True)
    title = TEXT(
        field_boost=2.0, analyzer=StemmingFoldingAnalyzer, sortable=True
    )
    content = TEXT(analyzer=StemmingFoldingAnalyzer)
    tags = KEYWORD(lowercase=False, field_boost=2.0)
    category = KEYWORD(lowercase=False, field_boost=1.5)
    visibility = KEYWORD(lowercase=False, field_boost=1.5)


class FileSystemNotes(BaseNotes):
    TAGS_RE = re.compile(r"(?:^|\s)#([a-zA-Z0-9_\-\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+)(?=\s|$)")
    CODEBLOCK_RE = re.compile(r"`{1,3}.*?`{1,3}", re.DOTALL)
    TAGS_WITH_HASH_RE = re.compile(
        r"(?:(?<=^)|(?<=\s))#[a-zA-Z0-9_\-\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+(?=\s|$)"
    )

    def __init__(self):
        self.base_path = get_env("SBNOTE_PATH", mandatory=True)
        if not os.path.exists(self.base_path):
            raise NotADirectoryError(
                f"'{self.base_path}' is not a valid directory."
            )
        # Create notes subdirectory for markdown files
        self.storage_path = os.path.join(self.base_path, "notes")
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize both indexes
        self.main_index = self._load_index("main")
        self.public_index = self._load_index("public")
        self._sync_index_with_retry(optimize=True)

    def create(self, data: NoteCreate) -> Note:
        """Create a new note."""
        # Generate random filename
        filename = generate_random_filename()
        while os.path.exists(os.path.join(self.storage_path, filename + MARKDOWN_EXT)):
            filename = generate_random_filename()
        
        filepath = os.path.join(self.storage_path, filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=data.title,
            content=data.content or "",
            tags=data.tags or [],
            created=created_time,
            category="note",
            visibility="private"
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=data.title,
            content=data.content,
            last_modified=os.path.getmtime(filepath),
            created=created_time.timestamp(),
            tags=data.tags or [],
            filename=filename + MARKDOWN_EXT,
        )

    def get(self, filename: str) -> Note:
        # Add extension if not present
        if not filename.endswith(MARKDOWN_EXT):
            filename += MARKDOWN_EXT
        
        # Special handling for README.md - use the app's README.md
        if filename.lower() == 'readme.md':
            # Get the app root directory (parent of storage_path)
            app_root = os.path.dirname(os.path.dirname(os.path.dirname(self.storage_path)))
            filepath = os.path.join(app_root, 'README.md')
            
            # Check if README.md exists in app root
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"README.md not found in app root: {filepath}")
        else:
            filepath = os.path.join(self.storage_path, filename)
        
        content = self._read_file(filepath)
        
        # Parse frontmatter
        metadata, body = parse_markdown_with_frontmatter(content)
        
        # Parse created date from frontmatter
        created_time = None
        if 'created_date' in metadata:
            try:
                created_time = datetime.strptime(metadata['created_date'], '%Y-%m-%d %H:%M:%S').timestamp()
            except (ValueError, TypeError):
                # Fallback to file creation time if parsing fails
                created_time = os.path.getctime(filepath)
        else:
            # Fallback to file creation time if no created_date field
            created_time = os.path.getctime(filepath)
        
        return Note(
            title=metadata.get('title', self._strip_ext(filename)),
            content=body,
            last_modified=os.path.getmtime(filepath),
            created=created_time,
            tags=metadata.get('tags', []),
            filename=filename,
            category=metadata.get('category', 'note'),
            visibility=metadata.get('visibility', 'private'),
        )

    def update(self, filename: str, data: NoteUpdate) -> Note:
        # Add extension if not present
        if not filename.endswith(MARKDOWN_EXT):
            filename += MARKDOWN_EXT
        filepath = os.path.join(self.storage_path, filename)
        
        # Read existing content and parse frontmatter
        existing_content = self._read_file(filepath)
        metadata, body = parse_markdown_with_frontmatter(existing_content)
        
        # Store old visibility for index update logic
        old_visibility = metadata.get('visibility', 'private')
        
        # Update metadata (file name stays the same, only frontmatter changes)
        if data.new_title is not None:
            metadata['title'] = data.new_title
        
        # Update content - handle both None and empty string cases
        if hasattr(data, 'new_content') and data.new_content is not None:
            body = data.new_content
        
        if data.tags is not None:
            metadata['tags'] = data.tags
        
        # Create new markdown with updated frontmatter
        # createdはdatetime型で渡す必要がある
        created_dt = None
        if 'created_date' in metadata and metadata['created_date']:
            if isinstance(metadata['created_date'], datetime):
                created_dt = metadata['created_date']
            else:
                try:
                    created_dt = datetime.strptime(metadata['created_date'], '%Y-%m-%d %H:%M:%S')
                except Exception:
                    created_dt = datetime.fromtimestamp(os.path.getctime(filepath))
        else:
            created_dt = datetime.fromtimestamp(os.path.getctime(filepath))

        markdown_content = create_markdown_with_frontmatter(
            title=metadata.get('title', self._strip_ext(filename)),
            content=body,
            tags=metadata.get('tags', []),
            created=created_dt
        )
        
        self._write_file(filepath, markdown_content, overwrite=True)
        
        # Update the search indexes with visibility change handling
        self._sync_index_with_retry(visibility_changed=(old_visibility != metadata.get('visibility', 'private')))
        
        # Parse created date from frontmatter
        created_time = None
        if 'created_date' in metadata:
            try:
                created_time = datetime.strptime(metadata['created_date'], '%Y-%m-%d %H:%M:%S').timestamp()
            except (ValueError, TypeError):
                # Fallback to file creation time if parsing fails
                created_time = os.path.getctime(filepath)
        else:
            # Fallback to file creation time if no created_date field
            created_time = os.path.getctime(filepath)
        
        return Note(
            title=metadata.get('title', self._strip_ext(filename)),
            content=body,
            last_modified=os.path.getmtime(filepath),
            created=created_time,
            tags=metadata.get('tags', []),
            filename=filename,
            category=metadata.get('category', 'note'),
            visibility=metadata.get('visibility', 'private'),
        )

    def delete(self, filename: str) -> None:
        # Add extension if not present
        if not filename.endswith(MARKDOWN_EXT):
            filename += MARKDOWN_EXT
        filepath = os.path.join(self.storage_path, filename)
        os.remove(filepath)
        
        # Update the search index
        self._sync_index_with_retry()

    def search(
        self,
        term: str,
        sort: Literal["score", "title", "last_modified", "created_date", "category", "visibility"] = "score",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        content_limit: int = None,
        use_public_index: bool = False,
    ) -> Tuple[SearchResult, ...]:
        """Search the index for the given term."""
        self._sync_index_with_retry()
        
        # Choose the appropriate index based on use_public_index parameter
        index_to_use = self.public_index if use_public_index else self.main_index
        
        # Check if this is a search for "_untagged" tag
        original_term = term.strip()
        if original_term == "#_untagged" or original_term == "tags:_untagged":
            # Special handling for _untagged tag - return notes without tags
            with index_to_use.searcher() as searcher:
                # Get all notes and filter those without tags
                query = Every()
                
                # Determine sort field
                sort_field = sort if sort in ["title", "last_modified", "created_date", "category", "visibility"] else None
                
                # Determine sort direction
                reverse = order == "desc"
                if sort_field is None:
                    reverse = not reverse
                
                # Run search to get all notes
                results = searcher.search(
                    query,
                    sortedby=sort_field,
                    reverse=reverse,
                    limit=None,  # Get all notes to filter
                    terms=True,
                )
                
                # Filter results to only include notes without tags
                filtered_results = []
                for hit in results:
                    filename = hit["filename"]
                    filepath = os.path.join(self.storage_path, filename)
                    content = self._read_file(filepath)
                    metadata, body = parse_markdown_with_frontmatter(content)
                    
                    # Only include notes without tags
                    if not metadata.get('tags', []):
                        filtered_results.append(hit)
                
                # Apply limit after filtering
                if limit:
                    filtered_results = filtered_results[:limit]
                
                return tuple(self._search_result_from_hit(hit, content_limit) for hit in filtered_results)
        
        # Regular search processing
        term = self._pre_process_search_term(term)
        with index_to_use.searcher() as searcher:
            # Parse Query
            if term == "*":
                query = Every()
            else:
                parser = MultifieldParser(
                    self._fieldnames_for_term(term), index_to_use.schema
                )
                parser.add_plugin(DateParserPlugin())
                
                # Add fuzzy search and wildcard support
                from whoosh.qparser import FuzzyTermPlugin, WildcardPlugin
                # Configure fuzzy search with distance 3 (allows more character differences)
                fuzzy_plugin = FuzzyTermPlugin()
                fuzzy_plugin.maxdist = 3
                parser.add_plugin(fuzzy_plugin)
                parser.add_plugin(WildcardPlugin())
                
                query = parser.parse(term)

            # Determine Sort By
            # Note: For the 'sort' option, "score" is converted to None as
            # that is the default for searches anyway and it's quicker for
            # Whoosh if you specify None.
            sort = sort if sort in ["title", "last_modified", "created_date", "category", "visibility"] else None

            # Determine Sort Direction
            # Note: Confusingly, when sorting by 'score', reverse = True means
            # asc so we have to flip the logic for that case!
            reverse = order == "desc"
            if sort is None:
                reverse = not reverse

            # Run Search
            results = searcher.search(
                query,
                sortedby=sort,
                reverse=reverse,
                limit=limit,
                terms=True,
            )
            return tuple(self._search_result_from_hit(hit, content_limit) for hit in results)

    def get_tags(self, use_public_index: bool = False) -> list[str]:
        """Return a list of all indexed tags. Note: Tags no longer in use will
        only be cleared when the index is next optimized."""
        self._sync_index_with_retry()
        index_to_use = self.public_index if use_public_index else self.main_index
        with index_to_use.reader() as reader:
            tags = reader.field_terms("tags")
            return [tag for tag in tags]

    def list_notes(
        self,
        sort: Literal["title", "last_modified", "created_date", "category", "visibility"] = "last_modified",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        use_public_index: bool = False,
    ) -> list[Note]:
        """Get a list of all notes."""
        self._sync_index_with_retry()
        index_to_use = self.public_index if use_public_index else self.main_index
        with index_to_use.searcher() as searcher:
            # Use Every() query to get all documents
            query = Every()
            
            # Determine sort field
            sort_field = sort if sort in ["title", "last_modified", "created_date", "category", "visibility"] else "last_modified"
            
            # Determine sort direction
            reverse = order == "desc"
            
            # Run search
            results = searcher.search(
                query,
                sortedby=sort_field,
                reverse=reverse,
                limit=limit,
            )
            
            # Convert to Note objects
            notes = []
            for hit in results:
                filename = hit["filename"]
                filepath = os.path.join(self.storage_path, filename)
                content = self._read_file(filepath)
                metadata, body = parse_markdown_with_frontmatter(content)
                
                notes.append(Note(
                    title=metadata.get('title', self._strip_ext(filename)),
                    content=body,
                    last_modified=hit["last_modified"].timestamp(),
                    tags=metadata.get('tags', []),
                    filename=filename,
                ))
            
            return notes

    def get_notes_by_tag(
        self,
        tag_name: str,
        sort: Literal["title", "last_modified", "created_date", "category", "visibility"] = "last_modified",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        use_public_index: bool = False,
    ) -> list[Note]:
        """Get notes that have a specific tag."""
        self._sync_index_with_retry()
        index_to_use = self.public_index if use_public_index else self.main_index
        
        # Special handling for "_untagged" tag - return notes without tags
        if tag_name == "_untagged":
            with index_to_use.searcher() as searcher:
                # Get all notes and filter those without tags
                from whoosh.query import Every
                query = Every()
                
                # Determine sort field
                sort_field = sort if sort in ["title", "last_modified", "created_date", "category", "visibility"] else "last_modified"
                
                # Determine sort direction
                reverse = order == "desc"
                
                # Run search to get all notes
                results = searcher.search(
                    query,
                    sortedby=sort_field,
                    reverse=reverse,
                    limit=None,  # Get all notes to filter
                )
                
                # Convert to Note objects and filter those without tags
                notes = []
                for hit in results:
                    filename = hit["filename"]
                    filepath = os.path.join(self.storage_path, filename)
                    content = self._read_file(filepath)
                    metadata, body = parse_markdown_with_frontmatter(content)
                    
                    # Only include notes without tags
                    if not metadata.get('tags', []):
                        notes.append(Note(
                            title=metadata.get('title', self._strip_ext(filename)),
                            content=body,
                            last_modified=hit["last_modified"].timestamp(),
                            tags=metadata.get('tags', []),
                            filename=filename,
                        ))
                
                # Apply limit after filtering
                if limit:
                    notes = notes[:limit]
                
                return notes
        
        # Regular tag search
        with index_to_use.searcher() as searcher:
            # Search for notes with the specific tag
            from whoosh.query import Term
            query = Term("tags", tag_name)
            
            # Determine sort field
            sort_field = sort if sort in ["title", "last_modified", "created_date", "category", "visibility"] else "last_modified"
            
            # Determine sort direction
            reverse = order == "desc"
            
            # Run search
            results = searcher.search(
                query,
                sortedby=sort_field,
                reverse=reverse,
                limit=limit,
            )
            
            # Convert to Note objects
            notes = []
            for hit in results:
                filename = hit["filename"]
                filepath = os.path.join(self.storage_path, filename)
                content = self._read_file(filepath)
                metadata, body = parse_markdown_with_frontmatter(content)
                
                notes.append(Note(
                    title=metadata.get('title', self._strip_ext(filename)),
                    content=body,
                    last_modified=hit["last_modified"].timestamp(),
                    tags=metadata.get('tags', []),
                    filename=filename,
                ))
            
            return notes

    @property
    def _index_path(self):
        return os.path.join(self.base_path, "index")

    @property
    def _main_index_path(self):
        return os.path.join(self.base_path, "index", "main")

    @property
    def _public_index_path(self):
        return os.path.join(self.base_path, "index", "public")



    def _get_by_filename(self, filename: str) -> Note:
        """Get a note by its filename."""
        filepath = os.path.join(self.storage_path, filename)
        content = self._read_file(filepath)
        metadata, body = parse_markdown_with_frontmatter(content)
        
        # Parse created date from frontmatter
        created_time = None
        if 'created_date' in metadata:
            try:
                created_time = datetime.strptime(metadata['created_date'], '%Y-%m-%d %H:%M:%S').timestamp()
            except (ValueError, TypeError):
                # Fallback to file creation time if parsing fails
                created_time = os.path.getctime(filepath)
        else:
            # Fallback to file creation time if no created_date field
            created_time = os.path.getctime(filepath)
        
        return Note(
            title=metadata.get('title', self._strip_ext(filename)),
            content=body,
            last_modified=os.path.getmtime(filepath),
            created=created_time,
            tags=metadata.get('tags', []),
            filename=filename,
            category=metadata.get('category', 'note'),
            visibility=metadata.get('visibility', 'private'),
        )

    def _load_index(self, index_name: str) -> Index:
        """Load the note index or create new if not exists."""
        if index_name == "main":
            index_path = self._main_index_path
        elif index_name == "public":
            index_path = self._public_index_path
        else:
            raise ValueError(f"Unknown index name: {index_name}")
        
        index_dir_exists = os.path.exists(index_path)
        if index_dir_exists and whoosh.index.exists_in(
            index_path, indexname=INDEX_SCHEMA_VERSION
        ):
            logger.info(f"Loading existing {index_name} index")
            return whoosh.index.open_dir(
                index_path, indexname=INDEX_SCHEMA_VERSION
            )
        else:
            if index_dir_exists:
                logger.info(f"Deleting outdated {index_name} index")
                self._clear_dir(index_path)
            else:
                os.makedirs(index_path, exist_ok=True)
            logger.info(f"Creating new {index_name} index")
            return whoosh.index.create_in(
                index_path, IndexSchema, indexname=INDEX_SCHEMA_VERSION
            )

    @classmethod
    def _extract_tags(cls, content) -> Tuple[str, Set[str]]:
        """Strip tags from the given content and return a tuple consisting of:

        - The content without the tags.
        - A set of tags converted to lowercase."""
        content_ex_codeblock = re.sub(cls.CODEBLOCK_RE, "", content)
        tags = cls.TAGS_RE.findall(content_ex_codeblock)
        content_ex_tags = cls.TAGS_RE.sub("", content)
        try:
            # Don't convert Japanese tags to lowercase
            processed_tags = []
            for tag in tags:
                # Only convert to lowercase if the tag contains only ASCII characters
                if tag.isascii():
                    processed_tags.append(tag.lower())
                else:
                    processed_tags.append(tag)
            return (content_ex_tags, set(processed_tags))
        except IndexError:
            return (content, set())

    def _add_note_to_index(
        self, writer: writing.IndexWriter, note: Note
    ) -> None:
        """Add a Note object to the index using the given writer. If the
        filename already exists in the index an update will be performed
        instead."""
        tag_string = " ".join(note.tags or [])
        writer.update_document(
            filename=note.filename or note.title + MARKDOWN_EXT,
            last_modified=datetime.fromtimestamp(note.last_modified),
            created_date=datetime.fromtimestamp(note.created) if note.created else datetime.fromtimestamp(note.last_modified),
            title=note.title,
            content=note.content,
            tags=tag_string,
            category=getattr(note, 'category', 'note'),
            visibility=getattr(note, 'visibility', 'private'),
        )

    def _list_all_note_filenames(self) -> List[str]:
        """Return a list of all note filenames."""
        return [
            os.path.split(filepath)[1]
            for filepath in glob.glob(
                os.path.join(self.storage_path, "*" + MARKDOWN_EXT)
            )
        ]

    def _sync_index(self, optimize: bool = False, clean: bool = False, visibility_changed: bool = False) -> None:
        """Synchronize both indexes with the notes directory.
        Specify clean=True to completely rebuild the indexes"""
        
        # Sync main index (always updated)
        self._sync_main_index(optimize=optimize, clean=clean)
        
        # Sync public index (conditionally updated)
        if clean or visibility_changed:
            self._sync_public_index(optimize=optimize, clean=clean)
        else:
            # For regular updates, only sync public index if there are changes
            self._sync_public_index_if_needed(optimize=optimize)

    def _sync_main_index(self, optimize: bool = False, clean: bool = False) -> None:
        """Synchronize the main index with the notes directory."""
        indexed = set()
        writer = self.main_index.writer()
        if clean:
            writer.mergetype = writing.CLEAR  # Clear the index
        with self.main_index.searcher() as searcher:
            for idx_note in searcher.all_stored_fields():
                idx_filename = idx_note["filename"]
                idx_filepath = os.path.join(self.storage_path, idx_filename)
                # Delete missing
                if not os.path.exists(idx_filepath):
                    writer.delete_by_term("filename", idx_filename)
                    logger.info(f"'{idx_filename}' removed from main index")
                # Update modified
                elif (
                    datetime.fromtimestamp(os.path.getmtime(idx_filepath))
                    != idx_note["last_modified"]
                ):
                    logger.info(f"'{idx_filename}' updated in main index")
                    self._add_note_to_index(
                        writer, self._get_by_filename(idx_filename)
                    )
                    indexed.add(idx_filename)
                # Ignore already indexed
                else:
                    indexed.add(idx_filename)
        # Add new
        for filename in self._list_all_note_filenames():
            if filename not in indexed:
                self._add_note_to_index(
                    writer, self._get_by_filename(filename)
                )
                logger.info(f"'{filename}' added to main index")
        writer.commit(optimize=optimize)
        logger.info("Main index synchronized")

    def _sync_public_index(self, optimize: bool = False, clean: bool = False) -> None:
        """Synchronize the public index with public notes only."""
        writer = self.public_index.writer()
        if clean:
            writer.mergetype = writing.CLEAR  # Clear the index
        
        # Get all notes and filter for public ones
        public_notes = []
        for filename in self._list_all_note_filenames():
            note = self._get_by_filename(filename)
            if getattr(note, 'visibility', 'private') == 'public':
                public_notes.append(note)
        
        # Add all public notes to the index
        for note in public_notes:
            self._add_note_to_index(writer, note)
            logger.info(f"'{note.filename}' added to public index")
        
        writer.commit(optimize=optimize)
        logger.info(f"Public index synchronized with {len(public_notes)} notes")

    def _sync_public_index_if_needed(self, optimize: bool = False) -> None:
        """Sync public index only if there are changes in public notes."""
        # Check if public index needs updating by comparing with main index
        with self.main_index.searcher() as main_searcher:
            with self.public_index.searcher() as public_searcher:
                main_public_notes = set()
                for note in main_searcher.all_stored_fields():
                    if note.get('visibility') == 'public':
                        main_public_notes.add(note['filename'])
                
                public_notes = set()
                for note in public_searcher.all_stored_fields():
                    public_notes.add(note['filename'])
                
                # If there are differences, sync the public index
                if main_public_notes != public_notes:
                    logger.info("Public index out of sync, updating...")
                    self._sync_public_index(optimize=optimize)

    def _sync_index_with_retry(
        self,
        optimize: bool = False,
        clean: bool = False,
        max_retries: int = 8,
        retry_delay: float = 0.25,
        visibility_changed: bool = False,
    ) -> None:
        for _ in range(max_retries):
            try:
                self._sync_index(optimize=optimize, clean=clean)
                return
            except LockError:
                logger.warning(f"Index locked, retrying in {retry_delay}s")
                time.sleep(retry_delay)
        logger.error(f"Failed to sync index after {max_retries} retries")

    @classmethod
    def _pre_process_search_term(cls, term):
        term = term.strip()
        # Replace "#tagname" with "tags:tagname"
        term = re.sub(
            cls.TAGS_WITH_HASH_RE,
            lambda tag: "tags:" + tag.group(0)[1:],
            term,
        )
        
        # Add wildcard support for partial matches
        # If the term doesn't already contain wildcards and is not a phrase
        if '*' not in term and '~' not in term and '"' not in term and len(term) > 0:
            # Add wildcard to the end for partial matching
            # But only if it's not already a field-specific search
            if ':' not in term:
                # For very short terms (2 characters or less), use both wildcard and fuzzy
                if len(term) <= 2:
                    term = term + '*' + ' OR ' + term + '~'
                else:
                    # Use wildcard for longer terms
                    term = term + '*'
        
        return term

    @staticmethod
    def _re_extract(pattern, string) -> Tuple[str, List[str]]:
        """Similar to re.sub but returns a tuple of:

        - `string` with matches removed
        - list of matches"""
        matches = []
        text = re.sub(pattern, lambda tag: matches.append(tag.group()), string)
        return (text, matches)

    @staticmethod
    def _strip_ext(filename):
        """Return the given filename without the extension."""
        return os.path.splitext(filename)[0]

    @staticmethod
    def _clear_dir(path):
        """Delete all contents of the given directory."""
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

    def _search_result_from_hit(self, hit: Hit, content_limit: int = None):
        matched_fields = self._get_matched_fields(hit.matched_terms())

        filename = hit["filename"]
        filepath = os.path.join(self.storage_path, filename)
        content = self._read_file(filepath)
        metadata, body = parse_markdown_with_frontmatter(content)
        title = metadata.get('title', self._strip_ext(filename))
        last_modified = hit["last_modified"].timestamp()

        # If the search was ordered using a text field then hit.score is the
        # value of that field. This isn't useful so only set self._score if it
        # is a float.
        score = hit.score if type(hit.score) is float else None

        if "title" in matched_fields:
            hit.results.fragmenter = WholeFragmenter()
            title_highlights = hit.highlights("title", text=title, top=1)
            # Replace Whoosh highlight tags with mark tags for better semantic meaning
            if title_highlights:
                # Replace all variations of Whoosh highlight tags
                title_highlights = re.sub(r'<b[^>]*>', '<mark class="highlight">', title_highlights)
                title_highlights = title_highlights.replace('</b>', '</mark>')
        else:
            title_highlights = None

        if "content" in matched_fields:
            hit.results.fragmenter = ContextFragmenter(charlimit=200, surround=50)
            content_ex_tags, _ = FileSystemNotes._extract_tags(body)
            content_highlights = hit.highlights(
                "content",
                text=content_ex_tags,
                top=2,  # Show up to 2 fragments to increase chance of finding matches
            )
            # Replace Whoosh highlight tags with mark tags for better semantic meaning
            if content_highlights:
                # Replace all variations of Whoosh highlight tags
                content_highlights = re.sub(r'<b[^>]*>', '<mark class="highlight">', content_highlights)
                content_highlights = content_highlights.replace('</b>', '</mark>')
            else:
                # If no highlights generated, show a snippet of the content
                content_highlights = content_ex_tags[:100] + ('...' if len(content_ex_tags) > 100 else '')
        else:
            content_highlights = None

        tag_matches = (
            [field[1] for field in hit.matched_terms() if field[0] == "tags"]
            if "tags" in matched_fields
            else None
        )

        # Limit content if content_limit is specified
        if content_limit and body and len(body) > content_limit:
            limited_content = body[:content_limit] + "..."
        else:
            limited_content = body

        return SearchResult(
            title=title,
            content=limited_content,
            last_modified=last_modified,
            filename=filename,
            score=score,
            title_highlights=title_highlights,
            content_highlights=content_highlights,
            tag_matches=tag_matches,
        )

    def _fieldnames_for_term(self, term: str) -> List[str]:
        """Return a list of field names to search based on the given term. If
        the term includes a phrase then only search title and content. If the
        term does not include a phrase then also search tags."""
        fields = ["title", "content", "category", "visibility"]
        if '"' not in term:
            # If the term does not include a phrase then also search tags
            fields.append("tags")
        return fields

    @staticmethod
    def _get_matched_fields(matched_terms):
        """Return a set of matched fields from a set of ('field', 'term') "
        "tuples generated by whoosh.searching.Hit.matched_terms()."""
        return set([matched_term[0] for matched_term in matched_terms])

    @staticmethod
    def _read_file(filepath: str):
        logger.debug(f"Reading from '{filepath}'")
        with open(filepath, "r") as f:
            content = f.read()
        return content

    @staticmethod
    def _write_file(filepath: str, content: str, overwrite: bool = False):
        logger.debug(f"Writing to '{filepath}'")
        with open(filepath, "w" if overwrite else "x") as f:
            f.write(content)
