import sqlite3

from flask import Flask, render_template_string, request, render_template
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

            return render_template("index.html", time=current_time, messages=daily_messages)

        @self.app.route('/metrics')
        def metrics():
            daily_data = self.get_daily_string_counts() or []
            today_performance = self.get_performance_data(self.main.get_current_date()) or []
            high_low_data = self.get_high_low_data(self.main.get_current_date())

            print(f"High/Low Data: {high_low_data}")
            return render_template("metrics.html", daily_data=daily_data, today_performance=today_performance, high_low_data=high_low_data)


        @self.app.route('/', methods=['POST'])
        def handle_post():
            data = request.data.decode('utf-8')
            if data is not None and data != " " and data != "":
                self.main.debug(f"{data} < to split")
                timer, message = data.split(":", 1)
                self.main.debug(message)
                time_elapsed = self.main.stop_timer(timer)
                self.main.add_message(message, timer, time_elapsed)

                return "Data received successfully", 200
            return "Bad Request", 400

    def get_messages_for_day(self, date):
        """
        Fetches messages for a specific day from the SQLite database.

        :param date: The date in yyyy-mm-dd format.
        :return: A list of messages for the day.
        """
        query = "SELECT timestamp, string FROM light_logs WHERE timestamp LIKE ?"
        date_pattern = f"{date}%"
        results = self.execute_query(query, (date_pattern,))
        return [f"{row[0]}: {row[1]}" for row in results]

    def get_daily_string_counts(self):
        """
        Fetches the count of strings for each day from the SQLite database.

        :return: A list of dictionaries with 'date' and 'count'.
        """
        query = """
        SELECT DATE(timestamp) as date, COUNT(*) as count
        FROM light_logs
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) ASC
        """
        results = self.execute_query(query)
        return [{"date": row[0], "count": row[1]} for row in results]

    def get_performance_data(self, date):
        """
        Fetches the performance data for today based on 'timer_id' and 'time'.

        :return: A list of dictionaries with 'timer_id' and 'time'.
        """
        query = """
        SELECT timestamp, time
        FROM light_logs
        WHERE DATE(timestamp) = ?
        """

        results = self.execute_query(query, (date,))
        formatted_results = [{"timestamps": row[0].split(" ")[1], "time": row[1]} for row in results]
        self.main.debug(f"Formatted Results: {formatted_results}")
        return formatted_results

    def get_high_low_data(self, date):
        query = "SELECT timestamp, string FROM light_logs WHERE timestamp LIKE ?"
        date_pattern = f"{date}%"
        results = self.execute_query(query, (date_pattern,))
        formatted_results = []
        for row in results:
            timestamp = row[0]
            value = 0 if "HIGH" in row[1].upper() else 1
            formatted_results.append({"timestamp": timestamp, "value": value})
        return formatted_results

    def execute_query(self, query, params=()):
        """
        Executes an SQL query

        :param query: The SQL query to execute.
        :param params: A tuple of parameters to pass to the query.
        :return: A list of processed rows.
        """
        try:
            conn = sqlite3.connect(self.config["database"]["path"])
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()

            if not results:
                self.main.debug("results is null")
            return results
        except Exception as e:
            print(f"Error executing query: {e}")
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


