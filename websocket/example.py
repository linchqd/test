#!/usr/local/bin/python3
# _*_ coding: utf-8 _*_


from flask import Flask, render_template
from flask_socketio import SocketIO, Namespace, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

class MyCustomNamespace(Namespace):
    def on_connect(self):
        print('------')

    def on_disconnect(self):
        print('========')

    def on_my_event(self, data):
        print(data)
        emit('my_response', data)


@app.route('/ws', methods=['get'])
def index():
    return render_template('example.html')


socketio.on_namespace(MyCustomNamespace('/webshell'))

if __name__ == '__main__':
    socketio.run(app)
