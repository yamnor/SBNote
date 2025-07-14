import sys
from enum import Enum

from helpers import CustomBaseModel, get_env
from logger import logger


class GlobalConfig:
    def __init__(self) -> None:
        logger.debug("Loading global config...")
        self.auth_type: AuthType = self._load_auth_type()
        self.quick_access_hide: bool = self._quick_access_hide()
        self.quick_access_sort: str = self._quick_access_sort()
        self.quick_access_limit: int = self._quick_access_limit()
        self.path_prefix: str = self._load_path_prefix()
        self.max_file_size: int = self._load_max_file_size()

    def load_auth(self):
        if self.auth_type in (AuthType.NONE, AuthType.READ_ONLY):
            return None
        elif self.auth_type in (AuthType.PASSWORD, AuthType.TOTP):
            from auth.local import LocalAuth

            return LocalAuth()

    def load_note_storage(self):
        from notes.file_system import FileSystemNotes

        return FileSystemNotes()

    def load_attachment_storage(self):
        from attachments.file_system import FileSystemAttachments

        return FileSystemAttachments()

    def _load_auth_type(self):
        key = "SBNOTE_AUTH_TYPE"
        auth_type = get_env(
            key, mandatory=False, default=AuthType.PASSWORD.value
        )
        try:
            auth_type = AuthType(auth_type.lower())
        except ValueError:
            logger.error(
                f"Invalid value '{auth_type}' for {key}. "
                + "Must be one of: "
                + ", ".join([auth_type.value for auth_type in AuthType])
                + "."
            )
            sys.exit(1)
        return auth_type

    def _quick_access_hide(self):
        key = "SBNOTE_QUICK_ACCESS_HIDE"
        value = get_env(key, mandatory=False, default=False, cast_bool=True)
        if value is False:
            deprecated_key = "SBNOTE_HIDE_RECENTLY_MODIFIED"
            value = get_env(
                deprecated_key, mandatory=False, default=False, cast_bool=True
            )
            if value is True:
                logger.warning(
                    f"{deprecated_key} is deprecated. Please use {key} instead."
                )
        return value

    def _quick_access_sort(self):
        key = "SBNOTE_QUICK_ACCESS_SORT"
        value = get_env(key, mandatory=False, default="lastModified")
        valid_values = ["score", "title", "lastModified"]
        if value not in valid_values:
            logger.error(
                f"Invalid value '{value}' for {key}. "
                + "Must be one of: "
                + ", ".join(valid_values)
            )
            sys.exit(1)
        return value

    def _quick_access_limit(self):
        key = "SBNOTE_QUICK_ACCESS_LIMIT"
        return get_env(key, mandatory=False, default=12, cast_int=True)

    def _load_path_prefix(self):
        key = "SBNOTE_PATH_PREFIX"
        value = get_env(key, mandatory=False, default="")
        if value and (not value.startswith("/") or value.endswith("/")):
            logger.error(
                f"Invalid value '{value}' for {key}. "
                + "Must start with '/' and not end with '/'."
            )
            sys.exit(1)
        return value

    def _load_max_file_size(self):
        key = "SBNOTE_MAX_FILE_SIZE_MB"
        value = get_env(key, mandatory=False, default=100, cast_int=True)
        # Convert MB to bytes
        return value * 1024 * 1024


class AuthType(str, Enum):
    NONE = "none"
    READ_ONLY = "read_only"
    PASSWORD = "password"
    TOTP = "totp"


class GlobalConfigResponseModel(CustomBaseModel):
    auth_type: AuthType
    quick_access_hide: bool
    quick_access_sort: str
    quick_access_limit: int
