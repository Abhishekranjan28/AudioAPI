from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import os
import asyncio
import edge_tts
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set in environment variables")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)
CORS(app)

# Voice mapping for various languages
language_to_voice = {
    "en": "en-US-JennyNeural",  # English
    "es": "es-ES-HelenaNeural",  # Spanish
    "fr": "fr-FR-DeniseNeural",  # French
    "de": "de-DE-KatjaNeural",   # German
    "it": "it-IT-ElsaNeural",    # Italian
    "pt": "pt-PT-DianaNeural",   # Portuguese
    "ru": "ru-RU-DariyaNeural",  # Russian
    "ja": "ja-JP-NanamiNeural",  # Japanese
    "ko": "ko-KR-SunHiNeural",   # Korean
    "zh": "zh-CN-XiaoyiNeural",  # Chinese (Simplified)
    "hi": "hi-IN-MadhurNeural",  # Hindi
    "ar": "ar-AR-ZakiNeural",    # Arabic
    "tr": "tr-TR-MuzafferNeural",# Turkish
    "pl": "pl-PL-AgnieszkaNeural", # Polish
    "nl": "nl-NL-CoenNeural",    # Dutch
    "sv": "sv-SE-EmiliaNeural",  # Swedish
    "no": "no-NO-KristineNeural",# Norwegian
    "fi": "fi-FI-NikoNeural",    # Finnish
    "da": "da-DK-BirgitteNeural",# Danish
    "cs": "cs-CZ-AdamNeural",    # Czech
}

# Default to English voice if no mapping is found
def get_voice_for_language(lang):
    return language_to_voice.get(lang, "en-US-JennyNeural")

async def generate_tts(text, lang_code, output_path):
    voice = get_voice_for_language(lang_code)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    text = data.get("text")
    lang = data.get("lang", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        prompt = f"Summarize the following text in 50 words in {lang} language: The text is \n{text}"
        response = model.generate_content(prompt)
        summary = response.text.strip()

        print(summary)

        # Temp file for audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.close()

        # Run async TTS generation
        asyncio.run(generate_tts(summary, lang, temp_file.name))

        return jsonify({
            "translated": summary,
            "audio_url": f"/audio/{os.path.basename(temp_file.name)}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/audio/<filename>')
def get_audio(filename):
    file_path = os.path.join(tempfile.gettempdir(), filename)
    return send_file(file_path, mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
