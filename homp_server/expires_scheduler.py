import schedule
import time
import threading


class ExpiresScheduler:
    def __init__(self):
        self.interval = 10

    def start(self, func):
        print("[ExpiresScheduler] Start...", flush=True)
        t = threading.Thread(target=self.run_pending, args=(func,))
        t.start()

    def run_pending(self, func):
        schedule.every(self.interval).seconds.do(func)

        while True:
            schedule.run_pending()
            time.sleep(1)
