import uuid
from datetime import datetime
from flask import request
from flask_restful import Resource

from config import HOMS_CONFIG, WEB_SOCKET_CONFIG, LOG_CONFIG
from classes.overlay import Overlay
from data.factory import Factory
from database.db_connector import DBConnector


class HybridOverlayCreation(Resource):
    def post(self):
        if LOG_CONFIG['PRINT_PROTOCOL_LOG']:
            print("[SERVER] {0} / {1}".format(self.methods, self.endpoint))
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = str(uuid.uuid4())
            title = request_data.get('title')
            overlay_type = request_data.get('type')
            sub_type = request_data.get('sub_type')
            owner_id = request_data.get('owner_id')
            expires = request_data.get('expires') if 'expires' in request_data else HOMS_CONFIG['OVERLAY_EXPIRES']
            description = request_data.get('description')
            heartbeat_interval = request_data.get('heartbeat_interval')
            heartbeat_timeout = request_data.get('heartbeat_timeout')
            overlay_auth = request_data.get('auth')

            if title is None or overlay_type is None or sub_type is None or owner_id is None or description is None or \
                    heartbeat_interval is None or heartbeat_timeout is None or overlay_auth is None:
                raise ValueError

            if overlay_type != 'core' or sub_type != 'tree':
                raise ValueError

            auth_keyword = overlay_auth.get('keyword')
            auth_type = overlay_auth.get('type')
            auth_admin_key = overlay_auth.get('admin_key')
            auth_access_key = None
            auth_peer_list = []
            overlay_status = 'active'

            if auth_type is None or (auth_type != 'closed' and auth_type != 'open') or auth_admin_key is None:
                raise ValueError

            if auth_type == 'closed':
                if 'access_key' in overlay_auth:
                    auth_access_key = overlay_auth.get('access_key')
                elif 'peerlist' in overlay_auth:
                    auth_peer_list = overlay_auth.get('peerlist')

                if auth_access_key is None and len(auth_peer_list) == 0:
                    raise ValueError

            overlay_query = "INSERT INTO hp2p_overlay " \
                            "(overlay_id, title, overlay_type, sub_type, owner_id, expires, overlay_status," \
                            "description, heartbeat_interval, heartbeat_timeout, auth_keyword, auth_type, " \
                            "auth_admin_key, auth_access_key, created_at, updated_at) " \
                            "VALUES " \
                            "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"
            overlay_parameters = (
                overlay_id, title, overlay_type, sub_type, owner_id, expires, overlay_status, description,
                heartbeat_interval, heartbeat_timeout, auth_keyword, auth_type,
                auth_admin_key, auth_access_key)
            db_connector.insert(overlay_query, overlay_parameters)

            if len(auth_peer_list) > 0:
                auth_peer_query = "INSERT INTO hp2p_auth_peer " \
                                  "(overlay_id, peer_id, updated_at) " \
                                  "VALUES " \
                                  "(%s, %s, now())"
                auth_peer_parameters = []
                for peer_id in auth_peer_list:
                    auth_peer = (overlay_id, peer_id)
                    auth_peer_parameters.append(auth_peer)

                db_connector.insert_all(auth_peer_query, auth_peer_parameters)

            result = {
                'overlay_id': overlay_id,
                'type': overlay_type,
                'sub_type': sub_type,
                'owner_id': owner_id,
                'expires': expires,
                'heartbeat_interval': heartbeat_interval,
                'heartbeat_timeout': heartbeat_timeout
            }
            new_overlay = Overlay()
            new_overlay.overlay_id = overlay_id
            new_overlay.expires = expires
            new_overlay.heartbeat_interval = heartbeat_interval
            new_overlay.heartbeat_timeout = heartbeat_timeout

            if expires > 0:
                new_overlay.update_time = datetime.now()

            Factory.get().set_overlay(overlay_id, new_overlay)
            Factory.get().get_web_socket_message_handler().send_create_overlay_message(overlay_id)
            Factory.get().get_web_socket_message_handler().send_log_message(overlay_id, owner_id, "Overlay Creation.")

            db_connector.commit()
            return result, 200
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


