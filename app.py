from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyC4RwK4x692XDcHZikOaKfpxWHmIXm4kuM")
MURF_API_KEY = "ap2_1ed5cd30-2f51-4ebc-b8f6-33c6a31c81e7"

VULGAR_WORDS = [
    "badword1", "badword2", "offensiveword",
    "fuck", "shit", "asshole", "bitch"
]

def contains_vulgar(text):
    text_lower = text.lower()
    return any(bad_word in text_lower for bad_word in VULGAR_WORDS)

def get_bot_reply(user_input):
    url = (
        f"https://generativelanguage.googleapis.com/"
        f"v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
    )

    prompt_text = (
        "You are a smart NetIQ bot. Keep responses short, precise, 5-6 lines (~50 words). "
        "When a user asks who you are, respond: 'I am a smart NetIQ bot.' "
        "If the user asks about your name, respond: 'I am a smart NetIQ bot.' "
        "If the user asks who made you, respond: 'I was made by NetIQ.' "
        f"Question: {user_input}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Extract text from the first candidate
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Gemini API error:", e)
        return "Sorry, something went wrong while generating a response."

def get_murf_audio_url(text):
    url = "https://api.murf.ai/speech/generate"
    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "voice": "en-US-wesley",
        "text": text,
        "format": "mp3"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("audioUrl")
    except Exception as e:
        print("Murf TTS error:", e)
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json.get('user_input', '').strip()
    if not user_input:
        return jsonify({
            'response': "Please enter a valid question.",
            'audio_url': None
        })

    if contains_vulgar(user_input):
        rejection_message = (
            "I'm sorry, I cannot assist with that type of content. "
            "Please ask networking-related questions."
        )
        audio_url = get_murf_audio_url(rejection_message)
        return jsonify({
            'response': rejection_message,
            'audio_url': audio_url
        })

    bot_reply = get_bot_reply(user_input)
    audio_url = get_murf_audio_url(bot_reply)

    return jsonify({
        'response': bot_reply,
        'audio_url': audio_url
    })

if __name__ == "__main__":
    app.run(debug=True)
