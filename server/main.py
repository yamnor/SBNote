from typing import List, Literal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, UploadFile, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import api_messages
from attachments.base import BaseAttachments
from attachments.models import AttachmentCreateResponse
from auth.base import BaseAuth
from auth.models import Login, Token
from global_config import AuthType, GlobalConfig, GlobalConfigResponseModel
from helpers import replace_base_href
from logger import logger
from notes.base import BaseNotes
from notes.models import Note, NoteCreate, NoteUpdate, SearchResult, NoteImport, NoteImageImport, NoteXyzImport, NotePlaintextImport, NotePasteImport


def is_authenticated(request: Request) -> bool:
    """Check if the user is authenticated based on the request."""
    if not auth:
        logger.info("No auth configured, considering as authenticated")
        return True  # No auth configured, consider as authenticated
    
    try:
        # Check if Authorization header exists
        auth_header = request.headers.get("Authorization")
        logger.info(f"Auth header: {auth_header}")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # Try to validate the token directly
            try:
                auth._validate_token(token)
                return True
            except Exception as e:
                logger.info(f"Token validation failed: {e}")
                return False
        else:
            logger.info("No valid Authorization header found")
            return False
    except Exception as e:
        logger.info(f"Authentication check failed: {e}")
        return False

global_config = GlobalConfig()
auth: BaseAuth = global_config.load_auth()
note_storage: BaseNotes = global_config.load_note_storage()
attachment_storage: BaseAttachments = global_config.load_attachment_storage()
auth_deps = [Depends(auth.authenticate)] if auth else []
router = APIRouter()
app = FastAPI(
    docs_url=global_config.path_prefix + "/docs",
    openapi_url=global_config.path_prefix + "/openapi.json",
)
replace_base_href("client/dist/index.html", global_config.path_prefix)





# region Login
if global_config.auth_type not in [AuthType.NONE, AuthType.READ_ONLY]:

    @router.post("/api/token", response_model=Token)
    def token(data: Login):
        try:
            return auth.login(data)
        except ValueError:
            raise HTTPException(
                status_code=401, detail=api_messages.login_failed
            )

    @router.get("/api/auth/status")
    def get_auth_status(request: Request):
        """Get current authentication status."""
        try:
            if auth:
                # Check if Authorization header exists
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    # Try to validate the token directly
                    try:
                        auth._validate_token(token)
                        return {"authenticated": True}
                    except Exception:
                        return {"authenticated": False}
                else:
                    return {"authenticated": False}
        except Exception:
            pass
        return {"authenticated": False}


# endregion


# region Notes
# Get Note
@router.get(
    "/api/notes/{filename}",
    response_model=Note,
)
def get_note(filename: str, request: Request):
    """Get a specific note."""
    try:
        note = note_storage.get(filename)
        
        # Check visibility access control
        if note.visibility == 'private' and not is_authenticated(request):
            # Return 404 for private notes when not authenticated
            raise HTTPException(404, api_messages.note_not_found)
        
        return note
    except ValueError:
        raise HTTPException(
            status_code=400, detail=api_messages.invalid_note_title
        )
    except FileNotFoundError:
        raise HTTPException(404, api_messages.note_not_found)


# Get Notes List
@router.get(
    "/api/notes",
    response_model=List[Note],
)
def get_notes_list(
    request: Request,
    sort: Literal["title", "lastModified", "createdTime", "category", "visibility"] = "lastModified",
    order: Literal["asc", "desc"] = "desc",
    limit: int = None,
):
    """Get a list of all notes."""
    if sort == "lastModified":
        sort = "last_modified"
    elif sort == "createdTime":
        sort = "created_time"
    # Use public index if not authenticated, main index if authenticated
    use_public_index = not is_authenticated(request)
    return note_storage.list_notes(sort=sort, order=order, limit=limit, use_public_index=use_public_index)