class HybridOverlayQuery(Resource):
    def get(self):
        if LOG_CONFIG['PRINT_PROTOCOL_LOG']:
            print("[SERVER] {0} / {1}".format(self.methods, self.endpoint))
        db_connector = DBConnector()
        try:
            query = "SELECT " \
                    "overlay_id, title, overlay_type, sub_type, owner_id, expires, overlay_status, auth_type " \
                    "FROM hp2p_overlay"
            where = None
            parameters = None
            order_by = " ORDER BY created_at"
            result = []

            if len(request.args) > 0:
                if 'overlay_id' in request.args:
                    where = " WHERE overlay_id = %s"
                    parameters = request.args.get('overlay_id')
                elif 'title' in request.args:
                    where = " WHERE title LIKE %s"
                    parameters = ('%%%s%%' % request.args.get('title'))
                elif 'description' in request.args:
                    where = " WHERE description LIKE %s"
                    parameters = ('%%%s%%' % request.args.get('description'))

            if parameters is None or where is None:
                select_overlay_list = db_connector.select(query + order_by)
            else:
                query = query + where + order_by
                select_overlay_list = db_connector.select(query, (parameters,))

            if len(select_overlay_list) > 0:
                for select_overlay in select_overlay_list:
                    overlay_id = select_overlay.get('overlay_id')

                    num_peers_query = "SELECT COUNT(*) AS num_peers FROM hp2p_peer WHERE overlay_id = %s"
                    select_num_peers = db_connector.select_one(num_peers_query, (overlay_id,))
                    num_peers = select_num_peers.get('num_peers') if select_num_peers is not None else 0

                    overlay = {
                        'overlay_id': overlay_id,
                        'title': select_overlay.get('title'),
                        'type': select_overlay.get('overlay_type'),
                        'sub_type': select_overlay.get('sub_type'),
                        'owner_id': select_overlay.get('owner_id'),
                        'expires': select_overlay.get('expires'),
                        'status': {
                            'num_peers': num_peers,
                            'status': select_overlay.get('overlay_status')
                        },
                        'auth': {
                            'type': select_overlay.get('auth_type')
                        }
                    }
                    result.append(overlay)

            return result, 200
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


