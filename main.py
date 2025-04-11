from flask import Flask, request, render_template, send_file
from openai import OpenAI
import os
from deep_translator import GoogleTranslator
from gtts import gTTS
from werkzeug.utils import secure_filename
import base64
import tempfile
import speech_recognition as sr
import httpx

app = Flask(__name__, template_folder='static/html', static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize OpenAI client with explicit http_client to avoid proxy issues
openai_api_key = os.environ.get("OPENAI_API_KEY")
# Create httpx client without proxies
http_client = httpx.Client()
client = OpenAI(api_key=openai_api_key, http_client=http_client)
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
        # Using the newer OpenAI API syntax for version 1.3.0
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a thoughtful content reviewer who carefully analyzes images. When you see an image, you first objectively describe what you see in the image, then you analyze whether it might contain harmful elements including AI-generated deceptive content, misinformation, racism, hate speech, or other problematic content. Always start with a factual description of what the image contains before providing any analysis."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please analyze this image. First describe what you see in the image objectively. Then analyze whether it contains any problematic content such as:  AI-generated fake content, misinformation, racism, hate speech, offensive symbolism, or other harmful material. Provide context about why certain elements might be concerning if present."},
                        {"type": "image_url", "image_url": {"url": base64_image}}
                    ]
                }
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Image analysis error: {e}")
        print(f"Error details: {error_details}")
        return f"Image analysis error: {e}. Please check server logs for details."

def analyse_and_translate(content, lang_code):
    global spoken_text
    if not content.strip():
        spoken_text = ""
        return {"english": "", "translated": ""}
    
    prompt = f"""Please analyze the following content:

"{content}"

First, describe the content objectively. Then analyze whether it contains any concerning elements such as hate speech, bullying, racism, sexism, body-shaming, or manipulation. 

If harmful content is present, explain:
1. What specific type of harmful content it is
2. The context that makes it harmful
3. The potential impact on readers
4. How someone might respond to such content safely

If the content is not harmful, explain why it appears to be safe and respectful.
"""
    
    try:
        # Using the newer OpenAI API syntax for version 1.3.0
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly and supportive online safety companion who provides thoughtful, contextual analysis of potentially harmful content."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        english_analysis = response.choices[0].message.content
        
        # Using deep-translator
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
    debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    app.run(debug=debug_mode, host='0.0.0.0', port=5050)