if global_config.auth_type != AuthType.READ_ONLY:

    # Create Note
    @router.post(
        "/api/notes",
        dependencies=auth_deps,
        response_model=Note,
    )
    def post_note(note: NoteCreate):
        """Create a new note."""
        try:
            return note_storage.create(note)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError:
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )

    # Import Note
    @router.post(
        "/api/notes/import",
        dependencies=auth_deps,
        response_model=Note,
    )
    def import_note(note: NoteImport):
        """Import a markdown file as a new note."""
        try:
            return note_storage.import_note(note)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError:
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )

    # Import Image
    @router.post(
        "/api/notes/import-image",
        dependencies=auth_deps,
        response_model=Note,
    )
    def import_image(image_data: NoteImageImport, attachment_filename: str = Query(...)):
        """Import an image file and create a note with the image link."""
        try:
            # Create a new data object with filename included
            import_data = NoteImageImport(
                original_filename=image_data.original_filename,
                tags=image_data.tags or []
            )
            
            # Pass filename as a separate parameter to the storage layer
            return note_storage.import_image(import_data, attachment_filename)
        except ValueError as e:
            logger.error(f"ValueError in import_image: {e}")
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError as e:
            logger.error(f"FileExistsError in import_image: {e}")
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )
        except Exception as e:
            logger.error(f"Unexpected error in import_image: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Import failed: {str(e)}",
            )

    # Import XYZ
    @router.post(
        "/api/notes/import-xyz",
        dependencies=auth_deps,
        response_model=Note,
    )
    def import_xyz(xyz_data: NoteXyzImport, attachment_filename: str = Query(...)):
        """Import a XYZ file as a new note."""
        try:
            # Create a new data object with filename included
            import_data = NoteXyzImport(
                original_filename=xyz_data.original_filename,
                tags=xyz_data.tags or []
            )
            
            # Pass filename as a separate parameter to the storage layer
            return note_storage.import_xyz(import_data, attachment_filename)
        except ValueError as e:
            logger.error(f"ValueError in import_xyz: {e}")
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError as e:
            logger.error(f"FileExistsError in import_xyz: {e}")
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )
        except Exception as e:
            logger.error(f"Unexpected error in import_xyz: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Import failed: {str(e)}",
            )

    # Import Plaintext
    @router.post(
        "/api/notes/import-plaintext",
        dependencies=auth_deps,
        response_model=Note,
    )
    def import_plaintext(plaintext_data: NotePlaintextImport, attachment_filename: str = Query(...)):
        """Import a plaintext file as a new note."""
        try:
            # Create a new data object with filename included
            import_data = NotePlaintextImport(
                original_filename=plaintext_data.original_filename,
                tags=plaintext_data.tags or []
            )
            
            # Pass filename as a separate parameter to the storage layer
            return note_storage.import_plaintext(import_data, attachment_filename)
        except ValueError as e:
            logger.error(f"ValueError in import_plaintext: {e}")
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError as e:
            logger.error(f"FileExistsError in import_plaintext: {e}")
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )
        except Exception as e:
            logger.error(f"Unexpected error in import_plaintext: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Import failed: {str(e)}",
            )

    # Import Paste
    @router.post(
        "/api/notes/import-paste",
        dependencies=auth_deps,
        response_model=Note,
    )
    def import_paste(paste_data: NotePasteImport, attachment_filename: str = Query(...)):
        """Import a pasted text file as a new note."""
        try:
            # Create a new data object with filename included
            import_data = NotePasteImport(
                original_filename=paste_data.original_filename,
                category=paste_data.category,
                tags=paste_data.tags or []
            )
            
            # Pass filename as a separate parameter to the storage layer
            return note_storage.import_paste(import_data, attachment_filename)
        except ValueError as e:
            logger.error(f"ValueError in import_paste: {e}")
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError as e:
            logger.error(f"FileExistsError in import_paste: {e}")
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )
        except Exception as e:
            logger.error(f"Unexpected error in import_paste: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Import failed: {str(e)}",
            )

    # Update Note
    @router.patch(
        "/api/notes/{filename}",
        dependencies=auth_deps,
        response_model=Note,
    )
    def patch_note(filename: str, data: NoteUpdate):
        try:
            return note_storage.update(filename, data)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileExistsError:
            raise HTTPException(
                status_code=409, detail=api_messages.note_exists
            )
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)

    # Delete Note
    @router.delete(
        "/api/notes/{filename}",
        dependencies=auth_deps,
        response_model=None,
    )
    def delete_note(filename: str):
        try:
            note_storage.delete(filename)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_note_title,
            )
        except FileNotFoundError:
            raise HTTPException(404, api_messages.note_not_found)


