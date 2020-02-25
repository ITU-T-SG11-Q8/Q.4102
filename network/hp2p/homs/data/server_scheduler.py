import time
import threading
import schedule
from datetime import datetime

from config import HOMS_CONFIG
from classes.overlay import Overlay
from classes.peer import Peer
from data.factory import Factory
from database.db_connector import DBConnector


class ServerScheduler:
    def __init__(self):
        self._interval = 0
        self._sleep_interval = 1
        self.fmt = "%Y-%m-%d %H:%M:%S.%f"
        self._is_run_scheduler = True
        self._is_remove_empty_overlay = HOMS_CONFIG['REMOVE_EMPTY_OVERLAY']

    def start(self, interval):
        self._interval = interval

        print("[ExpiresScheduler] Start.")
        t = threading.Thread(target=self.run_pending, daemon=True)
        t.start()

    def stop(self):
        schedule.clear()
        self._interval = 0
        self._is_run_scheduler = False

    def run_pending(self):
        if self._interval > 0:
            schedule.every(self._interval).seconds.do(self.check_alive_peer)
        else:
            print("[ExpiresScheduler] Stop.")
            return

        while self._is_run_scheduler:
            schedule.run_pending()
            time.sleep(self._sleep_interval)

    def remove_peer_and_empty_overlay(self, overlay_id, peer_id):
        db_connector = DBConnector()
        try:
            db_connector.delete("DELETE FROM hp2p_peer WHERE peer_id = %s AND overlay_id = %s", (peer_id, overlay_id))
            select_overlay = Factory.get().get_overlay(overlay_id)
            select_overlay.delete_peer(peer_id)
            Factory.get().get_web_socket_message_handler().send_log_message(overlay_id, peer_id, "Overlay Leave.")
            print("[ExpiresScheduler] Remove Peer =>", overlay_id, peer_id)

            if self._is_remove_empty_overlay and select_overlay.get_peer_dict_len() < 1:
                db_connector.delete("DELETE FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))
                db_connector.delete("DELETE FROM hp2p_peer WHERE overlay_id = %s", (overlay_id,))
                db_connector.delete("DELETE FROM hp2p_overlay WHERE overlay_id = %s", (overlay_id,))

                Factory.get().delete_overlay(overlay_id)
                Factory.get().get_web_socket_message_handler().send_remove_overlay_message(overlay_id)
                Factory.get().get_web_socket_message_handler().send_log_message(overlay_id, peer_id,
                                                                                "Overlay Removal(Empty).")
                print("[ExpiresScheduler] Remove Overlay(Empty).", overlay_id, peer_id)
            else:
                Factory.get().get_web_socket_message_handler().send_delete_peer_message(overlay_id, peer_id)

            db_connector.commit()
        except Exception as e:
            db_connector.rollback()
            print(e)

    def check_alive_peer(self):
        try:
            overlay_dic = Factory.get().get_overlay_dict()
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
                    self.remove_peer_and_empty_overlay(overlay_id, peer_id)

        except Exception as e:
            print(e)
