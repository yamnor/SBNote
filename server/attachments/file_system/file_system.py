import os
import shutil
import urllib.parse
import string
import random
from datetime import datetime

from fastapi import UploadFile
from fastapi.responses import FileResponse

from helpers import get_env, is_valid_filename

from ..base import BaseAttachments
from ..models import AttachmentCreateResponse


def generate_random_filename(length: int = 8) -> str:
    """Generate a random filename with specified length."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


class FileSystemAttachments(BaseAttachments):
    def __init__(self):
        self.base_path = get_env("SBNOTE_PATH", mandatory=True)
        if not os.path.exists(self.base_path):
            raise NotADirectoryError(
                f"'{self.base_path}' is not a valid directory."
            )
        self.storage_path = os.path.join(self.base_path, "files")
        os.makedirs(self.storage_path, exist_ok=True)

    def create(self, file: UploadFile) -> AttachmentCreateResponse:
        """Create a new attachment."""
        # Store original filename for alt attribute BEFORE generating random name
        original_filename = file.filename
        
        # Generate random filename with original extension
        random_filename = self._generate_random_filename_with_extension(original_filename)
        
        # Ensure filename is unique
        while os.path.exists(os.path.join(self.storage_path, random_filename)):
            random_filename = self._generate_random_filename_with_extension(original_filename)
        
        # Update file object with new filename
        file.filename = random_filename
        
        self._save_file(file)
        
        return AttachmentCreateResponse(
            filename=random_filename, 
            url=self._url_for_filename(random_filename),
            original_filename=original_filename
        )

    def get(self, filename: str) -> FileResponse:
        """Get a specific attachment."""
        is_valid_filename(filename)
        filepath = os.path.join(self.storage_path, filename)
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"'{filename}' not found.")
        return FileResponse(filepath)

    def get_by_basename_and_category(self, basename: str, category: str, original_extension: str = None) -> FileResponse:
        """Get an attachment by basename and category."""
        # Determine the extension based on category and original_extension
        if category == "output":
            # For output category, use original_extension if provided, otherwise default to txt
            extension = original_extension or "txt"
        else:
            # For coordinate and image, use the original extension
            extension = original_extension or "xyz"  # fallback for coordinate
        
        # Construct the filename
        filename = f"{category}.{extension}"
        
        # Create the directory path
        dir_path = os.path.join(self.storage_path, basename)
        filepath = os.path.join(dir_path, filename)
        
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"'{filename}' not found in '{basename}' directory.")
        
        return FileResponse(filepath)

    def _save_file(self, file: UploadFile):
        filepath = os.path.join(self.storage_path, file.filename)
        with open(filepath, "xb") as f:
            shutil.copyfileobj(file.file, f)

    def _save_file_with_category(self, file: UploadFile, basename: str, category: str, original_extension: str = None):
        """Save a file with category-based naming."""
        # Determine the extension based on category
        if category == "output":
            extension = "txt"
        else:
            # For coordinate and image, use the original extension
            extension = original_extension or "xyz"  # fallback for coordinate
        
        # Create the directory
        dir_path = os.path.join(self.storage_path, basename)
        os.makedirs(dir_path, exist_ok=True)
        
        # Construct the filename
        filename = f"{category}.{extension}"
        filepath = os.path.join(dir_path, filename)
        
        # Save the file
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        return filename

    def _generate_random_filename_with_extension(self, original_filename: str) -> str:
        """Generate a random filename with the original file extension."""
        name, ext = os.path.splitext(original_filename)
        random_name = generate_random_filename()
        return f"{random_name}{ext}"

    def _datetime_suffix_filename(self, filename: str) -> str:
        """Add a timestamp suffix to the filename."""
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%SZ")
        name, ext = os.path.splitext(filename)
        return f"{name}_{timestamp}{ext}"

    def _url_for_filename(self, filename: str) -> str:
        """Return the URL for the given filename."""
        return f"files/{urllib.parse.quote(filename)}"
