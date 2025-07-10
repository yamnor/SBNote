import router from "./router.js";

class Note {
  constructor(note) {
    this.title = note?.title;
    this.lastModified = note?.lastModified;
    this.created_time = note?.createdTime;
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
    if (!this.lastModified) return '';
    const date = this.lastModifiedAsDate;
    return date.toLocaleDateString('en-US', {
      year: '2-digit',
      month: '2-digit',
      day: '2-digit'
    }) + ' ' + date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  }

  get createdTimeAsDate() {
    return this.created_time ? new Date(this.created_time * 1000) : null;
  }

  get createdTimeAsString() {
    if (!this.created_time) return '';
    const date = this.createdTimeAsDate;
    return date.toLocaleDateString('en-US', {
      year: '2-digit',
      month: '2-digit',
      day: '2-digit'
    }) + ' ' + date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
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
