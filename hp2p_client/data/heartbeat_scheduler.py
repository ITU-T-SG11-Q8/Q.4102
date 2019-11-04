import schedule
import time
import threading


class HeartScheduler:
    def __init__(self, send_interval, check_interval):
        self.send_interval = send_interval
        self.check_interval = check_interval
        self.send_job = None
        self.check_job = None
        self.run_while = True

    def start(self, send_func, check_func):
        print("----------[HeartScheduler] Start...", flush=True)
        t = threading.Thread(target=self.run_pending, args=(send_func, check_func))
        t.start()

    def stop(self):
        print("----------[HeartScheduler] Stop...", flush=True)
        if self.send_job is not None and self.check_job is not None:
            schedule.cancel_job(self.send_job)
            schedule.cancel_job(self.check_job)
            self.run_while = False

    def run_pending(self, send_func, check_func):
        self.send_job = schedule.every(self.send_interval).seconds.do(send_func)
        self.check_job = schedule.every(self.check_interval).seconds.do(check_func)

        while self.run_while:
            schedule.run_pending()
            time.sleep(1)
