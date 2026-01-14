"""
AutoBlog Assistant - Personal Blog Content Generator
A simple web app that generates researched blog posts with images using Google AI.
"""

import os
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Import our modules
from src.researcher import research_topic
from src.blog_generator import generate_all_blogs
from src.image_generator import generate_all_images
from src.file_manager import save_outputs

# Page configuration
st.set_page_config(
    page_title="AutoBlog Assistant",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .blog-preview {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_api_keys():
    """Check if Google API key is configured."""
    google_key = os.getenv("GOOGLE_API_KEY", "")

    if not google_key or google_key.startswith("your-"):
        return ["GOOGLE_API_KEY"]
    return []


def main():
    # Initialize session state
    if "step" not in st.session_state:
        st.session_state.step = "input"
    if "results" not in st.session_state:
        st.session_state.results = None

    # Header
    st.markdown('<p class="main-header">AutoBlog Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Generate 3 researched blog posts with images from any topic</p>', unsafe_allow_html=True)

    # Check API keys
    missing_keys = check_api_keys()
    if missing_keys:
        st.error(f"Missing API key: {', '.join(missing_keys)}")
        st.info("""
        **Setup Instructions:**
        1. Copy `.env.example` to `.env`
        2. Add your Google API key:
           - Get one at: https://aistudio.google.com/apikey
           - Or via Google Cloud Console
        3. Restart the app
        """)
        return

    # Main content based on step
    if st.session_state.step == "input":
        show_input_page()
    elif st.session_state.step == "generating":
        show_generating_page()
    elif st.session_state.step == "results":
        show_results_page()


def show_input_page():
    """Show the topic input page."""
    st.markdown("### Enter Your Topic")

    # Topic input
    topic = st.text_input(
        "What would you like to write about?",
        placeholder="e.g., sustainable fashion trends, healthy cooking recipes, remote work tips",
        help="Enter any topic you'd like to research and create blog posts about."
    )

    # Image style selection
    st.markdown("### Image Style (Optional)")
    image_style = st.radio(
        "Choose a style for your featured images:",
        options=["realistic", "illustration", "artistic"],
        format_func=lambda x: {
            "realistic": "Realistic (Photo-like)",
            "illustration": "Illustration (Clean, modern)",
            "artistic": "Artistic (Creative, unique)"
        }[x],
        horizontal=True
    )

    # Generate button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Generate Blog Posts", type="primary", use_container_width=True):
            if not topic.strip():
                st.error("Please enter a topic first!")
            else:
                st.session_state.topic = topic.strip()
                st.session_state.image_style = image_style
                st.session_state.step = "generating"
                st.rerun()

    # Example topics
    with st.expander("Need inspiration? Try these topics:"):
        examples = [
            "The future of artificial intelligence",
            "Sustainable living tips for beginners",
            "Remote work productivity hacks",
            "Healthy meal prep ideas",
            "Travel photography tips",
            "Personal finance for millennials"
        ]
        for example in examples:
            if st.button(example, key=f"example_{example}"):
                st.session_state.topic = example
                st.session_state.image_style = "realistic"
                st.session_state.step = "generating"
                st.rerun()


def show_generating_page():
    """Show the progress/generating page."""
    topic = st.session_state.topic
    image_style = st.session_state.image_style

    st.markdown(f"### Generating content for: *{topic}*")
    st.markdown("---")

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Get Google API key
        google_key = os.getenv("GOOGLE_API_KEY")

        # Step 1: Research
        status_text.markdown("**Step 1/4:** Researching topic...")
        progress_bar.progress(10)

        research = research_topic(topic, google_key)
        progress_bar.progress(25)

        # Step 2: Generate blogs
        status_text.markdown("**Step 2/4:** Writing blog posts... (this may take a few minutes)")
        progress_bar.progress(30)

        def blog_progress(current, total):
            pct = 30 + int((current / total) * 35)
            progress_bar.progress(pct)
            status_text.markdown(f"**Step 2/4:** Writing blog post {current} of {total}...")

        blogs = generate_all_blogs(topic, research, google_key, blog_progress)
        progress_bar.progress(65)

        # Step 3: Generate images
        status_text.markdown("**Step 3/4:** Creating featured images...")
        progress_bar.progress(70)

        def image_progress(current, total):
            pct = 70 + int((current / total) * 20)
            progress_bar.progress(pct)
            status_text.markdown(f"**Step 3/4:** Creating image {current} of {total}...")

        images = generate_all_images(blogs, google_key, image_style, image_progress)
        progress_bar.progress(90)

        # Step 4: Save files
        status_text.markdown("**Step 4/4:** Saving files...")
        saved = save_outputs(topic, blogs, images)
        progress_bar.progress(100)

        # Store results
        st.session_state.results = {
            "topic": topic,
            "research": research,
            "blogs": blogs,
            "images": images,
            "saved": saved
        }
        st.session_state.step = "results"
        st.rerun()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.markdown("---")
        if st.button("Try Again"):
            st.session_state.step = "input"
            st.rerun()


def show_results_page():
    """Show the results page with previews and downloads."""
    results = st.session_state.results
    topic = results["topic"]
    blogs = results["blogs"]
    images = results["images"]
    saved = results["saved"]
    folder = saved["folder"]

    st.markdown("### Generation Complete!")
    st.success(f"Created 3 blog posts with images for: **{topic}**")

    # Output folder info
    st.info(f"Files saved to: `{folder}`")

    # Blog previews in tabs
    st.markdown("---")
    st.markdown("### Blog Post Previews")

    tabs = st.tabs([f"Blog {i+1}" for i in range(len(blogs))])

    for i, (tab, blog) in enumerate(zip(tabs, blogs)):
        with tab:
            title = blog.get("title", f"Blog Post {i+1}")
            content = blog.get("content", "")
            word_count = blog.get("word_count", 0)
            meta = blog.get("meta_description", "")

            st.markdown(f"**{title}**")
            st.caption(f"{word_count} words | {meta[:100]}...")

            # Show image if available
            if i < len(images) and images[i]:
                st.image(images[i], caption=f"Featured Image for Blog {i+1}", use_container_width=True)

            # Preview content (first 500 chars)
            with st.expander("Preview content"):
                st.markdown(content[:1000] + "...")

            # Download button for this blog
            blog_path = saved["blogs"][i]
            with open(blog_path, "r", encoding="utf-8") as f:
                blog_content = f.read()

            st.download_button(
                label=f"Download Blog {i+1} (Markdown)",
                data=blog_content,
                file_name=blog_path.name,
                mime="text/markdown",
                key=f"download_blog_{i}"
            )

    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Generate New Topic", type="primary", use_container_width=True):
            st.session_state.step = "input"
            st.session_state.results = None
            st.rerun()

    with col2:
        # Show folder path
        st.markdown(f"**Output folder:**")
        st.code(str(folder))


if __name__ == "__main__":
    main()
