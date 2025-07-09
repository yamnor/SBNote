import router from "./router.js";

class Note {
  constructor(note) {
    this.title = note?.title;
    this.lastModified = note?.lastModified;
    this.created = note?.created;
    this.content = note?.content;
    this.tags = note?.tags;
    this.filename = note?.filename;
    this.visibility = note?.visibility;
    this.category = note?.category;
  }

  get lastModifiedAsDate() {
    return this.lastModified ? new Date(this.lastModified * 1000) : null;
  }

  get lastModifiedAsString() {
    return this.lastModified ? this.lastModifiedAsDate.toLocaleString() : '';
  }

  get createdAsDate() {
    return this.created ? new Date(this.created * 1000) : null;
  }

  get createdAsString() {
    return this.created ? this.createdAsDate.toLocaleString() : '';
  }
}

class SearchResult extends Note {
  constructor(searchResult) {
    super(searchResult);
    this.score = searchResult.score;
    this.titleHighlights = searchResult.titleHighlights;
    this.contentHighlights = searchResult.contentHighlights;
    this.tagMatches = searchResult.tagMatches;
  }

  get titleHighlightsOrTitle() {
    return this.titleHighlights ? this.titleHighlights : this.title;
  }

  get includesHighlights() {
    if (
      this.titleHighlights ||
      this.contentHighlights ||
      (this.tagMatches != null && this.tagMatches.length)
    ) {
      return true;
    } else {
      return false;
    }
  }
}

export { Note, SearchResult };
