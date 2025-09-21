import datetime

class Logger:
    @staticmethod
    def info(msg):
        now = datetime.datetime.now().isoformat()
        print(f"[INFO] {now} - {msg}")

    @staticmethod
    def debug(msg):
        now = datetime.datetime.now().isoformat()
        print(f"[DEBUG] {now} - {msg}")

    @staticmethod
    def error(msg):
        now = datetime.datetime.now().isoformat()
        print(f"[ERROR] {now} - {msg}")
