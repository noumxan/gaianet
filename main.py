from flask import Flask, request, render_template_string, send_file
import openai
import os
from googletrans import Translator
from gtts import gTTS
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
import speech_recognition as sr
import tempfile

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

openai.api_key = os.environ.get("OPENAI_API_KEY", "your_openai_key_here")
translator = Translator()
spoken_text = ""

HTML_PAGE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>CoSafe AI – Online Safety Companion</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f9f9f9, #e6f2ff);
            padding: 2rem;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background-color: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 2rem;
        }
        textarea, select, input[type=file] {
            width: 100%;
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 10px;
            border: 1px solid #ccc;
            font-size: 1rem;
        }
        button {
            display: block;
            width: 100%;
            padding: 1rem;
            font-size: 1rem;
            border-radius: 10px;
            border: none;
            background-color: #0078d4;
            color: white;
            font-weight: bold;
            margin-top: 2rem;
            cursor: pointer;
        }
        button:hover {
            background-color: #005fa3;
        }
        .result {
            margin-top: 2rem;
            padding: 1.5rem;
            border-left: 6px solid #0078d4;
            background-color: #f0f8ff;
            border-radius: 12px;
        }
        audio {
            margin-top: 1rem;
            width: 100%;
        }
        label {
            font-weight: bold;
            margin-top: 1rem;
            display: block;
        }
        .report-section {
            margin-top: 2rem;
        }
        .report-section textarea {
            height: 100px;
        }
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>🛡️ CoSafe AI – Your Online Safety Companion</h1>
        <form method=\"post\" enctype=\"multipart/form-data\">
            <label>📝 Paste message, meme caption, or DM content:</label>
            <textarea name=\"content\" placeholder=\"e.g. You don’t belong here...\"></textarea>

            <label>🖼️ Upload a meme or screenshot:</label>
            <input type=\"file\" name=\"image\">

            <label>🎙️ Upload a voice message (MP3/WAV):</label>
            <input type=\"file\" name=\"audio\">

            <label>🌍 Select your native language:</label>
            <select name=\"language\" required>
                <option value=\"en\">English</option>
                <option value=\"ur\">Urdu</option>
                <option value=\"hi\">Hindi</option>
                <option value=\"ar\">Arabic</option>
                <option value=\"pl\">Polish</option>
            </select>

            <button type=\"submit\">🔎 Analyse Now</button>
        </form>

        {% if result %}
        <div class=\"result\">
            <h2>🧠 AI Analysis (English):</h2>
            <p>{{ result['english'] }}</p>

            <h2>🌍 Translated ({{ lang_name }}):</h2>
            <p>{{ result['translated'] }}</p>

            <audio controls>
                <source src=\"/play\" type=\"audio/mpeg\">
                Your browser does not support the audio element.
            </audio>

            <div class=\"report-section\">
                <p>📬 Do you want to report this to <strong>Show Racism the Red Card UK</strong>?</p>
                <a href=\"https://mail.google.com/mail/?view=cm&fs=1&to=contact@theredcard.org&su=Online%20Hate%20Report&body=Please%20investigate%20this%20content:%20{{ result['english'] | urlencode }}\" target=\"_blank\">
                    <button>📤 Generate Gmail Email</button>
                </a>
                <p style=\"margin-top:1rem;\">💡 You can also visit <a href=\"https://www.report-it.org.uk/\" target=\"_blank\">report-it.org.uk</a> to report hate crime anonymously in the UK.</p>
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""
def get_language_name(code):
    lang_map = {
        "en": "English",
        "ur": "Urdu",
        "hi": "Hindi",
        "ar": "Arabic",
        "pl": "Polish"
    }
    return lang_map.get(code, "Selected Language")

def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        return f"Error reading image: {e}"

def extract_text_from_audio(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data)
    except Exception as e:
        return f"Error transcribing audio: {e}"

def analyse_and_translate(content, lang_code):
    global spoken_text
    prompt = f"""
You are an ethical AI assistant that helps users understand harmful or offensive content. Analyse this message for hate, bullying, racism, sexism, body-shaming, or manipulation. Explain clearly and gently:

{content}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly and supportive online safety companion."},
                {"role": "user", "content": prompt}
            ]
        )
        english_analysis = response.choices[0].message.content
        translated = translator.translate(english_analysis, dest=lang_code).text
        spoken_text = translated
        return {"english": english_analysis, "translated": translated}
    except Exception as e:
        return {"english": f"Error: {e}", "translated": ""}

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    lang_name = None
    if request.method == "POST":
        content = request.form.get("content", "").strip()
        lang_code = request.form["language"]
        lang_name = get_language_name(lang_code)

        image = request.files.get("image")
        audio = request.files.get("audio")

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            content += "\n" + extract_text_from_image(image_path)

        if audio:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                audio.save(temp_audio.name)
                content += "\n" + extract_text_from_audio(temp_audio.name)

        result = analyse_and_translate(content, lang_code)
    return render_template_string(HTML_PAGE, result=result, lang_name=lang_name)

@app.route("/play")
def play_audio():
    global spoken_text
    tts = gTTS(text=spoken_text, lang='en')
    tts.save("speech.mp3")
    return send_file("speech.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5050)
