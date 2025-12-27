import base64
import json
from flask import Flask, render_template, request, session
from worker import speech_to_text, text_to_speech, openai_process_message
from flask_cors import CORS 
import os
import bleach
import logging
from logging.handlers import RotatingFileHandler

# Configure Logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler(
    'logs/voice_assistant.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO) 
app.logger.info('Voice Assistant startup')


def sanitize_input(text, max_length=1000):
    """
    Sanitize user input to prevent XSS and limit length.

    Why each step:
    - strip(): Remove leading/trailing whitespaces that wastes tokens
    - max_length: Prevent abuse by limiting input size (cost control)
    - bleach.clean(): Remove all HTML tags and dangerous content
    - allowed_tags=[]: No HTML tags allowed at all
    """
    if not text or not isinstance(text, str):
        return ""

    text = text.strip()[:max_length]
    text = bleach.clean(text, tags=[], strip=True)
    return text


app = Flask(__name__)
app.secret_key = os.environ.get(
    'SECRET_KEY', 'dev-secret-key-change-in-production')
cors = CORS(app, resources={r"/*": {"origins": "*"}},
            supports_credentials=True)

# Store conversation histories per session
conversation_histories = {}


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/speech-to-text', methods=['POST'])
def speech_to_text_route():
    audio_binary = request.data

    # Validate audio size (prevent DoS attacks)
    if len(audio_binary) > 10 * 1024 * 1024:  # 10MB limit
        return app.response_class(
            response=json.dumps({'error': 'Audio file too large'}),
            status=400,
            mimetype='application/json'
        )

    text = speech_to_text(audio_binary)
    text = sanitize_input(text)  # Sanitize the transcribed text

    response = app.response_class(
        response=json.dumps({'text': text}),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/process-message', methods=['POST'])
def process_prompt_route():
    user_message = request.json.get('userMessage', '')
    user_message = sanitize_input(user_message)  # Sanitize immediately

    if not user_message:
        return app.response_class(
            response=json.dumps({'error': 'Message cannot be empty'}),
            status=400,
            mimetype='application/json'
        )

    voice = request.json.get('voice', 'alloy')
    # Validate voice is in allowed list
    allowed_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    if voice not in allowed_voices:
        voice = 'alloy'

    # Get or create session ID
    if 'session_id' not in session:
        import uuid
        session['session_id'] = str(uuid.uuid4())

    session_id = session['session_id']

    # Initialize conversation history for this session if needed
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    # Get AI response with conversation history
    ai_response_text = openai_process_message(
        user_message, conversation_histories[session_id])

    # Update conversation history
    conversation_histories[session_id].append(
        {"role": "user", "content": user_message})
    conversation_histories[session_id].append(
        {"role": "assistant", "content": ai_response_text})

    # Limit history to last 20 messages to avoid token limits
    if len(conversation_histories[session_id]) > 20:
        conversation_histories[session_id] = conversation_histories[session_id][-20:]

    # Convert response to speech with selected voice
    ai_response_speech = text_to_speech(ai_response_text, voice)

    # Encode audio as base64
    ai_response_speech_base64 = base64.b64encode(
        ai_response_speech).decode('utf-8')

    response = app.response_class(
        response=json.dumps({
            "openaiResponseText": ai_response_text,
            "openaiResponseSpeech": ai_response_speech_base64
        }),
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == "__main__":
    app.run(port=8000, host='0.0.0.0')
