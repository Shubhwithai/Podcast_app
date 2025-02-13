import streamlit as st
import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import fal_client

# Set page configuration
st.set_page_config(
    page_title="Open Source NotebookLM Podcast Generator",
    page_icon="🎙️",
    layout="wide"
)

# Main title and description
st.title("🎙️ Open Source NotebookLM Podcast Generator")
st.markdown("""
An open-source alternative to Google's NotebookLM for generating AI-powered podcasts.
[Learn with Build Fast with AI](https://www.buildfastwithai.com/genai-course)
""")
st.markdown("---")

# Sidebar configuration
with st.sidebar:
    st.header("🔑 API Configuration")
    st.markdown("Get your API keys from:")
    st.markdown("- [FAL.AI](https://fal.ai/)")
    st.markdown("- [OpenRouter](https://openrouter.ai/)")
    
    # API key inputs
    fal_key = st.text_input("FAL API Key", type="password")
    openrouter_key = st.text_input("OpenRouter API Key", type="password")
    
    st.markdown("---")
    st.header("📖 Instructions")
    st.markdown("""
    1. Enter API keys
    2. Input podcast topic
    3. Click Generate Podcast
    4. Listen to generated audio
    """)

# Podcast generation functions
def generate_podcast_transcript(topic):
    """Generate podcast transcript using Deepseek model"""
    podcast_template = ChatPromptTemplate.from_template("""
    Create an engaging conversation between two speakers discussing: {topic}
    Requirements:
    - 5 natural back-and-forth exchanges
    - Each line starts with Speaker 1: or Speaker 2:
    - Max 20 words per response
    - Educational and insightful content
    """)
    
    llm = ChatOpenAI(
        model="deepseek/deepseek-chat",
        openai_api_key=openrouter_key,
        openai_api_base="https://openrouter.ai/api/v1"
    )
    
    chain = podcast_template | llm
    response = chain.invoke({"topic": topic})
    return response.content

def generate_podcast_audio(transcript):
    """Convert transcript to audio using FAL.AI"""
    try:
        os.environ["FAL_KEY"] = fal_key  # Set FAL key for current session
        
        result = fal_client.subscribe(
            "fal-ai/playai/tts/dialog",
            {
                "input": transcript,
                "voices": [
                    {"voice": "Jennifer (English (US)/American)", "turn_prefix": "Speaker 1: "},
                    {"voice": "Dexter (English (US)/American)", "turn_prefix": "Speaker 2: "}
                ]
            },
            with_logs=True
        )
        return result['audio']['url']
    except Exception as e:
        st.error(f"Audio generation failed: {str(e)}")
        return None

# Main app interface
topic = st.text_input("🎤 Enter podcast topic:", "Quantum Random Walks")

if st.button("🚀 Generate Podcast", disabled=not (fal_key and openrouter_key)):
    if not topic:
        st.error("Please enter a podcast topic")
    else:
        with st.spinner("Generating transcript..."):
            transcript = generate_podcast_transcript(topic)
        
        st.subheader("📜 Generated Transcript")
        st.text(transcript)
        
        with st.spinner("Generating audio (this may take a minute)..."):
            audio_url = generate_podcast_audio(transcript)
        
        if audio_url:
            st.subheader("🎧 Podcast Audio")
            st.audio(audio_url, format="audio/wav")
            st.success("Podcast generated successfully!")
        else:
            st.error("Failed to generate audio. Please check your API keys.")
else:
    if not (fal_key and openrouter_key):
        st.warning("Please enter both API keys to continue")
