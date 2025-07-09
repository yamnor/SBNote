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


class Note(CustomBaseModel):
    title: str
    content: Optional[str] = Field(None)
    last_modified: float
    created: Optional[float] = Field(None)
    tags: Optional[List[str]] = Field(default_factory=list)
    filename: Optional[str] = Field(None)
    category: Optional[str] = Field("note")


class NoteUpdate(CustomBaseModel):
    new_title: Optional[str] = Field(None)
    new_content: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(default_factory=list)


class SearchResult(CustomBaseModel):
    title: str
    content: Optional[str] = Field(None)
    last_modified: float
    filename: Optional[str] = Field(None)

    score: Optional[float] = Field(None)
    title_highlights: Optional[str] = Field(None)
    content_highlights: Optional[str] = Field(None)
    tag_matches: Optional[List[str]] = Field(None)
