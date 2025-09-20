# vista/logger.py
import datetime

class Logger:
    @staticmethod
    def info(msg):
        now = datetime.datetime.now().isoformat()
        print(f"[INFO] {now} - {msg}")

    @staticmethod
    def error(msg):
        now = datetime.datetime.now().isoformat()
        print(f"[ERROR] {now} - {msg}")
