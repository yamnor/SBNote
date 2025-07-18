import glob
import os
import re
import shutil
import string
import time
import asyncio
import pickle
from datetime import datetime
from typing import List, Literal, Set, Tuple, Optional
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

# Try to import cclib, but don't fail if it's not available
try:
    import cclib
    CCLIB_AVAILABLE = True
except ImportError:
    CCLIB_AVAILABLE = False

def _create_xyz_file(data_obj, xyz_file_path):
    """Create xyz file from cclib data object using writexyz() method."""
    try:
        # Check if writexyz method is available
        if not hasattr(data_obj, 'writexyz'):
            logger.warning("writexyz method not available in cclib data object")
            return False
        
        # Generate xyz content using cclib's writexyz method
        # This will use the last (final) coordinate set by default
        xyz_content = data_obj.writexyz()
        
        # Write xyz file
        with open(xyz_file_path, 'w') as f:
            f.write(xyz_content)
        
        return True
        
    except Exception as e:
        logger.warning(f"Failed to create xyz file: {str(e)}")
        return False

from helpers import get_env, parse_markdown_with_frontmatter, create_markdown_with_frontmatter
from logger import logger

from ..base import BaseNotes
from ..models import Note, NoteCreate, NoteUpdate, NoteImport, NoteImageImport, NoteXyzImport, NotePlaintextImport, NotePasteImport, SearchResult
from ..git_history import GitHistoryManager

MARKDOWN_EXT = ".md"
INDEX_SCHEMA_VERSION = "10"

# Use StandardAnalyzer for more flexible matching
StemmingFoldingAnalyzer = StandardAnalyzer() | CharsetFilter(accent_map)


