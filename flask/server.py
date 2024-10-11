# pip install Flask Flask-SocketIO

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

app = Flask(__name__)
socketio = SocketIO(logger=True, engineio_logger=True)
socketio.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(data):
    print('Received message: ' + str(data))
    emit('message', data, broadcast=True)

@socketio.on('offer')
def handle_offer(data):
    print('Received offer: ' + str(data))
    emit('offer', data, broadcast=True)

@socketio.on('answer')
def handle_answer(data):
    print('Received answer: ' + str(data))
    emit('answer', data, broadcast=True)

@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    print('Received ICE candidate: ' + str(data))
    emit('ice-candidate', data, broadcast=True)

if __name__ == '__main__':
    pywsgi.WSGIServer(("localhost", 5000), app, handler_class=WebSocketHandler).serve_forever()