# endregion


# region Search
@router.get(
    "/api/search",
    response_model=List[SearchResult],
)
def search(
    request: Request,
    term: str,
    sort: Literal["score", "title", "lastModified", "createdTime", "category", "visibility"] = "score",
    order: Literal["asc", "desc"] = "desc",
    limit: int = None,
    content_limit: int = None,
):
    """Perform a full text search on all notes."""
    if sort == "lastModified":
        sort = "last_modified"
    elif sort == "createdTime":
        sort = "created_time"
    use_public_index = not is_authenticated(request)
    return note_storage.search(term, sort=sort, order=order, limit=limit, content_limit=content_limit, use_public_index=use_public_index)


@router.get(
    "/api/tags",
    response_model=List[str],
)
def get_tags(request: Request):
    """Get a list of all indexed tags."""
    try:
        # Use public index if not authenticated, main index if authenticated
        use_public_index = not is_authenticated(request)
        
        # Get all tags from storage
        all_tags = note_storage.get_tags(use_public_index=use_public_index)
        
        # Check if there are any notes without tags
        all_notes = note_storage.list_notes(limit=None, use_public_index=use_public_index)
        has_notes_without_tags = any(not note.tags for note in all_notes)
        
        # Add "_untagged" tag if there are notes without tags
        if has_notes_without_tags and "_untagged" not in all_tags:
            all_tags.append("_untagged")
        
        return all_tags
    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tags")


