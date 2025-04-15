from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from gtts import gTTS
from deep_translator import GoogleTranslator
import requests
import tempfile
import os

app = Flask(__name__)
CORS(app)

HUGGINGFACE_API_TOKEN = "your_huggingface_token_here"
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

def summarize_with_flan_t5_api(text):
    payload = {
        "inputs": f"summarize: {text}",
        "parameters": {"max_length": 150, "min_length": 30, "do_sample": False}
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    result = response.json()

    if isinstance(result, list) and "generated_text" in result[0]:
        return result[0]["generated_text"]
    else:
        raise ValueError("Invalid response from Hugging Face API")

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    text = data.get("text")
    lang = data.get("lang", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        summary = summarize_with_flan_t5_api(text)
        translated = GoogleTranslator(source='auto', target=lang).translate(summary)

        # Generate TTS
        tts = gTTS(text=translated, lang=lang)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)

        return jsonify({
            "summary": summary,
            "translated": translated,
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
