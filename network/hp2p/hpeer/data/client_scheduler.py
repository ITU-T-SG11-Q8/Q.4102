import schedule
import time
import threading


class ClientScheduler:
    def __init__(self):
        self._heartbeat_send_job = None
        self._heartbeat_check_job = None
        self._expires_job = None
        self._checked_primary_job = None
        self._is_start = False

    def start(self):
        if not self._is_start:
            self._is_start = True
            print("****************************[CLIENT SCHEDULER] Start...", flush=True)
            t = threading.Thread(target=self.run_pending, args=(), daemon=True)
            t.start()

    def stop(self):
        if self._is_start:
            self._is_start = False
            print("****************************[CLIENT SCHEDULER] Stop...", flush=True)
            schedule.clear()

    def run_pending(self):
        while self._is_start:
            schedule.run_pending()
            time.sleep(1)

    def is_set_heartbeat_scheduler(self):
        return self._heartbeat_send_job is not None and self._heartbeat_check_job is not None

    def append_heartbeat_scheduler(self, send_interval, send_job, check_interval, check_job):
        if not self.is_set_heartbeat_scheduler():
            print("****************************[CLIENT SCHEDULER] START HEARTBEAT_SCHEDULER...", flush=True)
            self._heartbeat_send_job = schedule.every(send_interval).seconds.do(send_job)
            self._heartbeat_check_job = schedule.every(check_interval).seconds.do(check_job)

    def remove_heartbeat_scheduler(self):
        if self.is_set_heartbeat_scheduler():
            print("****************************[CLIENT SCHEDULER] STOP HEARTBEAT_SCHEDULER...", flush=True)
            schedule.cancel_job(self._heartbeat_send_job)
            schedule.cancel_job(self._heartbeat_check_job)
            self._heartbeat_send_job = None
            self._heartbeat_check_job = None

    def is_set_expires_scheduler(self):
        return self._expires_job is not None

    def append_expires_scheduler(self, expires_interval, expires_job):
        if not self.is_set_expires_scheduler():
            print("****************************[CLIENT SCHEDULER] START EXPIRES_SCHEDULER...", flush=True)
            self._expires_job = schedule.every(expires_interval).seconds.do(expires_job)

    def remove_expires_scheduler(self):
        if self.is_set_expires_scheduler():
            print("****************************[CLIENT SCHEDULER] STOP EXPIRES_SCHEDULER...", flush=True)
            schedule.cancel_job(self._expires_job)
            self._expires_job = None

    def is_set_checked_primary_scheduler(self):
        return self._checked_primary_job is not None

    def append_checked_primary_scheduler(self, checked_primary_interval, checked_primary_job):
        if not self.is_set_checked_primary_scheduler():
            print("****************************[CLIENT SCHEDULER] START CHECKED_PRIMARY_SCHEDULER...", flush=True)
            self._checked_primary_job = schedule.every(checked_primary_interval).seconds.do(checked_primary_job)

    def remove_checked_primary_scheduler(self):
        if self.is_set_checked_primary_scheduler():
            print("****************************[CLIENT SCHEDULER] STOP CHECKED_PRIMARY_SCHEDULER...", flush=True)
            schedule.cancel_job(self._checked_primary_job)
            self._checked_primary_job = None
