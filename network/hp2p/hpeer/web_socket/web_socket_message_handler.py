import json


class WebSocketMessageHandler:
    def __init__(self):
        self._web_socket_server = None

    def get_web_socket_server(self):
        return self._web_socket_server

    def set_web_socket_server(self, server):
        self._web_socket_server = server

    def _send_message_to_client(self, message):
        for desc, client in self._web_socket_server.connections.items():
            client.send_message(json.dumps(message))

    def send_creation(self, overlay_id):
        send_message = {
            "type": "creation",
            "overlayId": overlay_id,
        }
        self._send_message_to_client(send_message)

    def send_received_data(self, sender, source, received_data):
        send_message = {
            "type": "received_data",
            "sender": sender,
            "source": source,
            "message": received_data
        }
        self._send_message_to_client(send_message)

    def send_connection_change(self, has_connection):
        send_message = {
            "type": "connection_change",
            "hasConnection": has_connection
        }
        self._send_message_to_client(send_message)

    def send_scan_tree_path(self, path):
        send_message = {
            "type": "scan_tree",
            "data": path
        }
        self._send_message_to_client(send_message)

    def send_overlay_costmap(self, costmap):
        send_message = {
            "type": "overlay_costmap",
            "data": costmap
        }
        self._send_message_to_client(send_message)

    def send_log_message(self, message):
        send_message = {
            "type": "log",
            "message": message
        }
        self._send_message_to_client(send_message)

    def send_public_data(self, data):
        send_message = {
            "type": "public_data",
            "data": data
        }
        self._send_message_to_client(send_message)
