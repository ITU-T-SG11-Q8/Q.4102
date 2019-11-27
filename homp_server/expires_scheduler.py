import time
import threading
from datetime import datetime

import schedule

from service.service import Service
from classes.overlay import Overlay
from classes.peer import Peer


class ExpiresScheduler:
    def __init__(self):
        self._interval = 0
        self._sleep_interval = 1
        self._fired_callback = None
        self.fmt = "%Y-%m-%d %H:%M:%S.%f"
        self._is_run_scheduler = True

    def start(self, interval, callback):
        self._interval = interval
        self._fired_callback = callback

        print("[ExpiresScheduler] Start...", flush=True)
        t = threading.Thread(target=self.run_pending, daemon=True)
        t.start()

    def stop(self):
        schedule.clear()
        self._interval = 0
        self._is_run_scheduler = False

    def run_pending(self):
        if self._interval > 0:
            schedule.every(self._interval).seconds.do(self.checked_expires)
        else:
            print("[ExpiresScheduler] Stop...", flush=True)
            return

        while self._is_run_scheduler:
            schedule.run_pending()
            time.sleep(self._sleep_interval)

    def fired_callback(self, overlay_id, peer_id):
        if self._fired_callback is not None:
            self._fired_callback(overlay_id, peer_id)

    def checked_expires(self):
        try:
            overlay_dic = Service.get().get_overlay_dict()
            remove_peer_list = []

            for item in overlay_dic.values():
                overlay: Overlay = item
                peer_dict = overlay.get_peer_dict()

                for p_item in peer_dict.values():
                    peer: Peer = p_item
                    update_time = datetime.strptime(str(peer.update_time), self.fmt)
                    now_time = datetime.strptime(str(datetime.now()), self.fmt)
                    delta_time = now_time - update_time
                    if delta_time.seconds > peer.expires:
                        remove_peer_list.append((overlay.overlay_id, peer.peer_id))

            if len(remove_peer_list) > 0:
                for overlay_id, peer_id in remove_peer_list:
                    self.fired_callback(overlay_id, peer_id)
        except:
            print('ExpiresScheduler... Error')
