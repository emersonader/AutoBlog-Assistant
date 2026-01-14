"""
Google Drive Integration - Upload blogs to Drive for NotebookLM import
"""

import os
from typing import Optional

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload
    import google.auth
    import google.auth.transport.requests
    HAS_DRIVE_API = True
except ImportError:
    HAS_DRIVE_API = False


def get_drive_service():
    """Get Google Drive API service using application default credentials."""
    if not HAS_DRIVE_API:
        raise Exception("google-api-python-client not installed. Run: pip install google-api-python-client")

    # Use application default credentials (from gcloud auth application-default login)
    credentials, project = google.auth.default(
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

    # Refresh if needed
    if credentials.expired or not credentials.valid:
        credentials.refresh(google.auth.transport.requests.Request())

    return build('drive', 'v3', credentials=credentials)


def create_folder(service, name: str, parent_id: str = None) -> str:
    """
    Create a folder in Google Drive.

    Returns:
        Folder ID
    """
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        metadata['parents'] = [parent_id]

    folder = service.files().create(body=metadata, fields='id').execute()
    return folder.get('id')


def upload_file(service, name: str, content: str, folder_id: str, mime_type: str = 'text/markdown') -> str:
    """
    Upload a file to Google Drive.

    Returns:
        File ID
    """
    metadata = {
        'name': name,
        'parents': [folder_id]
    }

    media = MediaInMemoryUpload(
        content.encode('utf-8'),
        mimetype=mime_type,
        resumable=True
    )

    file = service.files().create(
        body=metadata,
        media_body=media,
        fields='id'
    ).execute()

    return file.get('id')


def upload_to_drive(
    topic: str,
    blogs: list,
    progress_callback: Optional[callable] = None
) -> dict:
    """
    Upload blog posts to Google Drive.

    Args:
        topic: Topic name (used as folder name)
        blogs: List of blog dicts with 'title' and 'content'
        progress_callback: Optional callback(step, total, message)

    Returns:
        dict with 'folder_id', 'folder_url', 'file_ids'
    """
    service = get_drive_service()

    # Step 1: Create folder
    if progress_callback:
        progress_callback(1, 2, "Creating Drive folder...")

    folder_name = f"AutoBlog - {topic}"
    folder_id = create_folder(service, folder_name)

    # Step 2: Upload blog posts
    if progress_callback:
        progress_callback(2, 2, "Uploading blog posts...")

    file_ids = []
    for i, blog in enumerate(blogs, 1):
        title = blog.get('title', f'Blog Post {i}')
        content = blog.get('content', '')

        # Add frontmatter
        meta_desc = blog.get('meta_description', '')
        full_content = f"""---
title: "{title}"
description: "{meta_desc}"
---

{content}"""

        filename = f"{i}. {title[:50]}.md"
        file_id = upload_file(service, filename, full_content, folder_id)
        file_ids.append(file_id)

    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

    return {
        'folder_id': folder_id,
        'folder_url': folder_url,
        'file_ids': file_ids
    }
