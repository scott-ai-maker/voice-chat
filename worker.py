from openai import OpenAI
import requests
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

openai_client = OpenAI()


def speech_to_text(audio_binary):
    """Convert speech to text using OpenAI Whisper API"""
    try:
        if not audio_binary or len(audio_binary) == 0:
            raise ValueError("Empty audio data received")

        # Create a file-like object from the audio binary data
        audio_file = io.BytesIO(audio_binary)
        audio_file.name = "audio.webm"

        # Use OpenAI Whisper API for transcription
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en",
            prompt="This is a conversation with a voice assistant."
        )

        return transcript.text

    except ValueError as e:
        print(f"Validation error in speech_to_text: {str(e)}")
        return "Error: Invalid audio data"
    except Exception as e:
        # Log the full error for debugging
        print(f"Error in speech_to_text: {type(e).__name__}: {str(e)}")
        # Return user-friendly message
        if "rate_limit" in str(e).lower():
            return "Error: Service is busy, please try again"
        elif "invalid_api_key" in str(e).lower():
            return "Error: Service configuration issue"
        else:
            return "Error: Could not transcribe audio"


def text_to_speech(text, voice="alloy"):
    """Convert text to speech using OpenAI TTS API"""
    # Use OpenAI TTS API
    response = openai_client.audio.speech.create(
        model="tts-1",
        voice=voice,  # Options: alloy, echo, fable, onyx, nova, shimmer
        input=text
    )

    # Return the audio content as bytes
    return response.content


def openai_process_message(user_message, conversation_history=None):
    """Process user message and get AI response with conversation history"""
    # Start with system message
    messages = [
        {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and conversational."}
    ]

    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return completion.choices[0].message.content
