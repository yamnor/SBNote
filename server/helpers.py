import os
import re
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, Union
from collections import OrderedDict

from pydantic import BaseModel

from logger import logger

import frontmatter


def camel_case(snake_case_str: str) -> str:
    """Return the declared snake_case string in camelCase."""
    parts = [part for part in snake_case_str.split("_") if part != ""]
    return parts[0] + "".join(part.title() for part in parts[1:])


def is_valid_filename(filename: str) -> str:
    """Validate that the given filename is valid."""
    if not filename:
        raise ValueError("Filename cannot be empty.")
    if len(filename) > 255:
        raise ValueError("Filename is too long.")
    if re.search(r'[<>:"/\\|?*]', filename):
        raise ValueError("Filename contains invalid characters.")
    return filename


def get_env(key: str, mandatory: bool = False, default: str = None, cast_bool: bool = False, cast_int: bool = False) -> Union[str, bool, int]:
    """Get an environment variable."""
    value = os.getenv(key, default)
    if mandatory and not value:
        raise ValueError(f"Environment variable '{key}' is required but not set.")
    
    if cast_bool and value is not None:
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    if cast_int and value is not None:
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Environment variable '{key}' must be an integer.")
    
    return value


def replace_base_href(html_file, path_prefix):
    """Replace the href value for the base element in an HTML file."""
    base_path = path_prefix + "/"
    logger.info(
        f"Replacing href value for base element in '{html_file}' "
        + f"with '{base_path}'."
    )
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
    pattern = r'(<base\s+href=")[^"]*(")'
    replacement = r"\1" + base_path + r"\2"
    updated_html = re.sub(pattern, replacement, html, flags=re.IGNORECASE)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(updated_html)


def parse_markdown_with_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse markdown content with frontmatter and return metadata and body."""
    try:
        post = frontmatter.loads(content)
        metadata = post.metadata
        body = post.content
        
        # Ensure title is always a string
        if 'title' in metadata and not isinstance(metadata['title'], str):
            metadata['title'] = str(metadata['title'])
        
        # Ensure tags is always a list
        if 'tags' in metadata:
            if metadata['tags'] is None:
                metadata['tags'] = []
            elif not isinstance(metadata['tags'], list):
                # Convert to list if it's not already
                metadata['tags'] = [metadata['tags']] if metadata['tags'] else []
        else:
            metadata['tags'] = []
        
        # Ensure attachment_extension is always a string
        if 'attachment_extension' in metadata:
            if not isinstance(metadata['attachment_extension'], str):
                metadata['attachment_extension'] = str(metadata['attachment_extension'])
        else:
            metadata['attachment_extension'] = ''
        
        return metadata, body
    except Exception:
        # If frontmatter parsing fails, treat entire content as body
        return {}, content


def create_markdown_with_frontmatter(
    title: str, 
    content: str, 
    tags: list = None, 
    created: datetime = None,
    category: str = "note",
    visibility: str = "private",
    attachment_extension: str = None
) -> str:
    """Create markdown content with frontmatter."""
    # Format created time without microseconds
    created_time = created or datetime.now()
    if created_time.microsecond != 0:
        created_time = created_time.replace(microsecond=0)
    
    # Format tags as YAML list
    tags_list = tags or []
    tags_yaml = ""
    if tags_list:
        tags_yaml = "\n".join([f"- {tag}" for tag in tags_list])
    else:
        # Use empty YAML list format that's more compatible
        tags_yaml = ""
    
    # Create frontmatter manually to control order
    # Ensure title is treated as string by wrapping in quotes if it looks like a number
    title_str = f'"{title}"' if str(title).isdigit() else title
    
    # Add attachment_extension to frontmatter if provided
    attachment_extension_yaml = ""
    if attachment_extension:
        attachment_extension_yaml = f"attachment_extension: {attachment_extension}\n"
    
    frontmatter_content = f"""---
title: {title_str}
tags:
{tags_yaml}
created_date: {created_time.strftime('%Y-%m-%d %H:%M:%S')}
category: {category}
visibility: {visibility}
{attachment_extension_yaml}---

{content}"""
    
    return frontmatter_content


class CustomBaseModel(BaseModel):
    class Config:
        alias_generator = camel_case
        populate_by_name = True
        from_attributes = True
