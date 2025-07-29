from flask import Flask, render_template
from flask_socketio import SocketIO
import speech_recognition as sr
import threading
import os

app = Flask(__name__)
socketio = SocketIO(app)

# Listening control flag
listening = False
listener_thread = None

# Intent–response map
RESPONSES = {
    "how are you": "I’m fine, thank you for asking!",
    "what is your name": "I am Jarvis AI, at your service.",
    "hello": "Hello there!",
    # add more...
}

# Text-to-speech helper
def say(text):
    os.system(f"say '{text}'")  # macOS; swap for espeak or PowerShell on other OS
    print(f"Jarvis: {text}")

# Continuous listen-and-respond loop
def continuous_listener():
    global listening
    r = sr.Recognizer()
    with sr.Microphone() as mic:
        say("Jarvis listening mode activated.")
        while listening:
            socketio.emit('status', {'msg': 'Listening...'})
            audio = r.listen(mic)
            try:
                transcription = r.recognize_google(audio).lower().strip()
                socketio.emit('user_msg', {'msg': transcription})
                # stop on exit or quit
                if transcription in ('exit', 'quit'):
                    stop_listening()
                    break
                response = RESPONSES.get(transcription, 
                    "Sorry, I don't know how to respond to that.")
                socketio.emit('bot_msg', {'msg': response})
                say(response)
            except sr.UnknownValueError:
                err = "Sorry, I didn't catch that."
                socketio.emit('bot_msg', {'msg': err})
                say(err)
            except sr.RequestError as e:
                err = f"Recognition error: {e}"
                socketio.emit('bot_msg', {'msg': err})
                say(err)
        say("Jarvis listening mode deactivated.")
        socketio.emit('status', {'msg': 'Stopped listening.'})

# Control functions
def start_listening_mode():
    global listening, listener_thread
    if not listening:
        listening = True
        listener_thread = threading.Thread(target=continuous_listener, daemon=True)
        listener_thread.start()
        socketio.emit('status', {'msg': 'Listening mode started.'})

def stop_listening():
    global listening
    if listening:
        listening = False

# Socket event handlers
@socketio.on('start_listening')
def handle_start_listening():
    start_listening_mode()

@socketio.on('stop_listening')
def handle_stop_listening():
    stop_listening()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
