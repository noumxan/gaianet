from flask import Flask, request, render_template_string, send_file
import openai
import os
from googletrans import Translator
from gtts import gTTS
from werkzeug.utils import secure_filename
import base64
import tempfile
import speech_recognition as sr

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

openai.api_key = os.environ.get("OPENAI_API_KEY", "your_openai_key_here")
translator = Translator()
spoken_text = ""

HTML_PAGE = """
<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>CoSafe AI – Online Safety Companion</title>
    <style>
        body { font-family: sans-serif; background-color: #f2f7fb; margin: 0; padding: 2rem; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #0078d4; }
        textarea, select, input[type='file'] { width: 100%; padding: 1rem; margin: 1rem 0; border-radius: 6px; border: 1px solid #ccc; }
        button { width: 100%; background-color: #0078d4; color: white; padding: 1rem; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #005fa3; }
        .result { margin-top: 2rem; background: #eaf4ff; padding: 1rem; border-left: 5px solid #0078d4; border-radius: 6px; }
        audio { width: 100%; margin-top: 1rem; }
    </style>
</head>
<body>
<div class='container'>
    <h1>🛡️ CoSafe AI – Your Online Safety Companion</h1>
    <form method='post' enctype='multipart/form-data'>
        <label>🖼️ Upload a meme or screenshot:</label>
        <input type='file' name='image' required>

        <label>🎙️ Upload a voice message (MP3/WAV):</label>
        <input type='file' name='audio'>

        <label>🌍 Select your native language:</label>
        <select name='language' required>
            <option value='en'>English</option>
            <option value='ur'>Urdu</option>
            <option value='hi'>Hindi</option>
            <option value='ar'>Arabic</option>
            <option value='pl'>Polish</option>
        </select>

        <button type='submit'>🔎 Analyse Now</button>
    </form>

    {% if result %}
    <div class='result'>
        <h3>🧠 AI Analysis (English):</h3>
        <p>{{ result['english'] }}</p>

        <h3>🌍 Translated ({{ lang_name }}):</h3>
        <p>{{ result['translated'] }}</p>

        <h3>🔍 Image Evaluation:</h3>
        <p>{{ result['image_check'] }}</p>

        <audio controls>
            <source src='/play' type='audio/mpeg'>
            Your browser does not support the audio element.
        </audio>

        <h3>📬 Report This</h3>
        <p>If you'd like to report this incident, click the button below to open a Gmail email draft.</p>
        <a href='https://mail.google.com/mail/?view=cm&fs=1&to=contact@theredcard.org&su=Online%20Hate%20Report&body=Please%20investigate%20this%20content:%20{{ result['english'] | urlencode }}' target='_blank'>
            <button type='button'>📤 Report via Gmail</button>
        </a>
        <p>Or report anonymously at: <a href='https://www.report-it.org.uk/' target='_blank'>report-it.org.uk</a></p>
    </div>
    {% endif %}
</div>
</body>
</html>
"""

def extract_text_from_audio(audio_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data)
    except Exception as e:
        return f"Error transcribing audio: {e}"

def analyse_image_with_openai(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        base64_image = f"data:image/jpeg;base64,{encoded_image}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a strict AI content reviewer. Analyse images for AI-generation, misinformation, racism, or ethical concerns with high certainty."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is this image AI-generated or fake? Does it include racism, hate, misinformation, or inappropriate content?"},
                        {"type": "image_url", "image_url": {"url": base64_image}}
                    ]
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Image analysis error: {e}"

def analyse_and_translate(content, lang_code):
    global spoken_text
    if not content.strip():
        spoken_text = ""
        return {"english": "", "translated": ""}
    prompt = f"You are a safety assistant. Analyse this message for hate, bullying, racism, sexism, body-shaming, or manipulation. Explain gently:\n\n{content}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly and supportive online safety companion."},
                {"role": "user", "content": prompt}
            ]
        )
        english_analysis = response.choices[0].message.content.strip()
        translated = translator.translate(english_analysis, dest=lang_code).text
        spoken_text = translated
        return {"english": english_analysis, "translated": translated}
    except Exception as e:
        return {"english": f"Error: {e}", "translated": ""}

def get_language_name(code):
    return {
        "en": "English",
        "ur": "Urdu",
        "hi": "Hindi",
        "ar": "Arabic",
        "pl": "Polish"
    }.get(code, "Selected Language")

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    lang_name = None
    if request.method == "POST":
        lang_code = request.form["language"]
        lang_name = get_language_name(lang_code)

        image = request.files.get("image")
        audio = request.files.get("audio")

        image_check = ""
        content = ""

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_check = analyse_image_with_openai(image_path)
            content += image_check

        if audio:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
                audio.save(temp_audio.name)
                content += "\n" + extract_text_from_audio(temp_audio.name)

        result = analyse_and_translate(content, lang_code)
        result['image_check'] = image_check
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
