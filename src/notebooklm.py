"""
NotebookLM Enterprise Integration - Upload blogs to NotebookLM via Vertex AI API
"""

import os
import subprocess
import requests
from typing import Optional

# Try to import google.auth for service account support
try:
    import google.auth
    import google.auth.transport.requests
    from google.oauth2 import service_account
    HAS_GOOGLE_AUTH = True
except ImportError:
    HAS_GOOGLE_AUTH = False


def get_access_token() -> str:
    """
    Get Google Cloud access token.

    Tries in order:
    1. Service account JSON file (GOOGLE_APPLICATION_CREDENTIALS env var)
    2. gcloud CLI

    Returns:
        Access token string
    """
    # Method 1: Try service account credentials
    sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_path and os.path.exists(sa_path) and HAS_GOOGLE_AUTH:
        try:
            credentials = service_account.Credentials.from_service_account_file(
                sa_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials.refresh(google.auth.transport.requests.Request())
            return credentials.token
        except Exception as e:
            pass  # Fall through to gcloud

    # Method 2: Try gcloud CLI (check common locations)
    gcloud_paths = [
        "gcloud",  # System PATH
        os.path.expanduser("~/Downloads/google-cloud-sdk/bin/gcloud"),
        os.path.expanduser("~/google-cloud-sdk/bin/gcloud"),
        "/usr/local/google-cloud-sdk/bin/gcloud",
        "/Volumes/ExternalHome/Grumpy/Downloads/google-cloud-sdk/bin/gcloud",
    ]

    for gcloud_path in gcloud_paths:
        try:
            result = subprocess.run(
                [gcloud_path, "auth", "print-access-token"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    raise Exception(
        "Authentication required. Either:\n"
        "1. Run: gcloud auth login\n"
        "2. Set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON file"
    )


def create_notebook(
    project_number: str,
    title: str,
    location: str = "us",
    region: str = "us"
) -> dict:
    """
    Create a new NotebookLM notebook.

    Args:
        project_number: Google Cloud project number (not ID)
        title: Title for the notebook
        location: Data store location (us, eu, or global)
        region: Endpoint region prefix (us, eu, or global)

    Returns:
        dict with notebook info including 'notebookId'
    """
    token = get_access_token()

    url = f"https://{region}-discoveryengine.googleapis.com/v1alpha/projects/{project_number}/locations/{location}/notebooks"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "title": title
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Failed to create notebook: {response.status_code} - {response.text}")

    return response.json()


def add_text_sources(
    project_number: str,
    notebook_id: str,
    sources: list,
    location: str = "us",
    region: str = "us"
) -> dict:
    """
    Add text content sources to a notebook.

    Args:
        project_number: Google Cloud project number
        notebook_id: ID of the notebook to add sources to
        sources: List of dicts with 'name' and 'content' keys
        location: Data store location
        region: Endpoint region prefix

    Returns:
        API response dict
    """
    token = get_access_token()

    url = f"https://{region}-discoveryengine.googleapis.com/v1alpha/projects/{project_number}/locations/{location}/notebooks/{notebook_id}/sources:batchCreate"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Format sources for the API
    user_contents = []
    for source in sources:
        user_contents.append({
            "textContent": {
                "sourceName": source["name"],
                "content": source["content"]
            }
        })

    data = {
        "userContents": user_contents
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Failed to add sources: {response.status_code} - {response.text}")

    return response.json()


def upload_to_notebooklm(
    topic: str,
    blogs: list,
    project_number: str,
    location: str = "us",
    region: str = "us",
    progress_callback: Optional[callable] = None
) -> dict:
    """
    Create a NotebookLM notebook and upload blog posts as sources.

    Args:
        topic: The topic name (used as notebook title)
        blogs: List of blog dicts with 'title' and 'content' keys
        project_number: Google Cloud project number
        location: Data store location (us, eu, or global)
        region: Endpoint region prefix (us, eu, or global)
        progress_callback: Optional callback function(step, total_steps, message)

    Returns:
        dict with 'notebook_id' and 'notebook_url'
    """
    total_steps = 2

    # Step 1: Create notebook
    if progress_callback:
        progress_callback(1, total_steps, "Creating NotebookLM notebook...")

    notebook_title = f"AutoBlog: {topic}"
    notebook = create_notebook(project_number, notebook_title, location, region)
    notebook_id = notebook.get("notebookId") or notebook.get("name", "").split("/")[-1]

    # Step 2: Add blog posts as sources
    if progress_callback:
        progress_callback(2, total_steps, "Uploading blog posts...")

    sources = []
    for i, blog in enumerate(blogs, 1):
        sources.append({
            "name": blog.get("title", f"Blog Post {i}"),
            "content": blog.get("content", "")
        })

    add_text_sources(project_number, notebook_id, sources, location, region)

    # Build the NotebookLM URL
    notebook_url = f"https://notebooklm.google.com/notebook/{notebook_id}"

    return {
        "notebook_id": notebook_id,
        "notebook_url": notebook_url
    }
