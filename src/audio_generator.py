"""
Audio Generator Module - NotebookLM-style podcast audio using Google Gemini
"""

from google import genai
from google.genai import types
from typing import Optional


def generate_podcast_script(
    blog_title: str,
    blog_content: str,
    api_key: str
) -> str:
    """
    Generate a conversational podcast script from blog content.

    Args:
        blog_title: Title of the blog post
        blog_content: Full blog content
        api_key: Google API key

    Returns:
        Podcast script as a string
    """
    client = genai.Client(api_key=api_key)

    # Truncate content if too long
    content_excerpt = blog_content[:6000] if len(blog_content) > 6000 else blog_content

    prompt = f"""You are a podcast script writer. Create a conversational podcast script between two hosts discussing this blog post.

## Blog Title
{blog_title}

## Blog Content
{content_excerpt}

## Instructions

Create a natural, engaging podcast conversation between two hosts:
- **Alex**: Curious, asks good questions, represents the listener's perspective
- **Sam**: Knowledgeable, explains concepts clearly, shares insights

Requirements:
1. Length: 600-900 words (about 4-5 minutes when spoken)
2. Start with a brief intro where they introduce the topic
3. Cover the main points from the blog in a conversational way
4. Include natural reactions ("That's interesting!", "I didn't know that", etc.)
5. End with a brief wrap-up and key takeaway
6. Make it sound natural, not like reading an article
7. Use conversational language, not formal writing

Format the script like this:
Alex: [dialogue]
Sam: [dialogue]

Write only the script, no other text."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=4096,
            temperature=0.8
        )
    )

    return response.text


def generate_audio(
    script: str,
    api_key: str
) -> bytes:
    """
    Convert podcast script to audio using Gemini.

    Args:
        script: The podcast script text
        api_key: Google API key

    Returns:
        Audio bytes (WAV format)
    """
    client = genai.Client(api_key=api_key)

    prompt = f"""Read this podcast script aloud as a natural conversation between two people.
Make it sound like a real podcast with two distinct voices having a friendly discussion.

{script}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                        types.SpeakerVoiceConfig(
                            speaker="Alex",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name="Kore"
                                )
                            )
                        ),
                        types.SpeakerVoiceConfig(
                            speaker="Sam",
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                    voice_name="Puck"
                                )
                            )
                        )
                    ]
                )
            )
        )
    )

    # Extract audio from response
    if response.candidates:
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    try:
                        if part.inline_data and part.inline_data.data:
                            audio_data = part.inline_data.data
                            if isinstance(audio_data, bytes) and len(audio_data) > 1000:
                                return audio_data
                    except Exception:
                        continue

    raise Exception("No audio was generated in response")


def generate_audio_overview(
    blog: dict,
    api_key: str
) -> bytes:
    """
    Generate a complete audio overview for a blog post.

    Args:
        blog: Blog dict with 'title' and 'content' keys
        api_key: Google API key

    Returns:
        Audio bytes (WAV format)
    """
    title = blog.get("title", "Blog Post")
    content = blog.get("content", "")

    # Step 1: Generate the podcast script
    script = generate_podcast_script(title, content, api_key)

    # Step 2: Convert to audio
    audio_bytes = generate_audio(script, api_key)

    return audio_bytes


def generate_all_audio(
    blogs: list,
    api_key: str,
    progress_callback: Optional[callable] = None
) -> list:
    """
    Generate audio overviews for all blog posts.

    Args:
        blogs: List of blog post dicts
        api_key: Google API key
        progress_callback: Optional callback function(audio_number, total)

    Returns:
        List of audio bytes (None for failed generations)
    """
    audios = []

    for i, blog in enumerate(blogs):
        if progress_callback:
            progress_callback(i + 1, len(blogs))

        try:
            audio_bytes = generate_audio_overview(blog, api_key)
            audios.append(audio_bytes)
        except Exception as e:
            print(f"Failed to generate audio {i + 1}: {e}")
            audios.append(None)

    return audios
