from abc import ABC, abstractmethod
from typing import Literal, List, Optional

from .models import Note, NoteCreate, NoteUpdate, NoteImport, NoteImageImport, NoteXyzImport, NotePlaintextImport, NotePasteImport, SearchResult


class BaseNotes(ABC):
    @abstractmethod
    def create(self, data: NoteCreate) -> Note:
        """Create a new note."""
        pass

    @abstractmethod
    def import_note(self, data: NoteImport) -> Note:
        """Import a markdown file as a new note."""
        pass

    @abstractmethod
    def import_image(self, data: NoteImageImport, filename: str) -> Note:
        """Import an image file and create a note with the image link."""
        pass

    @abstractmethod
    def import_xyz(self, data: NoteXyzImport, filename: str) -> Note:
        """Import an xyz file and create a note with the xyz file link."""
        pass

    @abstractmethod
    def import_plaintext(self, data: NotePlaintextImport, filename: str) -> Note:
        """Import a plaintext file and create a note with the plaintext file link."""
        pass

    @abstractmethod
    def import_paste(self, data: NotePasteImport, filename: str) -> Note:
        """Import a pasted text file and create a note with the text file link."""
        pass

    @abstractmethod
    def get(self, filename: str) -> Note:
        """Get a specific note."""
        pass

    @abstractmethod
    def get_by_basename(self, basename: str) -> Note:
        """Get a note by its basename (filename without extension)."""
        pass

    @abstractmethod
    def update(self, filename: str, new_data: NoteUpdate) -> Note:
        """Update a specific note."""
        pass

    @abstractmethod
    def delete(self, filename: str) -> None:
        """Delete a specific note.""" ""
        pass

    # Git history methods
    async def get_history(self, filename: str) -> List[dict]:
        """Get note history."""
        pass

    async def get_version_content(self, filename: str, commit_hash: str) -> Optional[str]:
        """Get content of specific version."""
        pass

    async def restore_version(self, filename: str, commit_hash: str) -> bool:
        """Restore note to specific version."""
        pass

    @abstractmethod
    def search(
        self,
        term: str,
        sort: Literal["score", "title", "last_modified", "created_time", "category", "visibility"] = "score",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        content_limit: int = None,
    ) -> list[SearchResult]:
        """Search for notes."""
        pass

    @abstractmethod
    def get_tags(self) -> list[str]:
        """Get a list of all indexed tags."""
        pass

    @abstractmethod
    def list_notes(
        self,
        sort: Literal["title", "last_modified", "created_time", "category", "visibility"] = "last_modified",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        use_public_index: bool = False,
    ) -> list[Note]:
        """Get a list of all notes."""
        pass

    @abstractmethod
    def get_notes_by_tag(
        self,
        tag_name: str,
        sort: Literal["title", "last_modified", "created_time", "category", "visibility"] = "last_modified",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        use_public_index: bool = False,
    ) -> list[Note]:
        """Get notes that have a specific tag."""
        pass

    @abstractmethod
    def get_notes_without_tags(
        self,
        sort: Literal["title", "last_modified", "created_time", "category", "visibility"] = "last_modified",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
        use_public_index: bool = False,
    ) -> list[Note]:
        """Get notes that have no tags."""
        pass
