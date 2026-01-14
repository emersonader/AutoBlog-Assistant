"""
File Manager Module - Local file saving and organization
"""

import os
import re
from pathlib import Path
from typing import Optional


def slugify(text: str) -> str:
    """
    Convert text to a URL/filename-friendly slug.
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove non-alphanumeric characters (except hyphens)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    # Limit length
    return text[:50] if text else "untitled"


def get_output_dir(base_path: str = None) -> Path:
    """
    Get the output directory path.
    """
    if base_path:
        return Path(base_path)

    # Default to output folder in project directory
    current_dir = Path(__file__).parent.parent
    return current_dir / "output"


def create_topic_folder(topic: str, base_path: str = None) -> Path:
    """
    Create a folder for the topic's outputs.

    Args:
        topic: The topic name
        base_path: Optional base output directory

    Returns:
        Path to the created folder
    """
    output_dir = get_output_dir(base_path)
    topic_slug = slugify(topic)

    topic_folder = output_dir / topic_slug

    # Handle existing folders by adding a number suffix
    if topic_folder.exists():
        counter = 1
        while (output_dir / f"{topic_slug}-{counter}").exists():
            counter += 1
        topic_folder = output_dir / f"{topic_slug}-{counter}"

    topic_folder.mkdir(parents=True, exist_ok=True)
    return topic_folder


def save_blog(
    folder: Path,
    blog: dict,
    index: int
) -> Path:
    """
    Save a blog post as a Markdown file.

    Args:
        folder: Output folder path
        blog: Blog dict with 'title', 'content', 'meta_description'
        index: Blog number (1, 2, or 3)

    Returns:
        Path to the saved file
    """
    title = blog.get("title", f"Blog Post {index}")
    content = blog.get("content", "")
    meta_description = blog.get("meta_description", "")

    # Create filename from title
    title_slug = slugify(title)
    filename = f"blog_{index}_{title_slug}.md"

    file_path = folder / filename

    # Add meta description as YAML frontmatter
    frontmatter = f"""---
title: "{title}"
description: "{meta_description}"
---

"""

    full_content = frontmatter + content

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_content)

    return file_path


def save_image(
    folder: Path,
    image_bytes: bytes,
    index: int,
    blog_title: str = ""
) -> Optional[Path]:
    """
    Save an image as a PNG file.

    Args:
        folder: Output folder path
        image_bytes: PNG image data
        index: Image number (1, 2, or 3)
        blog_title: Optional blog title for filename

    Returns:
        Path to the saved file, or None if image_bytes is None
    """
    if image_bytes is None:
        return None

    title_slug = slugify(blog_title) if blog_title else "image"
    filename = f"image_{index}_{title_slug}.png"

    file_path = folder / filename

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return file_path


def save_outputs(
    topic: str,
    blogs: list,
    images: list,
    base_path: str = None
) -> dict:
    """
    Save all outputs (blogs and images) to a topic folder.

    Args:
        topic: The topic name
        blogs: List of blog dicts
        images: List of image bytes (can contain None for failed images)
        base_path: Optional base output directory

    Returns:
        dict with keys:
            - folder: Path to the output folder
            - blogs: List of blog file paths
            - images: List of image file paths (None for failed images)
    """
    folder = create_topic_folder(topic, base_path)

    saved_blogs = []
    saved_images = []

    # Save blogs
    for i, blog in enumerate(blogs, 1):
        blog_path = save_blog(folder, blog, i)
        saved_blogs.append(blog_path)

    # Save images
    for i, (image_bytes, blog) in enumerate(zip(images, blogs), 1):
        image_path = save_image(
            folder,
            image_bytes,
            i,
            blog.get("title", "")
        )
        saved_images.append(image_path)

    # Create an index file with links to all content
    create_index_file(folder, topic, blogs, saved_blogs, saved_images)

    return {
        "folder": folder,
        "blogs": saved_blogs,
        "images": saved_images
    }


def create_index_file(
    folder: Path,
    topic: str,
    blogs: list,
    blog_paths: list,
    image_paths: list
) -> Path:
    """
    Create an index file listing all generated content.
    """
    index_content = f"""# {topic} - Generated Content

## Blog Posts

"""

    for i, (blog, blog_path) in enumerate(zip(blogs, blog_paths), 1):
        title = blog.get("title", f"Blog Post {i}")
        word_count = blog.get("word_count", 0)
        filename = blog_path.name
        index_content += f"{i}. [{title}]({filename}) ({word_count} words)\n"

    index_content += "\n## Featured Images\n\n"

    for i, image_path in enumerate(image_paths, 1):
        if image_path:
            filename = image_path.name
            index_content += f"{i}. ![Image {i}]({filename})\n"
        else:
            index_content += f"{i}. (Image generation failed)\n"

    index_content += f"""

---
Generated by AutoBlog Assistant
"""

    index_path = folder / "README.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    return index_path
