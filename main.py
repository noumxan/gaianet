from flask import Flask, request, render_template, send_file
import openai
import os
from deep_translator import GoogleTranslator
from gtts import gTTS
from werkzeug.utils import secure_filename
import base64
import tempfile
import speech_recognition as sr

app = Flask(__name__, template_folder='static/html', static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads'

openai.api_key = os.environ.get("OPENAI_API_KEY", "your_openai_key_here")
spoken_text = ""

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
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": "You are a strict AI content reviewer. Analyse images for AI-generation, misinformation, racism, or ethical concerns with high certainty."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is this image AI-generated or fake? Does it include racism, hate, misinformation, or inappropriate content?"},
                        {"type": "image_url", "image_url": {"url": base64_image}}
                    ]
                }
            ],
            max_tokens=300
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
        
        # Using deep-translator instead of googletrans
        translator = GoogleTranslator(source='en', target=lang_code)
        translated = translator.translate(english_analysis)
        
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

@app.route("/app", methods=["GET", "POST"])
def app_page():
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
    return render_template("app.html", result=result, lang_name=lang_name)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/play")
def play_audio():
    global spoken_text
    tts = gTTS(text=spoken_text, lang='en')
    tts.save("speech.mp3")
    return send_file("speech.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # Create static/img directory if it doesn't exist
    os.makedirs('static/img', exist_ok=True)
    app.run(debug=True, port=5050)
