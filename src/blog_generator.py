"""
Blog Generator Module - AI-powered blog post generation using Google Gemini
"""

from google import genai
from google.genai import types
from typing import Optional


def generate_blog(
    topic: str,
    angle: dict,
    research: dict,
    api_key: str,
    target_words: int = 2250
) -> dict:
    """
    Generate a blog post using Google Gemini AI.

    Args:
        topic: The main topic
        angle: Dict with 'title' and 'description' for the blog angle
        research: Research data from researcher module
        api_key: Google API key
        target_words: Target word count (default 2250, range 2000-2500)

    Returns:
        dict with keys:
            - title: Blog post title
            - content: Full blog post in Markdown format
            - meta_description: SEO meta description
            - word_count: Approximate word count
    """
    client = genai.Client(api_key=api_key)

    # Prepare research context
    research_summary = research.get("summary", "")
    key_facts = research.get("key_facts", [])
    facts_text = "\n".join(f"- {fact}" for fact in key_facts[:10])

    prompt = f"""You are an expert blog writer. Write a comprehensive, engaging blog post based on the following information.

## Topic
{topic}

## Blog Angle/Focus
Title: {angle.get('title', topic)}
Approach: {angle.get('description', 'Write a comprehensive article on this topic.')}

## Research to Incorporate
{research_summary}

### Key Facts to Include
{facts_text}

## Requirements

1. **Length**: Write approximately {target_words} words (between 2000-2500 words)

2. **Structure**:
   - Start with a compelling headline (use # for H1)
   - Write an engaging introduction (2-3 paragraphs) that hooks the reader
   - Use clear section headers (## for H2, ### for H3)
   - Include 4-6 main sections with substantial content
   - End with a strong conclusion and call-to-action

3. **Style**:
   - Write in a conversational yet authoritative tone
   - Use short paragraphs (2-4 sentences each)
   - Include rhetorical questions to engage readers
   - Add bullet points or numbered lists where appropriate
   - Make it accessible to general readers, not just experts

4. **SEO Best Practices**:
   - Naturally incorporate relevant keywords
   - Use descriptive subheadings
   - Include internal linking suggestions (marked as [Link: topic])

5. **Content Quality**:
   - Provide actionable insights and practical takeaways
   - Include specific examples, statistics, or case studies from the research
   - Address potential questions readers might have
   - Avoid fluff - every paragraph should add value

Write the complete blog post in Markdown format. Begin with the title as an H1 heading."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.7
        )
    )

    content = response.text

    # Extract title from content
    title = extract_title(content)

    # Generate meta description
    meta_description = generate_meta_description(client, title, content)

    # Count words
    word_count = len(content.split())

    return {
        "title": title,
        "content": content,
        "meta_description": meta_description,
        "word_count": word_count
    }


def extract_title(content: str) -> str:
    """
    Extract the title from the blog post content.
    """
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip()
    return "Untitled Blog Post"


def generate_meta_description(
    client: genai.Client,
    title: str,
    content: str
) -> str:
    """
    Generate an SEO meta description for the blog post.
    """
    # Take first 1000 chars for context
    excerpt = content[:1000]

    prompt = f"""Write a compelling SEO meta description for this blog post.

Title: {title}

Content excerpt:
{excerpt}

Requirements:
- Between 150-160 characters
- Include the main topic/keyword
- Be compelling and encourage clicks
- Don't use quotes around it

Write only the meta description, nothing else."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=100,
            temperature=0.7
        )
    )

    return response.text.strip()


def generate_all_blogs(
    topic: str,
    research: dict,
    api_key: str,
    progress_callback: Optional[callable] = None
) -> list:
    """
    Generate all 3 blog posts for the given topic.

    Args:
        topic: The main topic
        research: Research data from researcher module
        api_key: Google API key
        progress_callback: Optional callback function(blog_number, total)

    Returns:
        List of 3 blog post dicts
    """
    blogs = []
    angles = research.get("angles", [])

    # Ensure we have 3 angles
    while len(angles) < 3:
        angles.append({
            "title": f"{topic} - Perspective {len(angles) + 1}",
            "description": "An alternative exploration of this topic."
        })

    for i, angle in enumerate(angles[:3]):
        if progress_callback:
            progress_callback(i + 1, 3)

        blog = generate_blog(topic, angle, research, api_key)
        blogs.append(blog)

    return blogs
