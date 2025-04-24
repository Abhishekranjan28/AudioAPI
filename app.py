from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from gtts import gTTS
import tempfile
import os
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
        
        tts = gTTS(text=summary, lang=lang)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)

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
