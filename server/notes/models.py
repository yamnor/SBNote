from typing import List, Optional

from pydantic import Field
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

from helpers import CustomBaseModel


class NoteBase(CustomBaseModel):
    title: str


class NoteCreate(CustomBaseModel):
    title: str
    content: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(default_factory=list)
    category: Optional[str] = Field("note")
    visibility: Optional[str] = Field("private")


class Note(CustomBaseModel):
    title: str
    content: Optional[str] = Field(None)
    last_modified: float
    created_time: Optional[float] = Field(None)
    tags: Optional[List[str]] = Field(default_factory=list)
    filename: Optional[str] = Field(None)
    category: Optional[str] = Field("note")
    visibility: Optional[str] = Field("private")
    attachment_extension: Optional[str] = Field("")


class NoteUpdate(CustomBaseModel):
    new_title: Optional[str] = Field(None)
    new_content: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(default_factory=list)
    visibility: Optional[str] = Field(None)


class NoteImport(CustomBaseModel):
    content: str
    tags: Optional[List[str]] = Field(default_factory=list)


class NoteImageImport(CustomBaseModel):
    original_filename: str
    tags: Optional[List[str]] = Field(default_factory=list)


class NoteXyzImport(CustomBaseModel):
    original_filename: str
    tags: Optional[List[str]] = Field(default_factory=list)


class NotePlaintextImport(CustomBaseModel):
    original_filename: str
    tags: Optional[List[str]] = Field(default_factory=list)


class SearchResult(CustomBaseModel):
    title: str
    content: Optional[str] = Field(None)
    last_modified: float
    filename: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(default_factory=list)

    score: Optional[float] = Field(None)
    title_highlights: Optional[str] = Field(None)
    content_highlights: Optional[str] = Field(None)
    tag_matches: Optional[List[str]] = Field(None)
