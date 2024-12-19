from flask import Flask, render_template_string, request
import threading
import time

from logger import Logger

class Server:
    def __init__(self, main):
        self.app = Flask(__name__)
        self._add_routes()
        self.logger = main.get_logger()
        self.messages = self.logger.get_last_messages(10)
        self.config = main.get_config()

    def _add_routes(self):
        @self.app.route('/')
        def index():
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            return render_template_string(self._get_html_template(),
                                          time=current_time,
                                          messages=self.messages)

        @self.app.route('/', methods=['POST'])
        def handle_post():
            data = request.data.decode('utf-8')  # Decode the received data
            self.add_message(data)
            self.logger.add_message(data)
            return "Data received successfully", 200

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

    def run(self):
        host: str = self.config["server"]["host"]
        port: int = self.config["server"]["port"]
        thread = threading.Thread(target=self.app.run(host=host,
                                                      port=port,
                                                      debug=False,
                                                      use_reloader=False),
                                  daemon=True)
        thread.start()
        print(host, port)
