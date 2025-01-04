from vosk import Model, KaldiRecognizer
from datetime import datetime
import pyaudio
import wave
import os
import json
import webbrowser
import subprocess

USER = (f"{os.getenv('USER')}")

# Ścieżka do pliku z mapowaniem aplikacji
APP_MAPPING_FILE = "app_mapping.json"

# Initialize model and recognizer
model = Model(f"/home/{USER}/.ayva/en-US")
recognizer = KaldiRecognizer(model, 16000)

# Set up microphone for audio input
mic = pyaudio.PyAudio()
stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
stream.start_stream()


def play_audio(file_path):
    wf = wave.open(file_path, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    chunk_size = 1024
    data = wf.readframes(chunk_size)
    while data:
        stream.write(data)
        data = wf.readframes(chunk_size)
    stream.stop_stream()
    stream.close()
    p.terminate()

# Modify the speak function to handle single quotes properly
def speak(text):
    os.system(f'echo "{text}" | ./piper/piper --model ./piper/en_US-hfc_female-medium.onnx --output_file audio.wav')
    play_audio("audio.wav")


# Load application mapping from JSON file
def load_app_mapping():
    if os.path.exists(APP_MAPPING_FILE):
        with open(APP_MAPPING_FILE, "r") as f:
            return json.load(f)
    else:
        # Default application mapping
        default_mapping = {
            "firefox": "firefox",
            "fire fox": "firefox",
            "gedit": "gedit",
            "text editor": "gedit",
            "terminal": "gnome-terminal",
            "file manager": "nautilus"
        }
        # Create the file if it doesn't exist
        with open(APP_MAPPING_FILE, "w") as f:
            json.dump(default_mapping, f, indent=4)
        return default_mapping


# Define wake words
wake_words = ["eva", "ava"]

def listen_for_wake_word(text):
    for word in wake_words:
        if word in text.lower():
            return word
    return None

def handle_command(command):
    print(command)
    command = command.lower()
    app_mapping = load_app_mapping()  # Load app mapping dynamically
    if "what time is it" in command or "what's the time" in command:
        current_time = datetime.now()
        time = current_time.strftime('%H:%M')  # 24-hour format
        speak(f"It is now {time}")
    elif "who are you" in command:
        speak("I am Aiva, the yaerguOS assistant.") 
    elif "look up" in command:
        try:
            search_term = command.split("look up ")[1].strip().replace(" ", " ")
            speak(f"Searching {search_term}")
            site_name = command.split("look up ")[1].strip().replace(" ", "+")
            url = f"https://google.com/search?q={site_name}"
            webbrowser.open(url)
        except IndexError:
            speak("Sorry, I don't understand what to look up.")
    elif "open" in command and "dot com" in command:
        try:
            site_name = command.split("open ")[1].split(" dot com")[0].strip().replace(" ", "")
            url = f"https://{site_name}.com"
            speak(f"Opening {site_name} dot com")
            webbrowser.open(url)
        except IndexError:
            speak("Sorry, I couldn't figure out the website.") 
    elif "open" in command:
        try:
            # Extract application name from the command
            app_name = command.split("open ")[1].strip()
            # Match the app name to the mapped command
            app_command = app_mapping.get(app_name, app_name)
            speak(f"Opening {app_name}")
            subprocess.Popen(app_command, shell=True)
        except IndexError:
            speak("Sorry, I don't know what to open.")
        except FileNotFoundError:
            speak(f"Could not find the application {app_name}. Please check if it's installed.")
    else:
        speak("Sorry, I couldn't understand that.")

speak(f"Hi, {USER}.")
while True:
    data = stream.read(4096)

    if recognizer.AcceptWaveform(data):
        result = recognizer.Result()
        result_text = json.loads(result)['text']

        wake_word = listen_for_wake_word(result_text)
        if wake_word:
            speak("Yes?")
            print(f"Wake word detected: {wake_word}")
            while True:
                data = stream.read(4096)
                if recognizer.AcceptWaveform(data):
                    command_result = recognizer.Result()
                    command_text = json.loads(command_result)['text']
                    handle_command(command_text)
                    break
