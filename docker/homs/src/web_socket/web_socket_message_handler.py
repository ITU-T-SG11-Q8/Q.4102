import json

from config import LOG_CONFIG
from classes.overlay import Overlay
from classes.peer import Peer


class WebSocketMessageHandler:
    def __init__(self):
        self._web_socket_peer_dict = {}
        self._web_socket_client_list = []

    def add_web_socket_peer(self, peer_id, client):
        if client not in self._web_socket_peer_dict:
            print('[WebSocketMessageSender] Add Peer =>', peer_id)
            self._web_socket_peer_dict[peer_id] = client

    def delete_web_socket_peer(self, client):
        remove_peer_id = None
        for peer_id in self._web_socket_peer_dict.keys():
            connection = self._web_socket_peer_dict[peer_id]
            if connection == client:
                remove_peer_id = peer_id
                break

        if remove_peer_id is not None:
            print('[WebSocketMessageSender] Remove Peer =>', remove_peer_id)
            del self._web_socket_peer_dict[remove_peer_id]

    def send_message_to_peer(self, peer_id, message):
        if peer_id in self._web_socket_peer_dict:
            connection = self._web_socket_peer_dict[peer_id]
            connection.send_message(json.dumps(message))
            return True
        else:
            return False

    def append_web_socket_client(self, client):
        if client not in self._web_socket_client_list:
            print('[WebSocketMessageSender] Append Client =>', client.address)
            self._web_socket_client_list.append(client)

    def remove_web_socket_client(self, client):
        if client in self._web_socket_client_list:
            print('[WebSocketMessageSender] Remove Client =>', client.address)
            self._web_socket_client_list.remove(client)

    def send_message_to_client(self, message):
        for client in self._web_socket_client_list:
            client.send_message(json.dumps(message))

    def send_create_overlay_message(self, overlay_id):
        self.send_message_to_client({"overlay_id": overlay_id, "type": "overlay", "action": "create"})

    def send_remove_overlay_message(self, overlay_id):
        self.send_message_to_client({"overlay_id": overlay_id, "type": "overlay", "action": "remove"})

    def send_add_peer_message(self, overlay_id, peer_id, ticket_id):
        message = self.create_add_node_message(overlay_id, peer_id, ticket_id)
        if message is not None:
            self.send_message_to_client(message)

    def send_delete_peer_message(self, overlay_id, peer_id):
        message = self.create_delete_node_message(overlay_id, peer_id)
        if message is not None:
            self.send_message_to_client(message)

    def send_update_peer_message(self, overlay_id, costmap):
        message = self.create_update_link_message(overlay_id, costmap)
        if message is not None:
            self.send_message_to_client(message)

    def send_log_message(self, overlay_id, peer_id, messsage):
        if LOG_CONFIG['PRINT_PROTOCOL_LOG']:
            message = self.create_log_message(overlay_id, peer_id, messsage)
            if message is not None:
                self.send_message_to_client(message)

    @classmethod
    def create_overlay_cost_map_message(cls, overlay: Overlay):
        get_peer_dic = overlay.get_peer_dict()

        nodes = []
        links = []
        for item in get_peer_dic.values():
            peer: Peer = item
            node = {"id": peer.peer_id, "ticket_id": peer.ticket_id}
            if peer.ticket_id == 1:
                node["seeder"] = True
            nodes.append(node)
            costmap = peer.costmap.get('costmap')

            if costmap is not None and costmap.get('primary') is not None and costmap.get(
                    'outgoing_candidate') is not None:
                for p_item in peer.costmap.get('costmap').get('primary'):
                    link = {"source": peer.peer_id, "target": p_item, "primary": True}
                    reverse_link = {"source": p_item, "target": peer.peer_id, "primary": True}

                    if link not in links and reverse_link not in links:
                        links.append(link)

                for c_item in peer.costmap.get('costmap').get('outgoing_candidate'):
                    links.append({"source": peer.peer_id, "target": c_item, "primary": False})

        return {
            "overlay_id": overlay.overlay_id,
            "type": "peer",
            "action": "current_cost_map",
            "data": {
                "graph": [],
                "nodes": nodes,
                "links": links,
                "directed": False,
                "multigraph": True
            }
        }

    @classmethod
    def create_add_node_message(cls, overlay_id, peer_id, ticket_id):
        return {
            "overlay_id": overlay_id,
            "type": "peer",
            "action": "add_peer",
            "node": {
                "id": peer_id,
                "ticket_id": ticket_id
            }
        }

    @classmethod
    def create_delete_node_message(cls, overlay_id, peer_id):
        return {
            "overlay_id": overlay_id,
            "peer_id": peer_id,
            "type": "peer",
            "action": "delete_peer"
        }

    @classmethod
    def create_update_link_message(cls, overlay_id, costmap):
        peer_id = costmap.get('peer_id')
        costmap_dict = costmap.get('costmap')

        links = []

        if costmap_dict is not None and costmap_dict.get('primary') is not None and costmap_dict.get(
                'outgoing_candidate') is not None:
            for p_item in costmap_dict.get('primary'):
                links.append({"source": peer_id, "target": p_item, "primary": True})

            for c_item in costmap_dict.get('outgoing_candidate'):
                links.append({"source": peer_id, "target": c_item, "primary": False})

        if len(links) < 1:
            return None
        else:
            return {
                "overlay_id": overlay_id,
                "peer_id": peer_id,
                "type": "peer",
                "action": "update_connection",
                "links": links
            }

    @classmethod
    def create_log_message(cls, overlay_id, peer_id, message):
        return {
            "overlay_id": overlay_id,
            "peer_id": peer_id,
            "type": "log",
            "message": message
        }
