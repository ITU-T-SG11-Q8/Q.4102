import requests
from data.factory import Peer
from config import CLIENT_CONFIG
from classes.constants import RequestPath


class HompMessageHandler:
    def __init__(self):
        self._toms_url = CLIENT_CONFIG['HOMS_URL']
        print("=======[HompHandler] __init__", flush=True)

    def __del__(self):
        print("=======[HompHandler] __del__", flush=True)

    def creation(self, peer: Peer):
        print("=======[HompHandler] Call Creation", flush=True)
        try:
            data = {
                "title": peer.title,
                "type": peer.type,
                "sub_type": peer.sub_type,
                "owner_id": peer.peer_id,
                "expires": peer.overlay_expires,
                "description": peer.description,
                "heartbeat_interval": peer.heartbeat_interval,
                "heartbeat_timeout": peer.heartbeat_timeout,
                "auth": {
                    "type": peer.auth_type,
                    "admin_key": peer.admin_key,
                    "access_key": peer.auth_access_key
                }
            }
            response = requests.post(self._toms_url + RequestPath.OverlayCreation, json=data)
            if response.status_code == 200:
                result_data = response.json()
                peer.overlay_id = result_data.get('overlay_id')
                peer.isOwner = True
                print("=======[HompHandler] Creation...", result_data, flush=True)
                print("\t\tOVERLAY ID: ", peer.overlay_id, flush=True)
            else:
                print("=======[HompHandler] Error...", response.text, flush=True)

        except Exception as e:
            print('=======[HompHandler] Error\n', e, flush=True)

    def query(self):
        result_data = None
        try:
            response = requests.get(self._toms_url + RequestPath.OverlayQuery)
            if response.status_code == 200:
                result_data = response.json()
                print("=======[HompHandler] Query...", flush=True)
            else:
                print("=======[HompHandler] Error...", response.text, flush=True)
        except Exception as e:
            result_data = None
            print('=======[HompHandler] Error\n', e, flush=True)

        return result_data

    def modification(self, peer: Peer):
        if peer.isOwner:
            print("=======[HompHandler] Call Modification", flush=True)
            try:
                data = {
                    "overlay_id": peer.overlay_id,
                    "title": peer.title,
                    "owner_id": peer.peer_id,
                    "expires": peer.overlay_expires,
                    "description": peer.description,
                    "auth": {
                        "admin_key": peer.admin_key,
                        "access_key": peer.auth_access_key,
                    }
                }
                response = requests.put(self._toms_url + RequestPath.OverlayModification, json=data)
                if response.status_code == 200:
                    result_data = response.json()
                    print("=======[HompHandler] Modification...", result_data.get('overlay_id'), flush=True)
                else:
                    print("=======[HompHandler] Error...", response.text, flush=True)

            except Exception as e:
                print('=======[HompHandler] Error\n', e, flush=True)

    def removal(self, peer: Peer):
        if peer.isOwner:
            print("=======[HompHandler] Call Removal", flush=True)
            try:
                data = {
                    "overlay_id": peer.overlay_id,
                    "owner_id": peer.peer_id,
                    "auth": {
                        "admin_key": peer.admin_key
                    }
                }
                response = requests.delete(self._toms_url + RequestPath.OverlayRemoval, json=data)
                if response.status_code == 200:
                    result_data = response.json()
                    peer.isOwner = False
                    peer.overlay_id = None
                    print("=======[HompHandler] Removal...", result_data.get('overlay_id'), flush=True)
                else:
                    print("=======[HompHandler] Error...", response.text, flush=True)

            except Exception as e:
                print('=======[HompHandler] Error\n', e, flush=True)

    def join(self, peer: Peer):
        if not peer.isJoinOverlay:
            print("=======[HompHandler] Call Join", flush=True)
            try:
                data = {
                    "overlay_id": peer.overlay_id,
                    "type": peer.type,
                    "sub_type": peer.sub_type,
                    "expires": peer.peer_expires,
                    "auth": {
                        "access_key": peer.auth_access_key
                    },
                    "peer_info": {
                        "peer_id": peer.peer_id,
                        "address": peer.get_address(),
                        "auth": {
                            "password": peer.auth_password
                        }
                    }
                }
                response = requests.post(self._toms_url + RequestPath.OverlayJoin, json=data)
                if response.status_code == 200 or response.status_code == 202:
                    peer.isJoinOverlay = True

                    result_data = response.json()
                    peer.peer_expires = result_data.get('expires')
                    peer.ticket_id = result_data.get('ticket_id')
                    peer.heartbeat_interval = result_data.get('heartbeat_interval')
                    peer.heartbeat_timeout = result_data.get('heartbeat_timeout')
                    overlay_status = result_data.get('status')

                    print("=======[HompHandler] Join Overlay: ", result_data.get('overlay_id'), flush=True)
                    print("\t\t\tPeer Index: ", peer.ticket_id, flush=True)

                    return overlay_status.get('peer_info_list')
                elif response.status_code == 407:
                    print("=======[HompHandler] Auth Req...", response.text, flush=True)
                    return None
                else:
                    print("=======[HompHandler] Error...", response.text, flush=True)
                    return None

            except Exception as e:
                print('=======[HompHandler] Error\n', e, flush=True)
                return None

    def recovery(self, peer: Peer):
        if peer.isJoinOverlay:
            print("=======[HompHandler] Call Recovery", flush=True)
            try:
                data = {
                    "overlay_id": peer.overlay_id,
                    "type": peer.type,
                    "sub_type": peer.sub_type,
                    "auth": {
                        "access_key": peer.auth_access_key
                    },
                    "recovery": True,
                    "ticket_id": peer.ticket_id,
                    "peer_info": {
                        "peer_id": peer.peer_id,
                        "address": peer.get_address(),
                        "auth": {
                            "password": peer.auth_password
                        }
                    }
                }
                response = requests.post(self._toms_url + RequestPath.OverlayJoin, json=data)
                if response.status_code == 200 or response.status_code == 202:
                    result_data = response.json()
                    overlay_status = result_data.get('status')
                    print("=======[HompHandler] Recovery Overlay: ", result_data.get('overlay_id'), flush=True)
                    return overlay_status.get('peer_info_list')
                elif response.status_code == 407:
                    print("=======[HompHandler] Recovery Auth Req...", response.text, flush=True)
                    return None
                else:
                    print("=======[HompHandler] Error...", response.text, flush=True)
                    return None

            except Exception as e:
                print('=======[HompHandler] Error\n', e, flush=True)
                return None

    def report(self, peer: Peer, peer_manager):
        if peer.isJoinOverlay:
            print("=======[HompHandler] Call Report", flush=True)
            try:
                overlay_leave_url = self._toms_url + RequestPath.OverlayReport
                data = {
                    "overlay_id": peer.overlay_id,
                    "status": {
                        "num_primary": len(peer_manager.primary_list),
                        "num_out_candidate": len(peer_manager.out_candidate_list),
                        "num_in_candidate": len(peer_manager.in_candidate_list),
                        "costmap": {
                            "peer_id": peer.peer_id,
                            "costmap": {
                                "primary": peer_manager.primary_list,
                                "outgoing_candidate": peer_manager.out_candidate_list,
                                "incoming_candidate": peer_manager.in_candidate_list
                            }
                        }
                    }
                }

                response = requests.put(overlay_leave_url, json=data)
                if response.status_code == 200:
                    result_data = response.json()
                    overlay_id = result_data.get('overlay_id')
                    print("=======[HompHandler] Report...", overlay_id, flush=True)
                else:
                    print("=======[HompHandler] Error...", response.text, flush=True)

            except Exception as e:
                print('=======[HompHandler] Error\n', e, flush=True)

    def refresh(self, peer: Peer):
        if peer.isJoinOverlay:
            print("=======[HompHandler] Call Refresh", flush=True)
            try:
                overlay_leave_url = self._toms_url + RequestPath.OverlayRefresh
                data = {
                    "overlay_id": peer.overlay_id,
                    "auth": {
                        "access_key": peer.auth_access_key
                    },
                    "peer_info": {
                        "peer_id": peer.peer_id,
                        "address": peer.get_address(),
                        "auth": {
                            "password": peer.auth_password
                        }
                    }
                }

                response = requests.put(overlay_leave_url, json=data)
                if response.status_code == 200:
                    result_data = response.json()
                    overlay_id = result_data.get('overlay_id')
                    expires = result_data.get('expires')
                    print("=======[HompHandler] Refresh...", overlay_id, expires, flush=True)
                else:
                    print("=======[HompHandler] Error...", response.text, flush=True)

            except Exception as e:
                print('=======[HompHandler] Error\n', e, flush=True)

    def leave(self, peer: Peer):
        if peer.isJoinOverlay:
            print("=======[HompHandler] Call Leave", flush=True)
            try:
                overlay_leave_url = self._toms_url + RequestPath.OverlayLeave
                data = {
                    "overlay_id": peer.overlay_id,
                    "type": peer.type,
                    "sub_type": peer.sub_type,
                    "peer_info": {
                        "peer_id": peer.peer_id,
                        "auth": {
                            "password": peer.auth_password
                        }
                    }
                }

                response = requests.delete(overlay_leave_url, json=data)
                if response.status_code == 200:
                    result_data = response.json()
                    peer.isJoinOverlay = False
                    peer.ticket_id = -1
                    if not peer.isOwner:
                        peer.overlay_id = None
                    print("=======[HompHandler] leave...", result_data.get('overlay_id'), flush=True)
                else:
                    print("=======[HompHandler] Error...", response.text, flush=True)

            except Exception as e:
                print('=======[HompHandler] Error\n', e, flush=True)
