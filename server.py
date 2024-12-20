import sqlite3

from flask import Flask, render_template_string, request
import threading
import time

from logger import Logger

class Server:
    def __init__(self, main):
        self.app = Flask(__name__)
        self._add_routes()
        self.logger = main.get_logger()
        self.database = main.get_database()
        self.config = main.get_config()
        self.main = main

    def _add_routes(self):
        @self.app.route('/')
        def index():
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            current_date = time.strftime('%Y-%m-%d', time.localtime())

            # Fetch all messages for the current day
            daily_messages = self.get_messages_for_day(current_date)
            daily_messages.sort(reverse=True)

            return render_template_string(self.get_html_template(),
                                          time=current_time,
                                          messages=daily_messages)

        @self.app.route('/', methods=['POST'])
        def handle_post():
            data = request.data.decode('utf-8')
            if data is not None and data is not " " and data is not "":
                self.main.debug(f"{data} < to split")
                timer, message = data.split(":", 1)
                self.main.debug(message)
                self.main.add_message(message)
                self.main.stop_timer(timer)
                return "Data received successfully", 200
            return "Bad Request", 400

    def get_html_template(self):
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

    def get_messages_for_day(self, date):
        """
        Fetches messages for a specific day from the SQLite database.

        :param date: The date in yyyy-mm-dd format.
        :return: A list of messages for the day.
        """
        query = "SELECT timestamp, string FROM light_logs WHERE timestamp LIKE ?"
        date_pattern = f"{date}%"  # Matches all timestamps starting with the selected date
        try:
            conn = sqlite3.connect(self.config["database"]["path"])
            cursor = conn.cursor()
            cursor.execute(query, (date_pattern,))
            results = cursor.fetchall()
            # Format messages as "timestamp: message"
            return [f"{row[0]}: {row[1]}" for row in results]
        except Exception as e:
            print(f"Error fetching messages for {date}: {e}")
            return []

    def run(self):
        host: str = self.config["server"]["host"]
        port: int = self.config["server"]["port"]
        thread = threading.Thread(target=self.app.run, args=(host, port), kwargs={
            "debug": False,
            "use_reloader": False
        }, daemon=True)
        thread.start()
        print(host, port)
