from flask import Flask, render_template_string
import threading
import time
from logger import Logger

class Server:
    def __init__(self):
        self.app = Flask(__name__)
        self.messages = []
        self._add_routes()
        self.logger = Logger()

    def _add_routes(self):
        @self.app.route('/')
        def index():
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            return render_template_string(self._get_html_template(),
                                          time=current_time,
                                          messages=self.messages)

    def _get_html_template(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                }
                .top-bar {
                    background-color: #333;
                    color: white;
                    padding: 10px;
                    text-align: center;
                    position: fixed;
                    top: 0;
                    width: 100%;
                }
                .content {
                    margin-top: 50px;
                    padding: 20px;
                }
                ul {
                    list-style-type: none;
                    padding: 0;
                }
                li {
                    background-color: #f9f9f9;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <div class="top-bar">Current Time: {{ time }}</div>
            <div class="content">
                <h2>Messages</h2>
                <ul>
                    {% for message in messages %}
                        <li>{{ message }}</li>
                    {% endfor %}
                </ul>
            </div>
        </body>
        </html>
        '''

    def get_current_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

    def add_message(self, message):
        timestamp = self.get_current_time()
        message = f"{timestamp}: {message}"
        self.messages.append(message)
        self.logger.add_message(message)

    def run(self, host='0.0.0.0', port=5000):
        thread = threading.Thread(target=self.app.run, kwargs={'host': host, 'port': port, 'debug': False, 'use_reloader': False})
        thread.start()

if __name__ == '__main__':
    server = Server()
    logger = Logger()

    server.add_message("Hello, World!")

    server.add_message("This is a test message.")
    server.run()
