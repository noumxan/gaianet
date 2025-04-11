# GaiaScan - Online Safety Companion

GaiaScan is a web application that helps users identify potentially harmful content in images and text. It uses OpenAI's powerful models to analyze content and provides feedback in multiple languages.

## Features

- Image content analysis using GPT-4 Vision
- Voice message transcription and analysis
- Multiple language support (English, Urdu, Hindi, Arabic, Polish)
- Text-to-speech feedback
- Easy reporting options for harmful content
- Team information and project background

## Setup and Installation

1. Clone this repository
2. Create a virtual environment with Python 3.10 or 3.11:
   ```
   python3.10 -m venv venv
   source venv/bin/activate
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on the example:
   ```
   cp .env.example .env
   ```
5. Edit the `.env` file and add your OpenAI API key
6. Run the application:
   ```
   python main.py
   ```
7. Open your browser and navigate to `http://localhost:5050/` to use the application

## API Keys

To use this application, you'll need:
- An OpenAI API key with access to GPT-4 Vision (https://platform.openai.com/api-keys)

## Project Structure

- `main.py`: Main application file
- `static/html/`: HTML templates
- `static/css/`: CSS stylesheets
- `static/img/`: Image assets
- `uploads/`: Temporary storage for uploaded files

## About the Team

GaiaScan was created by a team of four:
- Nouman Syed - Backend Development
- Glory Iloba - Front End and Design
- Ogochukwu Juwah - Research on Sustainability and Design
- Palvir Ginn - DevOps and Pitching

Learn more about the team and project background on the About page of the application.

## Dependencies

- Flask: Web framework
- OpenAI: For content analysis
- deep-translator: For translation
- gTTS (Google Text-to-Speech): For text-to-speech conversion
- SpeechRecognition: For voice transcription

## License

MIT

## Notes

This application is intended for educational purposes. Always exercise caution when dealing with potentially harmful online content. 