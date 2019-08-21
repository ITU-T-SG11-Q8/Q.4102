import requests
from core.factory import Factor
from core.classes import RequestPath


class Hp2pCore:
    def __init__(self, peer_id):
        print("[CORE] __init__", flush=True)
        self.isJoinOverlay = False
        self.path = RequestPath
        self.properties = Factor.instance().properties
        self.peer_id = peer_id
        self.peer_index = -1
        self.overlay_id = None
        self.admin_key = None
        self.address = None

    def __del__(self):
        print("[CORE] __del__", flush=True)

    def query(self):
        try:
            overlay_query_url = self.properties.toms_url + self.path.OverlayQuery
            response = requests.get(overlay_query_url)
            if response.status_code == 200:
                result_data = response.json()
                print("[CORE] Query: ", flush=True)
                for data in result_data:
                    print("\t\t\t[Overlay]: ", data, flush=True)
            else:
                print("[CORE] Error...", response.text, flush=True)

        except Exception as e:
            print('[CORE] Error\n', e, flush=True)

    def creation(self, title, description, admin_key):
        print("[CORE] Call Creation", flush=True)
        try:
            self.admin_key = admin_key
            overlay_creation_url = self.properties.toms_url + self.path.OverlayCreation

            data = {
                "title": title,
                "type": self.properties.type,
                "sub_type": self.properties.sub_type,
                "owner_id": self.peer_id,
                "description": description,
                "auth": {
                    "type": self.properties.auth_type,
                    "admin_key": self.admin_key
                }
            }

            response = requests.post(overlay_creation_url, json=data)
            if response.status_code == 200:
                result_data = response.json()
                self.overlay_id = result_data.get('overlay_id')

                print("[CORE] Creation...", result_data, flush=True)
                print("\t\t\tOVERLAY ID: ", self.overlay_id, flush=True)
            else:
                print("[CORE] Error...", response.text, flush=True)

        except Exception as e:
            print('[CORE] Error\n', e, flush=True)

    def removal(self):
        if self.admin_key is not None:
            print("[CORE] Call Removal", flush=True)
            try:
                overlay_removal_url = self.properties.toms_url + self.path.OverlayRemoval

                data = {
                    "overlay_id": self.overlay_id,
                    "owner_id": self.peer_id,
                    "auth": {
                        "admin_key": self.admin_key
                    }
                }

                response = requests.delete(overlay_removal_url, json=data)
                if response.status_code == 200:
                    result_data = response.json()

                    print("[CORE] Removal...", result_data.get('overlay_id'), flush=True)
                    print("\t\t\tOVERLAY ID: ", self.overlay_id, flush=True)
                else:
                    print("[CORE] Error...", response.text, flush=True)

            except Exception as e:
                print('[CORE] Error\n', e, flush=True)

    def join(self, overlay_id):
        if not self.isJoinOverlay:
            print("[CORE] Call Join", flush=True)

            if overlay_id is not None:
                self.overlay_id = overlay_id

            try:
                overlay_join_url = self.properties.toms_url + self.path.OverlayJoin
                data = {
                    "overlay_id": self.overlay_id,
                    "type": self.properties.type,
                    "sub_type": self.properties.sub_type,
                    "expires": self.properties.expires,
                    "peer_info": {
                        "peer_id": self.peer_id,
                        "address": self.address
                    }
                }

                response = requests.post(overlay_join_url, json=data)
                if response.status_code == 200 or response.status_code == 202:
                    self.isJoinOverlay = True
                    result_data = response.json()
                    overlay_status = result_data.get('status')
                    self.peer_index = overlay_status.get('peer_index')
                    peer_info_list = overlay_status.get('peer_info_list')

                    print("[CORE] Join Overlay: ", result_data.get('overlay_id'), flush=True)
                    print("\t\t\tPeer Index: ", self.peer_index, flush=True)
                    return peer_info_list
                elif response.status_code == 407:
                    print("[CORE] Auth Req...", response.text, flush=True)
                    return None
                else:
                    print("[CORE] Error...", response.text, flush=True)
                    return None

            except Exception as e:
                print('[CORE] Error\n', e, flush=True)
                return None

    def leave(self):
        if self.isJoinOverlay:
            print("[CORE] Call Leave", flush=True)
            try:
                overlay_leave_url = self.properties.toms_url + self.path.OverlayLeave
                data = {
                    "overlay_id": self.overlay_id,
                    "type": self.properties.type,
                    "sub_type": self.properties.sub_type,
                    "peer_info": {
                        "peer_id": self.peer_id,
                    }
                }

                response = requests.delete(overlay_leave_url, json=data)
                if response.status_code == 200:
                    result_data = response.json()
                    self.isJoinOverlay = False
                    print("[CORE] leave...", result_data.get('overlay_id'), flush=True)
                else:
                    print("[CORE] Error...", response.text, flush=True)

            except Exception as e:
                print('[CORE] Error\n', e, flush=True)

    def refresh(self):
        if self.isJoinOverlay:
            print("[CORE] Call Refresh", flush=True)
            try:
                overlay_leave_url = self.properties.toms_url + self.path.OverlayRefresh
                data = {
                    "overlay_id": self.overlay_id,
                    "expires": self.properties.expires,
                    "peer_info": {
                        "peer_id": self.peer_id,
                        "address": self.address
                    }
                }

                response = requests.put(overlay_leave_url, json=data)
                if response.status_code == 200:
                    result_data = response.json()
                    overlay_id = result_data.get('overlay_id')
                    expires = result_data.get('expires')
                    print("[CORE] Refresh...", overlay_id, expires, flush=True)
                else:
                    print("[CORE] Error...", response.text, flush=True)

            except Exception as e:
                print('[CORE] Error\n', e, flush=True)

    def report(self, max_capacity, primary_list, out_candidate_list, in_candidate_list):
        if self.isJoinOverlay:
            print("[CORE] Call Report", flush=True)
            try:
                overlay_leave_url = self.properties.toms_url + self.path.OverlayReport
                data = {
                    "overlay_id": self.overlay_id,
                    "peer_status": {
                        "max_capa": max_capacity,
                        "num_primary": len(primary_list),
                        "num_out_candidate": len(out_candidate_list),
                        "num_in_candidate": len(in_candidate_list),
                        "costmap": {
                            "peer_id": self.peer_id,
                            "costmap": {
                                "primary": primary_list,
                                "outgoing_candidate": out_candidate_list,
                                "incoming_candidate": in_candidate_list
                            }
                        }
                    }
                }

                response = requests.put(overlay_leave_url, json=data)
                if response.status_code == 200:
                    result_data = response.json()
                    overlay_id = result_data.get('overlay_id')
                    print("[CORE] Report...", overlay_id, flush=True)
                else:
                    print("[CORE] Error...", response.text, flush=True)

            except Exception as e:
                print('[CORE] Error\n', e, flush=True)