class HybridOverlayModification(Resource):
    def put(self):
        if LOG_CONFIG['PRINT_PROTOCOL_LOG']:
            print("[SERVER] {0} / {1}".format(self.methods, self.endpoint))
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = request_data.get('overlay_id')
            title = request_data.get('title')
            owner_id = request_data.get('owner_id')
            expires = request_data.get('expires')
            description = request_data.get('description')
            overlay_auth = request_data.get('auth')

            auth_admin_key = overlay_auth.get('admin_key')
            auth_access_key = overlay_auth.get('access_key')
            auth_peer_list = overlay_auth.get('peerlist')

            if overlay_id is None or owner_id is None or auth_admin_key is None:
                raise ValueError

            query = "SELECT " \
                    "overlay_id, auth_access_key " \
                    "FROM hp2p_overlay " \
                    "WHERE overlay_id = %s AND owner_id = %s AND auth_admin_key = %s"
            select_overlay = db_connector.select_one(query, (overlay_id, owner_id, auth_admin_key))

            if select_overlay is None:
                raise ValueError

            update_query = "UPDATE hp2p_overlay SET updated_at = now()"
            set_query = ""
            where = " WHERE overlay_id = %s"
            parameters = []

            if title is not None:
                set_query += ", title = %s"
                parameters.append(title)
            if expires is not None:
                set_query += ", expires = %s"
                parameters.append(expires)
            if description is not None:
                set_query += ", description = %s"
                parameters.append(description)

            parameters.append(overlay_id)
            update_query = update_query + set_query + where
            db_connector.update(update_query, parameters)

            if auth_access_key is not None or (auth_peer_list is not None and len(auth_peer_list) > 0):
                db_connector.delete("DELETE FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))
                update_access_key_query = "UPDATE hp2p_overlay SET auth_access_key = %s WHERE overlay_id = %s"
                db_connector.update(update_access_key_query, (auth_access_key, overlay_id))

                if auth_access_key is None:
                    auth_peer_query = "INSERT INTO hp2p_auth_peer " \
                                      "(overlay_id, peer_id, updated_at) " \
                                      "VALUES " \
                                      "(%s, %s, now())"
                    auth_peer_list_parameters = []
                    for peer_id in auth_peer_list:
                        auth_peer_list_parameters.append((overlay_id, peer_id))

                    db_connector.insert_all(auth_peer_query, auth_peer_list_parameters)

            auth_peer_list = []
            select_auth_peer_list = db_connector.select(
                "SELECT peer_id FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))

            for select_auth_peer in select_auth_peer_list:
                if 'peer_id' in select_auth_peer:
                    auth_peer_list.append(select_auth_peer.get('peer_id'))

            auth_access_key_query = "SELECT auth_access_key FROM hp2p_overlay WHERE overlay_id = %s"
            select_auth_access_key = db_connector.select_one(auth_access_key_query, (overlay_id,))

            result = {
                'overlay_id': overlay_id,
                'title': title,
                'owner_id': owner_id,
                'expires': expires,
                'description': description,
                'auth': {
                    'access_key': select_auth_access_key.get('auth_access_key'),
                    'peerlist': auth_peer_list
                }
            }

            if title is None:
                del result['title']

            if expires is None:
                del result['expires']

            if description is None:
                del result['description']

            get_overlay: Overlay = Factory.get().get_overlay(overlay_id)
            if expires is not None:
                get_overlay.expires = expires

            if get_overlay.expires > 0:
                get_overlay.update_time = datetime.now()

            Factory.get().get_web_socket_message_handler().send_log_message(overlay_id, owner_id,
                                                                            "Overlay Modification.")
            db_connector.commit()
            return result, 200
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


class HybridOverlayRemoval(Resource):
    def delete(self):
        if LOG_CONFIG['PRINT_PROTOCOL_LOG']:
            print("[SERVER] {0} / {1}".format(self.methods, self.endpoint))
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = request_data.get('overlay_id')
            owner_id = request_data.get('owner_id')
            auth_admin_key = request_data.get('auth').get('admin_key')

            if overlay_id is None or owner_id is None or auth_admin_key is None:
                raise ValueError

            query = "SELECT " \
                    "overlay_id, expires, overlay_status, auth_type " \
                    "FROM hp2p_overlay " \
                    "WHERE overlay_id = %s AND owner_id = %s AND auth_admin_key = %s"
            select_overlay = db_connector.select_one(query, (overlay_id, owner_id, auth_admin_key))

            if select_overlay is None:
                raise ValueError

            db_connector.delete("DELETE FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))
            db_connector.delete("DELETE FROM hp2p_peer WHERE overlay_id = %s", (overlay_id,))
            db_connector.delete("DELETE FROM hp2p_overlay WHERE overlay_id = %s", (overlay_id,))

            Factory.get().delete_overlay(overlay_id)
            Factory.get().get_web_socket_message_handler().send_remove_overlay_message(overlay_id)
            Factory.get().get_web_socket_message_handler().send_log_message(overlay_id, owner_id, "Overlay Removal.")

            result = {
                'overlay_id': overlay_id
            }
            db_connector.commit()
            return result, 200
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


class ApiHybridOverlayRemoval(Resource):
    def post(self):
        print("[SERVER] {0} / {1}".format(self.methods, self.endpoint))
        db_connector = DBConnector()
        try:
            request_data = request.get_json()
            overlay_id = request_data.get('overlay_id')

            if overlay_id is None:
                raise ValueError

            query = "SELECT " \
                    "overlay_id, expires, overlay_status, auth_type " \
                    "FROM hp2p_overlay " \
                    "WHERE overlay_id = %s"
            select_overlay = db_connector.select_one(query, (overlay_id,))

            if select_overlay is None:
                raise ValueError

            db_connector.delete("DELETE FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))
            db_connector.delete("DELETE FROM hp2p_peer WHERE overlay_id = %s", (overlay_id,))
            db_connector.delete("DELETE FROM hp2p_overlay WHERE overlay_id = %s", (overlay_id,))

            Factory.get().delete_overlay(overlay_id)
            Factory.get().get_web_socket_message_handler().send_remove_overlay_message(overlay_id)
            Factory.get().get_web_socket_message_handler().send_log_message(overlay_id, "Administrator",
                                                                            "Overlay Removal.")

            result = {
                'overlay_id': overlay_id
            }
            db_connector.commit()
            return result, 200
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


class GetInitData(Resource):
    def get(self):
        print("[SERVER] {0} / {1}".format(self.methods, self.endpoint))
        result = {
            'WEB_SOCKET_PORT': WEB_SOCKET_CONFIG['PORT']
        }
        return result, 200


class GetOverlayCostMap(Resource):
    def get(self):
        print("[SERVER] {0} / {1}".format(self.methods, self.endpoint))
        if len(request.args) > 0 and 'overlay_id' in request.args:
            overlay = Factory.get().get_overlay(request.args.get('overlay_id'))
            message = Factory.get().get_web_socket_message_handler().create_overlay_cost_map_message(overlay)
            return message, 200
        else:
            return None, 404
