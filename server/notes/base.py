from abc import ABC, abstractmethod
from typing import Literal

from .models import Note, NoteCreate, NoteUpdate, NoteImport, SearchResult


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
    def get(self, filename: str) -> Note:
        """Get a specific note."""
        pass

    @abstractmethod
    def update(self, filename: str, new_data: NoteUpdate) -> Note:
        """Update a specific note."""
        pass

    @abstractmethod
    def delete(self, filename: str) -> None:
        """Delete a specific note.""" ""
        pass

    @abstractmethod
    def search(
        self,
        term: str,
        sort: Literal["score", "title", "last_modified", "created_date", "category", "visibility"] = "score",
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
        sort: Literal["title", "last_modified", "created_date", "category", "visibility"] = "last_modified",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
    ) -> list[Note]:
        """Get a list of all notes."""
        pass

    @abstractmethod
    def get_notes_by_tag(
        self,
        tag_name: str,
        sort: Literal["title", "last_modified", "created_date", "category", "visibility"] = "last_modified",
        order: Literal["asc", "desc"] = "desc",
        limit: int = None,
    ) -> list[Note]:
        """Get notes that have a specific tag."""
        pass