def generate_random_filename(length: int = 8) -> str:
    """Generate a random filename with specified length."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


class IndexSchema(SchemaClass):
    filename = ID(unique=True, stored=True)
    last_modified = DATETIME(stored=True, sortable=True)
    created_time = DATETIME(stored=True, sortable=True)
    title = TEXT(
        field_boost=2.0, analyzer=StemmingFoldingAnalyzer, sortable=True
    )
    content = TEXT(analyzer=StemmingFoldingAnalyzer)
    tags = KEYWORD(lowercase=False, field_boost=2.0)
    category = KEYWORD(lowercase=False, field_boost=1.5)
    visibility = KEYWORD(lowercase=False, field_boost=1.5)
    attachment_extension = KEYWORD(lowercase=False, field_boost=1.0)


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
        
        # Initialize Git history manager
        self.git_manager = GitHistoryManager(self.base_path)
        self.git_manager._initialize_git_repository()
        
        # Initialize both indexes
        self.main_index = self._load_index("main")
        self.public_index = self._load_index("public")
        logger.info("Initializing indexes...")
        self._sync_index_with_retry(optimize=True, clean=True)
        logger.info("Index initialization completed")

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
            category=getattr(data, 'category', 'note'),
            visibility=getattr(data, 'visibility', 'private')
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        # Git commit (non-blocking)
        try:
            # 同期的なコンテキストで非同期処理を実行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # イベントループが実行中の場合は、バックグラウンドタスクとして実行
                loop.create_task(self.git_manager.commit_note_change(filename + MARKDOWN_EXT, data))
            else:
                # イベントループが実行されていない場合は、新しいループで実行
                asyncio.run(self.git_manager.commit_note_change(filename + MARKDOWN_EXT, data))
        except RuntimeError:
            # イベントループが取得できない場合は、スレッドプールで実行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(asyncio.run, self.git_manager.commit_note_change(filename + MARKDOWN_EXT, data))
        
        return Note(
            title=data.title,
            content=data.content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=filename + MARKDOWN_EXT,
        )

    def import_note(self, data: NoteImport) -> Note:
        """Import a markdown file as a new note."""
        # Parse content to remove frontmatter
        metadata, body = parse_markdown_with_frontmatter(data.content)
        
        # Generate title from first line of content if not provided
        title = metadata.get('title', '')
        if not title:
            # Extract title from first non-empty line
            lines = body.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    # Remove markdown formatting
                    title = line.lstrip('#').strip()
                    break
        
        if not title:
            title = "Imported Note"
        
        # Generate random filename
        filename = generate_random_filename()
        while os.path.exists(os.path.join(self.storage_path, filename + MARKDOWN_EXT)):
            filename = generate_random_filename()
        
        filepath = os.path.join(self.storage_path, filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Create markdown with frontmatter (ignore original frontmatter)
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=body,
            tags=data.tags or [],
            created=created_time,
            category="note",
            visibility="private"
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        # Git commit (non-blocking)
        try:
            # 同期的なコンテキストで非同期処理を実行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # イベントループが実行中の場合は、バックグラウンドタスクとして実行
                loop.create_task(self.git_manager.commit_note_change(filename + MARKDOWN_EXT, data))
            else:
                # イベントループが実行されていない場合は、新しいループで実行
                asyncio.run(self.git_manager.commit_note_change(filename + MARKDOWN_EXT, data))
        except RuntimeError:
            # イベントループが取得できない場合は、スレッドプールで実行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(asyncio.run, self.git_manager.commit_note_change(filename + MARKDOWN_EXT, data))
        
        return Note(
            title=title,
            content=body,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=filename + MARKDOWN_EXT,
        )

    def import_image(self, data: NoteImageImport, filename: str) -> Note:
        """Import an image file and create a note with the image link."""
        # Generate title from original filename
        title = data.original_filename
        
        # Use the same filename as the attachment (without extension)
        note_filename = os.path.splitext(filename)[0]
        
        # Ensure filename is unique for markdown file
        while os.path.exists(os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)):
            # Add suffix if duplicate
            base_name = note_filename
            counter = 1
            while os.path.exists(os.path.join(self.storage_path, f"{base_name}_{counter}{MARKDOWN_EXT}")):
                counter += 1
            note_filename = f"{base_name}_{counter}"
        
        filepath = os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Extract attachment extension (without dot)
        attachment_extension = os.path.splitext(filename)[1].lstrip('.')
        
        # Create markdown content with original filename on first line and image link on third line
        content = f"{data.original_filename}\n\n![Image](/a/{note_filename})"
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=content,
            tags=data.tags or [],
            created=created_time,
            category="image",
            visibility="private",
            attachment_extension=attachment_extension
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=note_filename + MARKDOWN_EXT,
            attachment_extension=attachment_extension,
        )

    def import_xyz(self, data: NoteXyzImport, filename: str) -> Note:
        """Import an xyz file and create a note with the xyz file link."""
        # Generate title from original filename
        title = data.original_filename
        
        # Use the same filename as the attachment (without extension)
        note_filename = os.path.splitext(filename)[0]
        
        # Ensure filename is unique for markdown file
        while os.path.exists(os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)):
            # Add suffix if duplicate
            base_name = note_filename
            counter = 1
            while os.path.exists(os.path.join(self.storage_path, f"{base_name}_{counter}{MARKDOWN_EXT}")):
                counter += 1
            note_filename = f"{base_name}_{counter}"
        
        filepath = os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Extract attachment extension (without dot)
        attachment_extension = os.path.splitext(filename)[1].lstrip('.')
        
        # Create markdown content with original filename on first line and xyz file link on third line
        content = f"{data.original_filename}\n\n[Coordinate](/a/{note_filename})"
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=content,
            tags=data.tags or [],
            created=created_time,
            category="coordinate",
            visibility="private",
            attachment_extension=attachment_extension
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=note_filename + MARKDOWN_EXT,
            attachment_extension=attachment_extension,
        )

    def import_plaintext(self, data: NotePlaintextImport, filename: str) -> Note:
        """Import a plaintext file and create a note with the plaintext file link."""
        # Generate title from original filename
        title = data.original_filename
        
        # Use the same filename as the attachment (without extension)
        note_filename = os.path.splitext(filename)[0]
        
        # Ensure filename is unique for markdown file
        while os.path.exists(os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)):
            # Add suffix if duplicate
            base_name = note_filename
            counter = 1
            while os.path.exists(os.path.join(self.storage_path, f"{base_name}_{counter}{MARKDOWN_EXT}")):
                counter += 1
            note_filename = f"{base_name}_{counter}"
        
        filepath = os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Extract attachment extension (without dot)
        attachment_extension = os.path.splitext(filename)[1].lstrip('.')
        
        # Create markdown content with original filename on first line and plaintext file link on third line
        content = f"{data.original_filename}\n\n[Plaintext](/a/{note_filename})"
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=content,
            tags=data.tags or [],
            created=created_time,
            category="output",
            visibility="private",
            attachment_extension=attachment_extension
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=note_filename + MARKDOWN_EXT,
            attachment_extension=attachment_extension,
        )

    def import_paste(self, data: NotePasteImport, filename: str) -> Note:
        """Import a pasted text file and create a note with the text file link."""
        # Generate title from category (capitalized)
        title = data.category.capitalize()
        
        # Use the same filename as the attachment (without extension)
        note_filename = os.path.splitext(filename)[0]
        
        # Ensure filename is unique for markdown file
        while os.path.exists(os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)):
            # Add suffix if duplicate
            base_name = note_filename
            counter = 1
            while os.path.exists(os.path.join(self.storage_path, f"{base_name}_{counter}{MARKDOWN_EXT}")):
                counter += 1
            note_filename = f"{base_name}_{counter}"
        
        filepath = os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Extract attachment extension (without dot)
        attachment_extension = os.path.splitext(filename)[1].lstrip('.')
        
        # Use the category from the data
        category = data.category
        
        # Create markdown content with original filename on first line and text file link on third line
        content = f"{data.original_filename}\n\n[Text](/a/{note_filename})"
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=content,
            tags=data.tags or [],
            created=created_time,
            category=category,
            visibility="private",
            attachment_extension=attachment_extension
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=note_filename + MARKDOWN_EXT,
            attachment_extension=attachment_extension,
        )

    def import_image_new(self, data: NoteImageImport, basename: str, original_extension: str) -> Note:
        """Import an image file with new directory structure."""
        # Generate title from original filename
        title = data.original_filename
        
        # Use the provided basename
        note_filename = basename
        
        # Ensure filename is unique for markdown file
        while os.path.exists(os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)):
            # Add suffix if duplicate
            base_name = note_filename
            counter = 1
            while os.path.exists(os.path.join(self.storage_path, f"{base_name}_{counter}{MARKDOWN_EXT}")):
                counter += 1
            note_filename = f"{base_name}_{counter}"
        
        filepath = os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Use the original extension
        attachment_extension = original_extension
        
        # Create markdown content with original filename on first line and image link on third line
        content = f"{data.original_filename}\n\n![Image](/a/{note_filename})"
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=content,
            tags=data.tags or [],
            created=created_time,
            category="image",
            visibility="limited",
            attachment_extension=attachment_extension
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=note_filename + MARKDOWN_EXT,
            attachment_extension=attachment_extension,
        )

    def import_coordinate_new(self, data: NoteXyzImport, basename: str, original_extension: str) -> Note:
        """Import a coordinate file with new directory structure."""
        # Generate title from original filename
        title = data.original_filename
        
        # Use the provided basename
        note_filename = basename
        
        # Ensure filename is unique for markdown file
        while os.path.exists(os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)):
            # Add suffix if duplicate
            base_name = note_filename
            counter = 1
            while os.path.exists(os.path.join(self.storage_path, f"{base_name}_{counter}{MARKDOWN_EXT}")):
                counter += 1
            note_filename = f"{base_name}_{counter}"
        
        filepath = os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Use the original extension
        attachment_extension = original_extension
        
        # Create markdown content with original filename on first line and coordinate file link on third line
        content = f"{data.original_filename}\n\n[Coordinate](/a/{note_filename})"
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=content,
            tags=data.tags or [],
            created=created_time,
            category="coordinate",
            visibility="limited",
            attachment_extension=attachment_extension
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=note_filename + MARKDOWN_EXT,
            attachment_extension=attachment_extension,
        )

    def import_output_new(self, data: NotePlaintextImport, basename: str, original_extension: str) -> Note:
        """Import an output file with new directory structure."""
        # Generate title from original filename
        title = data.original_filename
        
        # Use the provided basename
        note_filename = basename
        
        # Ensure filename is unique for markdown file
        while os.path.exists(os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)):
            # Add suffix if duplicate
            base_name = note_filename
            counter = 1
            while os.path.exists(os.path.join(self.storage_path, f"{base_name}_{counter}{MARKDOWN_EXT}")):
                counter += 1
            note_filename = f"{base_name}_{counter}"
        
        filepath = os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Use the original extension
        attachment_extension = original_extension
        
        # Create markdown content with original filename on first line and output file link on third line
        content = f"{data.original_filename}\n\n[Output](/a/{note_filename})"
        
        # cclib processing
        if CCLIB_AVAILABLE:
            try:
                # Build file paths
                output_file_path = os.path.join(self.base_path, "files", basename, "output.txt")
                pickle_file_path = os.path.join(self.base_path, "files", basename, "output.pkl")
                
                # Check if output file exists
                if not os.path.exists(output_file_path):
                    raise FileNotFoundError(f"Output file not found: {output_file_path}")
                
                # Check if directory exists
                output_dir = os.path.dirname(output_file_path)
                if not os.path.exists(output_dir):
                    raise FileNotFoundError(f"Output directory not found: {output_dir}")
                
                # Parse with cclib
                parser = cclib.io.ccopen(output_file_path)
                if parser is None:
                    raise ValueError(f"cclib could not determine file format for: {output_file_path}")
                
                data_obj = parser.parse()
                if data_obj is None:
                    raise ValueError(f"cclib parsing failed for: {output_file_path}")
                
                # Save as pickle
                with open(pickle_file_path, 'wb') as f:
                    pickle.dump(data_obj, f)
                
                # Create xyz file from coordinates
                xyz_file_path = os.path.join(self.base_path, "files", basename, "output.xyz")
                xyz_created = _create_xyz_file(data_obj, xyz_file_path)
                
                # Add success message to content
                if xyz_created:
                    content += f"\n\n## cclib Processing\n✅ Successfully parsed and saved to `output.pkl`\n✅ Created `output.xyz` from final coordinates"
                else:
                    content += f"\n\n## cclib Processing\n✅ Successfully parsed and saved to `output.pkl`\n⚠️ Could not create `output.xyz` (no coordinates available)"
                
            except Exception as e:
                # Add error message to content
                error_msg = str(e)
                content += f"\n\n## cclib Processing\n❌ Error: {error_msg}"
                logger.warning(f"cclib processing failed for {basename}: {error_msg}")
                logger.warning(f"Output file path: {output_file_path if 'output_file_path' in locals() else 'not defined'}")
                logger.warning(f"Exception type: {type(e).__name__}")
        else:
            # cclib is not available
            content += f"\n\n## cclib Processing\n⚠️ cclib library is not available"
            logger.warning(f"cclib library is not available for {basename}")
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=content,
            tags=data.tags or [],
            created=created_time,
            category="output",
            visibility="limited",
            attachment_extension=attachment_extension
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=note_filename + MARKDOWN_EXT,
            attachment_extension=attachment_extension,
        )

    def import_paste_new(self, data: NotePasteImport, basename: str, original_extension: str) -> Note:
        """Import a pasted text file with new directory structure."""
        # Generate title from category (capitalized)
        title = data.category.capitalize()
        
        # Use the provided basename
        note_filename = basename
        
        # Ensure filename is unique for markdown file
        while os.path.exists(os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)):
            # Add suffix if duplicate
            base_name = note_filename
            counter = 1
            while os.path.exists(os.path.join(self.storage_path, f"{base_name}_{counter}{MARKDOWN_EXT}")):
                counter += 1
            note_filename = f"{base_name}_{counter}"
        
        filepath = os.path.join(self.storage_path, note_filename + MARKDOWN_EXT)
        created_time = datetime.now()
        
        # Use the original extension
        attachment_extension = original_extension
        
        # Use the category from the data
        category = data.category
        
        # Create markdown content with original filename on first line and text file link on third line
        content = f"{data.original_filename}\n\n[Text](/a/{note_filename})"
        
        # Create markdown with frontmatter
        markdown_content = create_markdown_with_frontmatter(
            title=title,
            content=content,
            tags=data.tags or [],
            created=created_time,
            category=category,
            visibility="private",
            attachment_extension=attachment_extension
        )
        
        self._write_file(filepath, markdown_content)
        
        # Update the search indexes
        self._sync_index_with_retry()
        
        return Note(
            title=title,
            content=content,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time.timestamp(),
            tags=data.tags or [],
            filename=note_filename + MARKDOWN_EXT,
            attachment_extension=attachment_extension,
        )

    def get_by_basename(self, basename: str) -> Note:
        """Get a note by its basename (filename without extension)."""
        # Try to find the note with the given basename
        filename_with_ext = basename + MARKDOWN_EXT
        filepath = os.path.join(self.storage_path, filename_with_ext)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Note with basename '{basename}' not found.")
        
        return self.get(filename_with_ext)

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
        if 'created_time' in metadata:
            # Handle both string and datetime objects
            if isinstance(metadata['created_time'], datetime):
                created_time = metadata['created_time'].timestamp()
            else:
                try:
                    created_time = datetime.strptime(metadata['created_time'], '%Y-%m-%d %H:%M:%S').timestamp()
                except (ValueError, TypeError):
                    # Fallback to file creation time if parsing fails
                    created_time = os.path.getctime(filepath)
        else:
            # Fallback to file creation time if no created_time field
            created_time = os.path.getctime(filepath)
        
        return Note(
            title=metadata.get('title', self._strip_ext(filename)),
            content=body,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time,
            tags=metadata.get('tags', []),
            filename=filename,
            category=metadata.get('category', 'note'),
            visibility=metadata.get('visibility', 'private'),
            attachment_extension=metadata.get('attachment_extension', ''),
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
        
        # Update visibility if provided
        if data.visibility is not None:
            metadata['visibility'] = data.visibility
        
        # Create new markdown with updated frontmatter
        # createdはdatetime型で渡す必要がある
        created_dt = None
        if 'created_time' in metadata and metadata['created_time']:
            if isinstance(metadata['created_time'], datetime):
                created_dt = metadata['created_time']
            else:
                try:
                    created_dt = datetime.strptime(metadata['created_time'], '%Y-%m-%d %H:%M:%S')
                except Exception:
                    created_dt = datetime.fromtimestamp(os.path.getctime(filepath))
        else:
            created_dt = datetime.fromtimestamp(os.path.getctime(filepath))

        markdown_content = create_markdown_with_frontmatter(
            title=metadata.get('title', self._strip_ext(filename)),
            content=body,
            tags=metadata.get('tags', []),
            created=created_dt,
            category=metadata.get('category', 'note'),
            visibility=metadata.get('visibility', 'private')
        )
        
        self._write_file(filepath, markdown_content, overwrite=True)
        
        # Update the search indexes with visibility change handling
        self._sync_index_with_retry(visibility_changed=(old_visibility != metadata.get('visibility', 'private')))
        
        # Git commit (non-blocking)
        try:
            # 同期的なコンテキストで非同期処理を実行
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # イベントループが実行中の場合は、バックグラウンドタスクとして実行
                loop.create_task(self.git_manager.commit_note_change(filename, data))
            else:
                # イベントループが実行されていない場合は、新しいループで実行
                asyncio.run(self.git_manager.commit_note_change(filename, data))
        except RuntimeError:
            # イベントループが取得できない場合は、スレッドプールで実行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.submit(asyncio.run, self.git_manager.commit_note_change(filename, data))
        
        # Parse created date from frontmatter
        created_time = None
        if 'created_time' in metadata:
            try:
                created_time = datetime.strptime(metadata['created_time'], '%Y-%m-%d %H:%M:%S').timestamp()
            except (ValueError, TypeError):
                created_time = os.path.getctime(filepath)
        else:
            created_time = os.path.getctime(filepath)
        
        return Note(
            title=metadata.get('title', self._strip_ext(filename)),
            content=body,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time,
            tags=metadata.get('tags', []),
            filename=filename,
            category=metadata.get('category', 'note'),
            visibility=metadata.get('visibility', 'private'),
            attachment_extension=metadata.get('attachment_extension', ''),
        )

    def delete(self, filename: str) -> None:
        # Add extension if not present
        if not filename.endswith(MARKDOWN_EXT):
            filename += MARKDOWN_EXT
        filepath = os.path.join(self.storage_path, filename)
        os.remove(filepath)
        
        # Update the search index
        self._sync_index_with_retry()

    def _pre_process_search_term(self, term: str) -> str:
        """Pre-process search terms to handle special prefixes."""
        # Handle ext: prefix for attachment_extension searches
        if term.startswith('ext:'):
            extension = term[4:].strip()
            return f'attachment_extension:{extension}'
        return term

    def search(
        self,
        term: str,
        sort: Literal["score", "title", "last_modified", "created_time", "category", "visibility"] = "score",
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
                sort_field = sort if sort in ["title", "last_modified", "created_time", "category", "visibility"] else None
                
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
        
        # Pre-process search term
        term = self._pre_process_search_term(term)
        
        # Regular search processing
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
            sort = sort if sort in ["title", "last_modified", "created_time", "category", "visibility"] else None

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
        sort: Literal["title", "last_modified", "created_time", "category", "visibility"] = "last_modified",
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
            sort_field = sort if sort in ["title", "last_modified", "created_time", "category", "visibility"] else "last_modified"
            
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
                
                # Parse created date from frontmatter
                created_time = None
                if 'created_time' in metadata:
                    try:
                        created_time = datetime.strptime(metadata['created_time'], '%Y-%m-%d %H:%M:%S').timestamp()
                    except (ValueError, TypeError):
                        created_time = os.path.getctime(filepath)
                else:
                    created_time = os.path.getctime(filepath)
                notes.append(Note(
                    title=metadata.get('title', self._strip_ext(filename)),
                    content=body,
                    last_modified=hit["last_modified"].timestamp(),
                    created_time=created_time,
                    tags=metadata.get('tags', []),
                    filename=filename,
                    category=metadata.get('category', 'note'),
                    visibility=metadata.get('visibility', 'private'),
                    attachment_extension=metadata.get('attachment_extension', ''),
                ))
            
            return notes

    def get_notes_by_tag(
        self,
        tag_name: str,
        sort: Literal["title", "last_modified", "created_time", "category", "visibility"] = "last_modified",
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
                sort_field = sort if sort in ["title", "last_modified", "created_time", "category", "visibility"] else "last_modified"
                
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
                        # Parse created date from frontmatter
                        created_time = None
                        if 'created_time' in metadata:
                            try:
                                created_time = datetime.strptime(metadata['created_time'], '%Y-%m-%d %H:%M:%S').timestamp()
                            except (ValueError, TypeError):
                                created_time = os.path.getctime(filepath)
                        else:
                            created_time = os.path.getctime(filepath)
                        notes.append(Note(
                            title=metadata.get('title', self._strip_ext(filename)),
                            content=body,
                            last_modified=hit["last_modified"].timestamp(),
                            created_time=created_time,
                            tags=metadata.get('tags', []),
                            filename=filename,
                            category=metadata.get('category', 'note'),
                            visibility=metadata.get('visibility', 'private'),
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
            sort_field = sort if sort in ["title", "last_modified", "created_time", "category", "visibility"] else "last_modified"
            
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
                
                # Parse created date from frontmatter
                created_time = None
                if 'created_time' in metadata:
                    try:
                        created_time = datetime.strptime(metadata['created_time'], '%Y-%m-%d %H:%M:%S').timestamp()
                    except (ValueError, TypeError):
                        created_time = os.path.getctime(filepath)
                else:
                    created_time = os.path.getctime(filepath)
                notes.append(Note(
                    title=metadata.get('title', self._strip_ext(filename)),
                    content=body,
                    last_modified=hit["last_modified"].timestamp(),
                    created_time=created_time,
                    tags=metadata.get('tags', []),
                    filename=filename,
                    category=metadata.get('category', 'note'),
                    visibility=metadata.get('visibility', 'private'),
                ))
            
            return notes

    def get_notes_without_tags(
        self,
        sort: Literal["title", "last_modified", "created_time", "category", "visibility"] = "last_modified",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        use_public_index: bool = False,
    ) -> list[Note]:
        """Get notes that have no tags."""
        all_notes = self.list_notes(sort=sort, order=order, limit=None, use_public_index=use_public_index)
        notes_without_tags = [note for note in all_notes if not note.tags]
        if limit:
            notes_without_tags = notes_without_tags[:limit]
        return notes_without_tags

    # Git history methods
    async def get_history(self, filename: str) -> List[dict]:
        """Get note history."""
        return await self.git_manager.get_note_history(filename)
    
    async def get_version_content(self, filename: str, commit_hash: str) -> Optional[str]:
        """Get content of specific version."""
        return await self.git_manager.get_note_version(filename, commit_hash)
    
    async def restore_version(self, filename: str, commit_hash: str) -> bool:
        """Restore note to specific version."""
        return await self.git_manager.restore_note_version(filename, commit_hash)

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
        if 'created_time' in metadata:
            try:
                created_time = datetime.strptime(metadata['created_time'], '%Y-%m-%d %H:%M:%S').timestamp()
            except (ValueError, TypeError):
                created_time = os.path.getctime(filepath)
        else:
            created_time = os.path.getctime(filepath)
        
        return Note(
            title=metadata.get('title', self._strip_ext(filename)),
            content=body,
            last_modified=os.path.getmtime(filepath),
            created_time=created_time,
            tags=metadata.get('tags', []),
            filename=filename,
            category=metadata.get('category', 'note'),
            visibility=metadata.get('visibility', 'private'),
            attachment_extension=metadata.get('attachment_extension', ''),
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
            created_time=datetime.fromtimestamp(note.created_time) if note.created_time else datetime.fromtimestamp(note.last_modified),
            title=note.title,
            content=note.content,
            tags=tag_string,
            category=getattr(note, 'category', 'note'),
            visibility=getattr(note, 'visibility', 'private'),
            attachment_extension=getattr(note, 'attachment_extension', ''),
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
                # Update modified
                elif (
                    datetime.fromtimestamp(os.path.getmtime(idx_filepath))
                    != idx_note["last_modified"]
                ):
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
        writer.commit(optimize=optimize)

    def _sync_public_index(self, optimize: bool = False, clean: bool = False) -> None:
        """Synchronize the public index with public notes only."""
        writer = self.public_index.writer()
        if clean:
            writer.mergetype = writing.CLEAR  # Clear the index
        
        # Get all notes and filter for public ones
        public_notes = []
        all_notes = []
        for filename in self._list_all_note_filenames():
            note = self._get_by_filename(filename)
            all_notes.append(note)
            if getattr(note, 'visibility', 'private') == 'public':
                public_notes.append(note)
        
        # Add all public notes to the index
        for note in public_notes:
            self._add_note_to_index(writer, note)
        
        writer.commit(optimize=optimize)

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
            tags=metadata.get('tags', []),
            score=score,
            title_highlights=title_highlights,
            content_highlights=content_highlights,
            tag_matches=tag_matches,
        )

    def _fieldnames_for_term(self, term: str) -> List[str]:
        """Return the field names to search in based on the term."""
        # Check for field-specific searches
        if term.startswith('title:'):
            return ['title']
        elif term.startswith('content:'):
            return ['content']
        elif term.startswith('tags:'):
            return ['tags']
        elif term.startswith('category:'):
            return ['category']
        elif term.startswith('visibility:'):
            return ['visibility']
        elif term.startswith('attachment_extension:'):
            return ['attachment_extension']
        else:
            # Default search fields
            return ['title', 'content', 'tags', 'category', 'attachment_extension']

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
