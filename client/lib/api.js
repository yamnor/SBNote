import * as constants from "./constants.js";

import { Note, SearchResult } from "./classes.js";

import axios from "axios";
import { getStoredToken } from "./tokenStorage.js";

import router from "../router.js";

const api = axios.create();

api.interceptors.request.use(
  // If the request is not for the token endpoint, add the token to the headers.
  function (config) {
    if (config.url !== "api/token") {
      const token = getStoredToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  function (error) {
    return Promise.reject(error);
  },
);

export function apiErrorHandler(error) {
  if (error.response?.status === 401) {
    const redirectPath = router.currentRoute.value.fullPath;
    router.push({
      name: "login",
      query: { [constants.params.redirect]: redirectPath },
    });
  } else {
    // Log error for debugging but don't show to user
    // Toast will be handled by the calling component
  }
}

export async function getConfig() {
  try {
    const response = await api.get("api/config");
    return response.data;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function getAuthStatus() {
  try {
    const response = await api.get("api/auth/status");
    return response.data;
  } catch (error) {
    // For auth status check, we want to handle 401 errors gracefully
    // without redirecting to login page
    if (error.response?.status === 401) {
      return { authenticated: false };
    }
    return Promise.reject(error);
  }
}

export async function getToken(username, password, totp) {
  try {
    const response = await api.post("api/token", {
      username: username,
      password: totp ? password + totp : password,
    });
    return response.data.access_token;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function getNotes(term, sort, order, limit, content_limit) {
  try {
    const response = await api.get("api/search", {
      params: {
        term: term,
        sort: sort === 'createdTime' ? 'createdTime' : sort,
        order: order,
        limit: limit,
        content_limit: content_limit,
      },
    });
    return response.data.map((note) => new SearchResult(note));
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function getNotesList(sort, order, limit) {
  try {
    const response = await api.get("api/notes", {
      params: {
        sort: sort === 'createdTime' ? 'createdTime' : sort,
        order: order,
        limit: limit,
      },
    });
    return response.data.map((note) => new Note(note));
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function createNote(title, content, tags = [], category = "note", visibility = "private") {
  try {
    const response = await api.post("api/notes", {
      title: title,
      content: content,
      tags: tags,
      category: category,
      visibility: visibility,
    });
    return new Note(response.data);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function importNote(content, tags = []) {
  try {
    const response = await api.post("api/notes/import", {
      content: content,
      tags: tags,
    });
    return new Note(response.data);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function importImage(file, tags = []) {
  try {
    // Use new import endpoint with directory structure
    const formData = new FormData();
    formData.append("file", file);
    formData.append("image_data", JSON.stringify({
      original_filename: file.name,
      tags: tags,
    }));
    
    const response = await api.post("api/notes/import-image-new", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return new Note(response.data);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function importCoordinate(file, tags = []) {
  try {
    // Use new import endpoint with directory structure
    const formData = new FormData();
    formData.append("file", file);
    formData.append("coordinate_data", JSON.stringify({
      original_filename: file.name,
      tags: tags,
    }));
    
    const response = await api.post("api/notes/import-coordinate-new", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return new Note(response.data);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function importOutput(file, tags = []) {
  try {
    // Use new import endpoint with directory structure
    const formData = new FormData();
    formData.append("file", file);
    formData.append("output_data", JSON.stringify({
      original_filename: file.name,
      tags: tags,
    }));
    
    const response = await api.post("api/notes/import-output-new", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return new Note(response.data);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function importPaste(file, tags = [], category = 'output') {
  try {
    // Use new import endpoint with directory structure
    const formData = new FormData();
    formData.append("file", file);
    formData.append("paste_data", JSON.stringify({
      original_filename: file.name,
      category: category,
      tags: tags,
    }));
    
    const response = await api.post("api/notes/import-paste-new", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return new Note(response.data);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function getNote(filename) {
  try {
    const response = await api.get(`api/notes/${encodeURIComponent(filename)}`);
    return new Note(response.data);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function updateNote(filename, newTitle, newContent, tags = [], visibility = null) {
  try {
    const requestData = {
      newTitle: newTitle,
      newContent: newContent,
      tags: tags,
    };
    
    // Add visibility if provided
    if (visibility !== null) {
      requestData.visibility = visibility;
    }
    
    const response = await api.patch(`api/notes/${encodeURIComponent(filename)}`, requestData);
    return new Note(response.data);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function deleteNote(filename) {
  try {
    await api.delete(`api/notes/${encodeURIComponent(filename)}`);
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function getTags() {
  try {
    const response = await api.get("api/tags");
    return response.data;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function getTagsWithCounts() {
  try {
    const response = await api.get("api/tags/with-counts");
    return response.data;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function getNotesByTag(tagName, sort = "lastModified", order = "desc", limit = 10) {
  try {
    const response = await api.get(`api/tags/${encodeURIComponent(tagName)}/notes`, {
      params: {
        sort: sort === 'createdTime' ? 'createdTime' : sort,
        order: order,
        limit: limit,
      },
    });
    return response.data.map((note) => new Note(note));
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function rebuildIndex() {
  try {
    const response = await api.post("api/rebuild-index");
    return response.data;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function createAttachment(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post("api/files", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function renameTag(oldTagName, newTagName) {
  try {
    const response = await api.patch(`api/tags/${encodeURIComponent(oldTagName)}`, {
      newName: newTagName,
    });
    return response.data;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function deleteTag(tagName) {
  try {
    await api.delete(`api/tags/${encodeURIComponent(tagName)}`);
  } catch (error) {
    return Promise.reject(error);
  }
}

// Git history API functions
export async function getNoteHistory(filename) {
  try {
    const response = await api.get(`api/notes/${encodeURIComponent(filename)}/history`);
    return response.data;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function getNoteVersion(filename, commitHash) {
  try {
    const response = await api.get(`api/notes/${encodeURIComponent(filename)}/version/${commitHash}`);
    return response.data.content;
  } catch (error) {
    return Promise.reject(error);
  }
}

export async function restoreNoteVersion(filename, commitHash) {
  try {
    const response = await api.post(`api/notes/${encodeURIComponent(filename)}/restore`, {
      commit_hash: commitHash
    });
    return response.data;
  } catch (error) {
    return Promise.reject(error);
  }
}
