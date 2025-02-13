import streamlit as st
import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import fal_client

# Function definitions from the original notebook

def generate_podcast_transcript(topic):
    podcast_template = ChatPromptTemplate.from_template("""
      Create an engaging conversation between two speakers discussing the topic: {topic}

      Requirements:
      - Generate exactly 5 back-and-forth exchanges
      - Make it natural and conversational
      - Include specific details about the {topic}
      - Each line should start with either "Speaker 1:" or "Speaker 2:"

      Here's an example of the format (but create NEW content about {topic}, don't copy this example):
      Speaker 1: [First speaker's line]
      Speaker 2: [Second speaker's line]

      The response of the each speaker should be at most 20 words. The conversation has to be insightful, engaging, explanatory, deep diving and educational.

      It should be in the style of a podcast where one speaker slightly is more knowledgeable than the other.

      You are allowed to write only in the below format. Just give the output in the below format in a single string. No additional delimiters.

      The content should be explanatory, deep diving and educational.

      Speaker 1: Hey, did you catch the game last night?
      Speaker 2: Of course! What a match—it had me on the edge of my seat.
      Speaker 1: Same here! That last-minute goal was unreal. Who's your MVP?
      Speaker 2: Gotta be the goalie. Those saves were unbelievable.


      Remember: Create completely new dialogue about {topic}, don't use the above example.
      """)

    llm = ChatOpenAI(
        model="deepseek/deepseek-chat",
        openai_api_key=st.secrets["OPENROUTER_API_KEY"],
        openai_api_base="https://openrouter.ai/api/v1"
    )

    chain = podcast_template | llm
    response = chain.invoke({"topic": topic})
    return response.content

def generate_podcast(topic):
    st.info(f"🎙️ Generating podcast transcript about: {topic}")
    st.info("-" * 50)

    transcript_result = generate_podcast_transcript(topic)

    st.info("\n✍️ Generated transcript:")
    st.info("-" * 50)
    st.text(transcript_result) # Using st.text to preserve formatting

    st.info("\n🔊 Converting transcript to audio...")
    st.info("-" * 50)

    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                st.info(f"🎵 {log['message']}")

    try:
        result = fal_client.subscribe(
            "fal-ai/playai/tts/dialog",
            {
                "input": transcript_result,
                "voices": [
                    {
                        "voice": "Jennifer (English (US)/American)",
                        "turn_prefix": "Speaker 1: "
                    },
                    {
                        "voice": "Dexter (English (US)/American)",
                        "turn_prefix": "Speaker 2: "
                    }
                ]
            },
            api_key=st.secrets["FAL_KEY"], # Use st.secrets for FAL_KEY
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        st.success("\n✅ Audio generation complete!")
        audio_url = result['audio']['url']
        st.success(f"🔗 Audio URL: {audio_url}")

        return {
            "conversation": transcript_result,
            "audio_url": audio_url
        }

    except Exception as e:
        error_message = f"\n❌ Error generating audio: {str(e)}"
        st.error(error_message)
        return {
            "conversation": transcript_result,
            "audio_url": None,
            "error": str(e)
        }

# Streamlit App
st.set_page_config(
    page_title="Open Source NotebookLM Podcast Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎙️ Open Source NotebookLM Podcast Generator")
st.markdown("An open-source alternative to Google's NotebookLM for generating podcasts from topics.")
st.markdown("[Build Fast with AI](https://www.buildfastwithai.com/genai-course)")
st.markdown("---")

# Sidebar for API Keys and Instructions
with st.sidebar:
    st.header("API Keys")
    st.markdown("Please enter your API keys below. You can get them from:")
    st.markdown("[OpenRouter](https://openrouter.ai/) for `OPENROUTER_API_KEY`")
    st.markdown("[FAL AI](https://fal.ai/) for `FAL_KEY`")

    openrouter_api_key = st.text_input("OpenRouter API Key", type="password")
    fal_api_key = st.text_input("FAL API Key", type="password")

    if openrouter_api_key and fal_api_key:
        st.success("API Keys are set! You can now generate podcasts.")
        st.session_state['api_keys_set'] = True # Use session state to track if keys are set
    else:
        st.warning("Please enter both API Keys to use the app.")
        st.session_state['api_keys_set'] = False

    st.markdown("---")
    st.subheader("Instructions")
    st.markdown("1. **Enter API Keys** in the sidebar.")
    st.markdown("2. **Enter a topic** for your podcast in the text box below.")
    st.markdown("3. **Click 'Generate Podcast'** to create a transcript and audio.")
    st.markdown("4. **Listen to your podcast** using the audio player below.")


topic_input = st.text_input("Enter a topic for your podcast:", "Quantum Random Walks")

if st.button("Generate Podcast", disabled=not st.session_state.get('api_keys_set', False)):
    if not topic_input:
        st.error("Please enter a topic for the podcast.")
    else:
        if 'api_keys_set' in st.session_state and st.session_state['api_keys_set']:
            podcast_result = generate_podcast(topic_input)

            if podcast_result and podcast_result['audio_url']:
                st.audio(podcast_result['audio_url'], format='audio/wav') # fal-ai/playai/tts/dialog returns wav
            else:
                st.error("Podcast audio generation failed. See error messages above.")
        else:
            st.error("API Keys are not set. Please enter them in the sidebar.")
else:
    st.info("Enter a topic and click 'Generate Podcast' to begin!")
