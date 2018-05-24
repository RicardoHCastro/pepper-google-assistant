from flask import Flask, request, send_file, render_template, jsonify
import urllib3
from gtts import gTTS
import configparser
import json
import requests
import base64
from naoqi import ALProxy
from flask_socketio import SocketIO
from threading import Thread


my_server = Flask(__name__)
socketio = SocketIO(my_server)
stream = None
wavstream = None
pepper = None
host = None
port = None


@my_server.route("/", methods=['GET'])
def root():
    return render_template('index.html')


@my_server.route("/texttospeech", methods=['GET'])
def tts():
    return render_template('tts.html')


@my_server.route("/pepper", methods=['POST'])
def pepper():
    req = request.json.get('input')
    altts = ALProxy("ALTextToSpeech", pepper, 9559)
    altts.say(str(req))
    return "success"


@my_server.route("/gtts", methods=['POST'])
def gtts():
    req = request.json.get('input')
    googletts = gTTS(text=req, lang='en')
    googletts.save("/tmp/syn.mp3")
    return "success"


@my_server.route("/gcloud", methods=['POST'])
def gcloud():
    headers = {
        'Content-Type': 'application/json'
    }
    resp = requests.post("https://cxl-services.appspot.com/proxy?url=https%3A%2F%2Ftexttospeech.googleapis.com%2Fv1beta1%2Ftext%3Asynthesize", headers=headers, data=json.dumps(request.get_json()))
    r = resp.json().get('audioContent')
    with open("/tmp/syn.mp3", 'w') as file:
        file.write(base64.decodestring(r))
    return "success"


@my_server.route("/playpepper", methods=['GET'])
def playstream():
    t = Thread(target=play_pepper)
    t.start()
    return "success"


@my_server.route("/stream", methods=['GET'])
def stream_mp3():
    return send_file('/tmp/syn.mp3', cache_timeout=0)


@my_server.route("/wavstream", methods=['GET'])
def stream_wav():
    return send_file('/tmp/syn.wav', cache_timeout=0)


def emit_socket(msg_type, msg):
    socketio.emit(msg_type, msg)


def play_pepper():
    audio = ALProxy("ALAudioPlayer", pepper, 9559)
    audio.playWebStream(stream, 1, 0)


def play_asistant_response():
    audio = ALProxy("ALAudioPlayer", pepper, 9559)
    audio.playWebStream(wavstream, 1, 0)


def start_server():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    global stream, wavstream, pepper, host, port
    config = configparser.ConfigParser()
    config.read('config.ini')

    host = config['IP']['Host']
    port = config['IP']['Port']

    stream = "http://" + str(host) + ":" + str(port) + "/stream"
    wavstream = "http://" + str(host) + ":" + str(port) + "/wavstream"
    pepper = str(config['IP']['Robot'])

    print("API is running")
    socketio.run(my_server, host=host, port=int(port))
