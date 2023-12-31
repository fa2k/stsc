from flask import Flask, request
from datetime import datetime, timedelta
import threading
import signal
import requests
import smtplib
from email.message import EmailMessage
import configparser
import os

config = configparser.ConfigParser()
config.read('config.ini')
app = Flask(__name__)

last_heartbeat = datetime.now()

def send_email(subject):
    try:
        msg = EmailMessage()
        msg.set_content(f"heartbeat-alerter.py message at {datetime.now()}.")
        msg['Subject'] = subject
        msg['From'] = config.get("email", "from")
        msg['To'] = config.get("email", "to")
        server = smtplib.SMTP(
            config.get("email", "smtp_host"),
            config.getint("email", "smtp_port")
            )
        server.starttls()
        server.login(config.get("email", "user"), config.get("email", "password"))
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Emailing error:", e)

def send_pushover(message):
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": config.get("pushover", "token"),
            "user": config.get("pushover", "user"),
            "message": message
        })
    except Exception as e:
        print("Pushover sending error:", e)

def periodic_check():
    global last_heartbeat
    try:
        reporting_interval_loop_count = 10 * 24 * 60
        loop_count = reporting_interval_loop_count # Start by reporting, with normal code path
        error_state = False
        while True:
            time_now = datetime.now()
            time_difference = time_now - last_heartbeat

            if time_difference > timedelta(minutes=3):
                if not error_state:
                    print("Heartbeat lost!")
                    send_email("Heartbeat lost!")
                    send_pushover("Heartbeat lost!")
                error_state = True
            else:
                if error_state:
                    # Non-essential message, intentionally just pushover
                    send_pushover("Heartbeat recovered!")
                error_state = False

            if loop_count == reporting_interval_loop_count:
                send_email("Stethoscope is working.")
                send_pushover("Stethoscope is working.")
                reporting_interval_loop_count = 0

            loop_count += 1
            threading.Event().wait(60)

    except Exception as e:
        send_email("FATAL: Stethoscope checking thread exited:" + str(e))
        send_pushover("FATAL: Stethoscope checking thread exited:" + str(e))

class GracefulExiter:
    def __init__(self):
        self.orig_handler = None

    def __call__(self, signum, frame):
        print("Stethoscope app is about to terminate...")
        send_email("Stethoscope app is terminating")
        send_pushover("Stethoscope app is terminating")
        if self.orig_handler:
            if callable(self.orig_handler):              # Call previous handler
                self.orig_handler(signum, frame)
            elif self.orig_handler == signal.SIG_DFL:    # Default disposition
                signal.signal(signum, signal.SIG_DFL)
                os.kill(os.getpid(), signum)

def wrap_signal(signal_to_wrap):
    graceful_exiter = GracefulExiter()
    orig_handler = signal.signal(signal_to_wrap, graceful_exiter)
    graceful_exiter.orig_handler = orig_handler


@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    global last_heartbeat
    last_heartbeat = datetime.now()
    #print(f"Received heartbeat at {last_heartbeat}")
    return "Received", 200

@app.route('/explicit_alarm', methods=['POST'])
def explicit_alarm():
    print("Received explicit alarm")
    send_email("Explicit alarm triggered")
    send_pushover("Explicit alarm triggered")
    return "Alarm received", 200

# Register the function for SIGTERM and SIGINT
wrap_signal(signal.SIGTERM)
wrap_signal(signal.SIGINT)

if __name__ == '__main__':
    # Start the periodic check in a new thread
    check_thread = threading.Thread(target=periodic_check)
    check_thread.start()

    # Start the Flask app
    app.run(host='0.0.0.0', port=64250)
