import pymysql
import json
from datetime import datetime

from config import DATABASE_CONFIG
from service.service import Service
from classes.overlay import Overlay
from classes.peer import Peer


class DBManager:
    def __init__(self):
        self.database_name = DATABASE_CONFIG["DB_DATABASE"]
        self.connect = pymysql.connect(host=DATABASE_CONFIG["DB_HOST"], port=DATABASE_CONFIG["DB_PORT"],
                                       user=DATABASE_CONFIG["DB_USER"], password=DATABASE_CONFIG["DB_PASS"],
                                       charset='utf8', cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.connect.cursor()

    def __del__(self):
        self.connect.close()

    # DB Check
    def init(self):
        try:
            is_execute = False
            self.cursor.execute("show databases like %s", (self.database_name,))
            database = self.cursor.fetchone()
            if database is None:
                is_execute = True
                self.cursor.execute("CREATE DATABASE IF NOT EXISTS {0}".format(self.database_name))
                print("[DBManager] CREATE DATABASE...", flush=True)

            self.cursor.execute("USE {0}".format(self.database_name))

            self.cursor.execute("show tables like 'hp2p_overlay'")
            hp2p_overlay = self.cursor.fetchone()
            if hp2p_overlay is None:
                is_execute = True
                self.cursor.execute("CREATE TABLE IF NOT EXISTS hp2p_overlay ( "
                                    "overlay_id varchar(50) COLLATE utf8_unicode_ci NOT NULL, "
                                    "title varchar(100) COLLATE utf8_unicode_ci NOT NULL, "
                                    "overlay_type varchar(50) COLLATE utf8_unicode_ci NOT NULL, "
                                    "sub_type varchar(50) COLLATE utf8_unicode_ci NOT NULL, "
                                    "owner_id varchar(50) COLLATE utf8_unicode_ci NOT NULL, "
                                    "expires int(11) NOT NULL DEFAULT 0, "
                                    "overlay_status varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL, "
                                    "description varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL, "
                                    "heartbeat_interval int(11) NOT NULL DEFAULT 0,  "
                                    "heartbeat_timeout int(11) NOT NULL DEFAULT 0, "
                                    "auth_keyword varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL, "
                                    "auth_type varchar(50) COLLATE utf8_unicode_ci NOT NULL,  "
                                    "auth_admin_key varchar(50) COLLATE utf8_unicode_ci NOT NULL,  "
                                    "auth_access_key varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,  "
                                    "created_at datetime NOT NULL, "
                                    "updated_at datetime NOT NULL,  "
                                    " PRIMARY KEY (`overlay_id`)"
                                    ")")
                print("[DBManager] CREATE TABLE hp2p_overlay", flush=True)

            self.cursor.execute("show tables like 'hp2p_peer'")
            hp2p_peer = self.cursor.fetchone()
            if hp2p_peer is None:
                is_execute = True
                self.cursor.execute("CREATE TABLE IF NOT EXISTS hp2p_peer ( "
                                    "peer_id varchar(50) COLLATE utf8_unicode_ci NOT NULL, "
                                    "overlay_id varchar(50) COLLATE utf8_unicode_ci NOT NULL,  "
                                    "ticket_id int(11) DEFAULT NULL,  "
                                    "overlay_type varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL, "
                                    "sub_type varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL, "
                                    "expires int(11) DEFAULT NULL,  "
                                    "address varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL, "
                                    "auth_password varchar(50) COLLATE utf8_unicode_ci NOT NULL,  "
                                    "num_primary int(11) NOT NULL DEFAULT 0,  "
                                    "num_out_candidate int(11) NOT NULL DEFAULT 0, "
                                    "num_in_candidate int(11) NOT NULL DEFAULT 0, "
                                    "costmap longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,  "
                                    "created_at datetime DEFAULT NULL, "
                                    "updated_at datetime DEFAULT NULL, "
                                    "report_time datetime DEFAULT NULL, "
                                    " PRIMARY KEY (peer_id, overlay_id)"
                                    ")")
                print("[DBManager] CREATE TABLE hp2p_peer", flush=True)

            self.cursor.execute("show tables like 'hp2p_auth_peer'")
            hp2p_auth_peer = self.cursor.fetchone()
            if hp2p_auth_peer is None:
                is_execute = True
                self.cursor.execute("CREATE TABLE IF NOT EXISTS hp2p_auth_peer ( "
                                    "overlay_id varchar(50) COLLATE utf8_unicode_ci NOT NULL, "
                                    "peer_id varchar(50) COLLATE utf8_unicode_ci NOT NULL, "
                                    "updated_at datetime DEFAULT NULL, "
                                    "PRIMARY KEY (overlay_id, peer_id)"
                                    ")")
                print("[DBManager] CREATE TABLE hp2p_auth_peer", flush=True)

            if is_execute:
                self.connect.commit()
        except Exception as e:
            print(e)
            self.connect.rollback()
            return False

        return True

    # DB Clear
    def clear_database(self):
        print("[CLEAR_DATABASE] CALL...", flush=True)
        try:
            self.cursor.execute("DELETE FROM hp2p_auth_peer")
            self.cursor.execute("DELETE FROM hp2p_peer")
            self.cursor.execute("DELETE FROM hp2p_overlay")
            self.connect.commit()
        except:
            self.connect.rollback()

    # DB Select & Create Overlay Map
    def create_overlay_map(self):
        print("[CREATE_OVERLAY_MAP] CALL...", flush=True)
        self.cursor.execute("SELECT * FROM hp2p_overlay")
        select_overlay_list = self.cursor.fetchall()

        for select_overlay in select_overlay_list:
            overlay_id = select_overlay.get('overlay_id')
            overlay = Overlay()
            overlay.overlay_id = overlay_id
            overlay.expires = select_overlay.get('expires')
            overlay.heartbeat_interval = select_overlay.get('heartbeat_interval')
            overlay.heartbeat_timeout = select_overlay.get('heartbeat_timeout')

            self.cursor.execute("SELECT * FROM hp2p_peer WHERE overlay_id = %s ORDER BY ticket_id", (overlay_id,))
            select_peer_list = self.cursor.fetchall()

            for select_peer in select_peer_list:
                ticket_id = select_peer.get('ticket_id')
                peer_id = select_peer.get('peer_id')
                overlay.current_ticket_id = ticket_id

                peer = Peer()
                peer.overlay_id = overlay_id
                peer.expires = select_peer.get('expires')
                peer.peer_id = peer_id
                peer.ticket_id = ticket_id
                peer.update_time = datetime.now()
                if select_peer.get('costmap') is not None:
                    peer.costmap = json.loads(select_peer.get('costmap'))
                overlay.add_peer(peer_id, peer)

            Service.get().set_overlay(overlay_id, overlay)

    def init_public_data(self):
        try:
            is_execute = False
            self.cursor.execute("show databases like %s", (self.database_name,))
            database = self.cursor.fetchone()
            if database is None:
                is_execute = True
                self.cursor.execute("CREATE DATABASE IF NOT EXISTS {0}".format(self.database_name))
                print("[DBManager] CREATE DATABASE...", flush=True)

            self.cursor.execute("USE {0}".format(self.database_name))

            self.cursor.execute("show tables like 'public_data'")
            hp2p_overlay = self.cursor.fetchone()
            if hp2p_overlay is None:
                is_execute = True
                self.cursor.execute("CREATE TABLE IF NOT EXISTS public_data ( "
                                    "data_time DATETIME NOT NULL, "
                                    "pm10_data LONGTEXT NOT NULL COLLATE utf8_unicode_ci, "
                                    "updated_at DATETIME NOT NULL,  "
                                    " PRIMARY KEY (`data_time`)"
                                    ")")
                print("[DBManager] CREATE TABLE public_data", flush=True)

            if is_execute:
                self.connect.commit()
        except Exception as e:
            print(e)
            self.connect.rollback()
            return False