@router.get("/api/tags/with-counts")
def get_tags_with_counts(request: Request):
    """Get a list of all tags with their note counts and recent note info."""
    try:
        # Use public index if not authenticated, main index if authenticated
        use_public_index = not is_authenticated(request)
        
        # Get all notes to calculate tag counts
        all_notes = note_storage.list_notes(limit=None, use_public_index=use_public_index)
        tag_counts = {}
        tag_notes = {}
        tag_recent_modified = {}  # Track most recent modified time for each tag
        untagged_count = 0
        untagged_notes = []
        untagged_recent_modified = None
        
        # Count notes for each tag and collect note titles (max 5 per tag)
        for note in all_notes:
            if note.tags:
                for tag in note.tags:
                    if tag not in tag_counts:
                        tag_counts[tag] = 0
                        tag_notes[tag] = []
                        tag_recent_modified[tag] = None
                    tag_counts[tag] += 1
                    # Only collect up to 5 note titles per tag
                    if len(tag_notes[tag]) < 5:
                        tag_notes[tag].append(note.title)
                    # Track most recent modified time
                    if tag_recent_modified[tag] is None or note.last_modified > tag_recent_modified[tag]:
                        tag_recent_modified[tag] = note.last_modified
            else:
                # Count notes without tags as "_untagged"
                untagged_count += 1
                if len(untagged_notes) < 5:
                    untagged_notes.append(note.title)
                # Track most recent modified time for untagged
                if untagged_recent_modified is None or note.last_modified > untagged_recent_modified:
                    untagged_recent_modified = note.last_modified
        
        # Get all tags and add counts, but only include tags with count > 0
        all_tags = note_storage.get_tags(use_public_index=use_public_index)
        result = []
        
        for tag in all_tags:
            count = tag_counts.get(tag, 0)
            if count > 0:  # Only include tags that have at least one note
                result.append({
                    "tag": tag,
                    "count": count,
                    "notes": tag_notes.get(tag, []),
                    "recentModified": tag_recent_modified.get(tag)
                })
        
        # Add _untagged tag if there are notes without tags
        if untagged_count > 0:
            result.append({
                "tag": "_untagged",
                "count": untagged_count,
                "notes": untagged_notes,
                "recentModified": untagged_recent_modified
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting tags with counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tags with counts")


@router.get(
    "/api/tags/{tag_name}/notes",
    response_model=List[Note],
)
def get_notes_by_tag(
    request: Request,
    tag_name: str,
    sort: Literal["title", "lastModified", "createdTime", "category", "visibility"] = "lastModified",
    order: Literal["asc", "desc"] = "desc",
    limit: int = 10,
):
    if sort == "lastModified":
        sort = "last_modified"
    elif sort == "createdTime":
        sort = "created_time"
    use_public_index = not is_authenticated(request)
    return note_storage.get_notes_by_tag(tag_name, sort=sort, order=order, limit=limit, use_public_index=use_public_index)


if global_config.auth_type != AuthType.READ_ONLY:

    @router.patch(
        "/api/tags/{tag_name}",
        dependencies=auth_deps,
        response_model=dict,
    )
    def rename_tag(tag_name: str, data: dict):
        """Rename a tag across all notes."""
        try:
            new_name = data.get("newName")
            if not new_name:
                raise HTTPException(status_code=400, detail="newName is required")
            
            if tag_name == "_untagged":
                raise HTTPException(status_code=400, detail="Cannot rename _untagged tag")
            
            # Get all notes that have this tag
            notes_with_tag = note_storage.get_notes_by_tag(tag_name, limit=None)
            
            # Update each note to replace the old tag with the new one
            for note in notes_with_tag:
                if note.tags and tag_name in note.tags:
                    new_tags = [new_name if tag == tag_name else tag for tag in note.tags]
                    note_storage.update(note.filename, NoteUpdate(tags=new_tags))
            
            return {"message": f"Tag '{tag_name}' renamed to '{new_name}' successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error renaming tag {tag_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to rename tag {tag_name}")

    @router.delete(
        "/api/tags/{tag_name}",
        dependencies=auth_deps,
        response_model=dict,
    )
    def delete_tag(tag_name: str):
        """Delete a tag from all notes."""
        try:
            if tag_name == "_untagged":
                raise HTTPException(status_code=400, detail="Cannot delete _untagged tag")
            
            # Get all notes that have this tag
            notes_with_tag = note_storage.get_notes_by_tag(tag_name, limit=None)
            
            # Update each note to remove the tag
            for note in notes_with_tag:
                if note.tags and tag_name in note.tags:
                    new_tags = [tag for tag in note.tags if tag != tag_name]
                    note_storage.update(note.filename, NoteUpdate(tags=new_tags))
            
            return {"message": f"Tag '{tag_name}' deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting tag {tag_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete tag {tag_name}")


@router.post("/api/rebuild-index", dependencies=auth_deps)
def rebuild_index():
    """Rebuild both search indexes (main and public) completely."""
    try:
        note_storage._sync_index_with_retry(clean=True, optimize=True)
        return {"message": "Both indexes (main and public) rebuilt successfully"}
    except Exception as e:
        logger.error(f"Failed to rebuild indexes: {e}")
        raise HTTPException(500, "Failed to rebuild indexes")

# Git history endpoints
@router.get("/api/notes/{filename}/history")
async def get_note_history(filename: str, request: Request):
    """Get note history."""
    if not is_authenticated(request):
        raise HTTPException(401, "Authentication required")
    
    try:
        history = await note_storage.get_history(filename)
        return history
    except Exception as e:
        logger.error(f"Failed to get note history: {e}")
        raise HTTPException(500, "Failed to get history")

@router.get("/api/notes/{filename}/version/{commit_hash}")
async def get_note_version(filename: str, commit_hash: str, request: Request):
    """Get content of specific version."""
    if not is_authenticated(request):
        raise HTTPException(401, "Authentication required")
    
    try:
        content = await note_storage.get_version_content(filename, commit_hash)
        if content:
            return {"content": content}
        else:
            raise HTTPException(404, "Version not found")
    except Exception as e:
        logger.error(f"Failed to get note version: {e}")
        raise HTTPException(500, "Failed to get version")

@router.post("/api/notes/{filename}/restore")
async def restore_note_version(filename: str, request: Request, data: dict):
    """Restore note to specific version."""
    if not is_authenticated(request):
        raise HTTPException(401, "Authentication required")
    
    commit_hash = data.get("commit_hash")
    if not commit_hash:
        raise HTTPException(422, "commit_hash is required")
    
    try:
        success = await note_storage.restore_version(filename, commit_hash)
        if success:
            return {"message": "Restored successfully"}
        else:
            raise HTTPException(400, "Restore failed")
    except Exception as e:
        logger.error(f"Failed to restore note version: {e}")
        raise HTTPException(500, "Restore failed")


# endregion


# region Config
@router.get("/api/config", response_model=GlobalConfigResponseModel)
def get_config():
    """Retrieve server-side config required for the UI."""
    return GlobalConfigResponseModel(
        auth_type=global_config.auth_type,
        quick_access_hide=global_config.quick_access_hide,
        quick_access_sort=global_config.quick_access_sort,
        quick_access_limit=global_config.quick_access_limit,
    )


# region Migration
@router.post("/api/migrate-frontmatter", dependencies=auth_deps)
def migrate_to_frontmatter():
    """Migrate existing notes to frontmatter format."""
    try:
        note_storage.migrate_to_frontmatter()
        return {"message": "Migration completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# endregion


# endregion


# region Attachments
# Get Attachment
@router.get(
    "/api/files/{filename}",
)
# Include a secondary route used to create relative URLs that can be used
# outside the context of SBNote (e.g. "/files/image.jpg").
@router.get(
    "/files/{filename}",
    include_in_schema=False,
)
def get_attachment(filename: str):
    """Download an attachment."""
    try:
        return attachment_storage.get(filename)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=api_messages.invalid_attachment_filename,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=api_messages.attachment_not_found
        )

# Attachment redirect endpoint
@router.get(
    "/a/{basename}",
    include_in_schema=False,
)
def get_attachment_by_basename(basename: str):
    """Get an attachment by note basename. Redirects to the actual file if the note has an attachment."""
    try:
        # Get the note by basename
        note = note_storage.get_by_basename(basename)
        
        # Check if attachment_extension exists
        if not note.attachment_extension:
            raise HTTPException(
                status_code=404, detail="No attachment extension found"
            )
        
        # Construct the full filename with extension
        filename = f"{basename}.{note.attachment_extension}"
        
        # Redirect to the actual file
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/files/{filename}")
        
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail="Note not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_attachment_by_basename: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error"
        )


if global_config.auth_type != AuthType.READ_ONLY:

    # Create Attachment
    @router.post(
        "/api/files",
        dependencies=auth_deps,
        response_model=AttachmentCreateResponse,
    )
    def post_attachment(file: UploadFile):
        """Upload an attachment."""
        try:
            return attachment_storage.create(file)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=api_messages.invalid_attachment_filename,
            )
        except FileExistsError:
            raise HTTPException(409, api_messages.attachment_exists)


# endregion


# region Healthcheck
@router.get("/health")
def healthcheck() -> str:
    """A lightweight endpoint that simply returns 'OK' to indicate the server
    is running."""
    return "OK"




# endregion


# region UI
@router.get("/{path:path}", include_in_schema=False)
def root(path: str = ""):
    import os
    from fastapi.responses import FileResponse
    
    # Handle static files
    if path and not path.startswith("api/"):
        file_path = os.path.join("client/dist", path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
    
    # Serve index.html for all other routes (SPA routing)
    with open("client/dist/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)


# endregion

app.include_router(router, prefix=global_config.path_prefix)

# Handle static files in the root handler instead of mounting
