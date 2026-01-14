"""
Image Generator Module - Using Gemini's native image generation (Nano Banana Pro)
"""

from google import genai
from google.genai import types
from typing import Optional


def generate_image(
    blog_title: str,
    blog_content: str,
    api_key: str,
    style: str = "realistic"
) -> bytes:
    """
    Generate a featured image using Gemini's native image generation.

    Args:
        blog_title: Title of the blog post
        blog_content: Full blog content (used for context)
        api_key: Google API key
        style: Image style - "realistic", "illustration", or "artistic"

    Returns:
        PNG image as bytes
    """
    client = genai.Client(api_key=api_key)

    # Create image prompt
    image_prompt = create_image_prompt(blog_title, blog_content, style)

    # Use Gemini's native image generation model
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        )
    )

    # Extract image from response
    # Response has multiple parts - find the one with image data
    if response.candidates:
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    # Check if this part has inline_data (image)
                    try:
                        if part.inline_data and part.inline_data.data:
                            image_data = part.inline_data.data
                            # Verify it's actual image data (should be large)
                            if isinstance(image_data, bytes) and len(image_data) > 1000:
                                return image_data
                    except Exception:
                        continue

    raise Exception("No image was generated in response")


def create_image_prompt(
    blog_title: str,
    blog_content: str,
    style: str = "realistic"
) -> str:
    """
    Create an image prompt based on blog content.
    """
    # Style descriptions
    style_descriptions = {
        "realistic": "photorealistic, high quality photograph, professional lighting",
        "illustration": "modern digital illustration, clean vector style, vibrant colors",
        "artistic": "artistic, creative composition, visually striking, contemporary art"
    }

    style_desc = style_descriptions.get(style, style_descriptions["realistic"])

    # Build prompt
    prompt = f"Generate a featured image for a blog post titled: {blog_title}. Style: {style_desc}. The image should be professional, visually appealing, and contain no text."

    return prompt


def generate_all_images(
    blogs: list,
    api_key: str,
    style: str = "realistic",
    progress_callback: Optional[callable] = None
) -> list:
    """
    Generate featured images for all blog posts.

    Args:
        blogs: List of blog post dicts (with 'title' and 'content' keys)
        api_key: Google API key
        style: Image style preference
        progress_callback: Optional callback function(image_number, total)

    Returns:
        List of image bytes
    """
    images = []

    for i, blog in enumerate(blogs):
        if progress_callback:
            progress_callback(i + 1, len(blogs))

        try:
            image_bytes = generate_image(
                blog.get("title", "Blog Post"),
                blog.get("content", ""),
                api_key,
                style
            )
            images.append(image_bytes)
        except Exception as e:
            print(f"Failed to generate image {i + 1}: {e}")
            images.append(None)

    return images
