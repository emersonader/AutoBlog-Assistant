"""
Research Module - AI-powered topic research using Google Gemini
"""

from google import genai
from google.genai import types


def research_topic(topic: str, api_key: str) -> dict:
    """
    Research a topic using Google Gemini AI.

    Args:
        topic: The topic to research
        api_key: Google API key

    Returns:
        dict with keys:
            - summary: Overall research summary
            - key_facts: List of important facts
            - angles: List of 3 unique blog angles
            - sources: Suggested source types
    """
    client = genai.Client(api_key=api_key)

    prompt = f"""You are a professional research assistant. Research the following topic thoroughly and provide comprehensive information that can be used to write blog posts.

Topic: {topic}

Please provide your research in the following format:

## Research Summary
Provide a comprehensive 2-3 paragraph summary of the topic, covering the most important aspects.

## Key Facts
List 10-15 important facts, statistics, or insights about this topic. Include specific numbers, dates, or data points where relevant.

## Blog Angles
Suggest exactly 3 unique and engaging angles for blog posts about this topic. For each angle:
- Provide a compelling title
- Explain the angle in 2-3 sentences
- Note what makes this angle unique or interesting

## Suggested Sources
List types of authoritative sources that would typically cover this topic (e.g., academic journals, industry publications, government reports).

Be thorough, accurate, and provide actionable information for content creation."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=4096,
            temperature=0.7
        )
    )

    response_text = response.text

    # Parse the response into structured data
    result = parse_research_response(response_text)
    result["raw_response"] = response_text

    return result


def parse_research_response(response: str) -> dict:
    """
    Parse Gemini's research response into structured data.
    """
    sections = {
        "summary": "",
        "key_facts": [],
        "angles": [],
        "sources": []
    }

    current_section = None
    current_content = []

    lines = response.split("\n")

    for line in lines:
        line_lower = line.lower().strip()

        # Detect section headers
        if "research summary" in line_lower and line.startswith("#"):
            if current_section and current_content:
                sections[current_section] = process_section(current_section, current_content)
            current_section = "summary"
            current_content = []
        elif "key facts" in line_lower and line.startswith("#"):
            if current_section and current_content:
                sections[current_section] = process_section(current_section, current_content)
            current_section = "key_facts"
            current_content = []
        elif "blog angles" in line_lower and line.startswith("#"):
            if current_section and current_content:
                sections[current_section] = process_section(current_section, current_content)
            current_section = "angles"
            current_content = []
        elif "suggested sources" in line_lower and line.startswith("#"):
            if current_section and current_content:
                sections[current_section] = process_section(current_section, current_content)
            current_section = "sources"
            current_content = []
        elif current_section:
            current_content.append(line)

    # Process the last section
    if current_section and current_content:
        sections[current_section] = process_section(current_section, current_content)

    return sections


def process_section(section_type: str, content: list) -> any:
    """
    Process content based on section type.
    """
    text = "\n".join(content).strip()

    if section_type == "summary":
        return text
    elif section_type in ["key_facts", "sources"]:
        # Extract list items
        items = []
        for line in content:
            line = line.strip()
            if line.startswith(("-", "*", "•")) or (len(line) > 2 and line[0].isdigit() and line[1] in ".):"):
                # Remove bullet/number prefix
                item = line.lstrip("-*•0123456789.): ").strip()
                if item:
                    items.append(item)
        return items if items else [text] if text else []
    elif section_type == "angles":
        # Parse blog angles - look for numbered items or headers
        angles = []
        current_angle = {"title": "", "description": ""}

        for line in content:
            line = line.strip()
            if not line:
                if current_angle["title"]:
                    angles.append(current_angle)
                    current_angle = {"title": "", "description": ""}
                continue

            # Check for title patterns
            if line.startswith(("1.", "2.", "3.", "**", "###")):
                if current_angle["title"]:
                    angles.append(current_angle)
                # Extract title
                title = line.lstrip("123.#*- ").strip()
                title = title.rstrip("*").strip()
                current_angle = {"title": title, "description": ""}
            elif current_angle["title"]:
                # Add to description
                desc_line = line.lstrip("-*• ").strip()
                if current_angle["description"]:
                    current_angle["description"] += " " + desc_line
                else:
                    current_angle["description"] = desc_line

        # Don't forget the last angle
        if current_angle["title"]:
            angles.append(current_angle)

        # Ensure we have exactly 3 angles
        while len(angles) < 3:
            angles.append({
                "title": f"Perspective {len(angles) + 1}",
                "description": "An alternative viewpoint on the topic."
            })

        return angles[:3]

    return text
