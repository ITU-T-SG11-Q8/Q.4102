# import schedule
# import time
# import threading
#
#
# class HeartScheduler:
#     def __init__(self, send_interval, check_interval):
#         self.send_interval = send_interval
#         self.check_interval = check_interval
#         self.send_job = None
#         self.check_job = None
#         self.is_run_Scheduler = False
#
#     def start(self, send_func, check_func):
#         if not self.is_run_Scheduler:
#             self.is_run_Scheduler = True
#             print("----------[HeartScheduler] Start...", flush=True)
#             t = threading.Thread(target=self.run_pending, args=(send_func, check_func), daemon=True)
#             t.start()
#
#     def stop(self):
#         print("----------[HeartScheduler] Stop...", flush=True)
#         if self.send_job is not None and self.check_job is not None:
#             self.is_run_Scheduler = False
#             schedule.cancel_job(self.send_job)
#             schedule.cancel_job(self.check_job)
#
#         schedule.clear()
#
#     def run_pending(self, send_func, check_func):
#         self.send_job = schedule.every(self.send_interval).seconds.do(send_func)
#         self.check_job = schedule.every(self.check_interval).seconds.do(check_func)
#
#         while self.is_run_Scheduler:
#             schedule.run_pending()
#             time.sleep(1)
