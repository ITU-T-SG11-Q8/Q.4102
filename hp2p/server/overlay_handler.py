from flask import request
from flask_restful import Resource
from server.db_connector import DBConnector
from server.factory import Factory
from server.classes import Overlay
import uuid


class HybridOverlayCreation(Resource):
    def post(self):
        print("[SERVER] Call HybridOverlayCreation", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = str(uuid.uuid4())
            title = request_data.get('title')
            overlay_type = request_data.get('type')
            sub_type = request_data.get('sub_type')
            owner_id = request_data.get('owner_id')
            description = request_data.get('description')
            # TODO => OVERLAY expires 관리-추가
            expires = request_data.get('expires') if 'expires' in request_data else 0

            if overlay_id is None or title is None or overlay_type is None or sub_type is None or owner_id is None or description is None:
                raise ValueError

            overlay_auth = request_data.get('auth')
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
                if 'peerlist' in overlay_auth:
                    auth_peer_list = overlay_auth.get('peerlist')

                if auth_access_key is None and len(auth_peer_list) == 0:
                    raise ValueError

            overlay_query = "INSERT INTO hp2p_overlay " \
                            "(overlay_id, title, overlay_type, sub_type, owner_id, expires, overlay_status," \
                            "description, auth_type, auth_admin_key, auth_access_key, created_at, updated_at) " \
                            "VALUES " \
                            "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"
            overlay_parameters = (
                overlay_id, title, overlay_type, sub_type, owner_id, expires, overlay_status, description, auth_type,
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
                'expires': expires
            }
            Factory.instance().set_overlay(overlay_id, Overlay(overlay_id))

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
        print("[SERVER] Call HybridOverlayQuery", flush=True)
        db_connector = DBConnector()
        try:
            query = "SELECT " \
                    "overlay_id, title, overlay_type, sub_type, owner_id, expires, overlay_status, auth_type " \
                    "FROM hp2p_overlay"
            where = None
            parameters = None
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
                select_overlay_list = db_connector.select(query)
            else:
                query += where
                select_overlay_list = db_connector.select(query, (parameters,))

            if len(select_overlay_list) > 0:
                for select_overlay in select_overlay_list:
                    overlay_id = select_overlay.get('overlay_id')

                    num_peers_query = "select count(*) as num_peers from hp2p_peer where overlay_id = %s"
                    select_num_peers = db_connector.select_one(num_peers_query, (overlay_id,))
                    num_peers = select_num_peers.get('num_peers') if select_num_peers is not None else 0

                    select_peers_info_query = "SELECT peer_id,address FROM " \
                                              "(SELECT peer_id , overlay_id , peer_index, address, " \
                                              "(max_capa - num_primary - num_out_candidate - num_in_candidate) " \
                                              "as capa FROM hp2p_peer WHERE overlay_id = %s) AS t_capa " \
                                              "WHERE capa > 0 ORDER BY capa DESC , peer_index ASC LIMIT 5"
                    peer_info_list = db_connector.select(select_peers_info_query, (overlay_id,))

                    overlay = {
                        'overlay_id': overlay_id,
                        'title': select_overlay.get('title'),
                        'type': select_overlay.get('overlay_type'),
                        'sub_type': select_overlay.get('sub_type'),
                        'owner_id': select_overlay.get('owner_id'),
                        'expires': select_overlay.get('expires'),
                        'status': {
                            'num_peers': num_peers,
                            'peer_info_list': peer_info_list,
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
        print("[SERVER] Call HybridOverlayModification", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = request_data.get('overlay_id')
            owner_id = request_data.get('owner_id')
            auth_data = request_data.get('auth')
            auth_admin_key = auth_data.get('admin_key')

            title = request_data.get('title')
            # TODO => OVERLAY expires 관리-갱신
            expires = request_data.get('expires')
            description = request_data.get('description')
            auth_access_key = auth_data.get('access_key')
            auth_peer_list = auth_data.get('peerlist')

            if overlay_id is None or owner_id is None or auth_admin_key is None:
                raise ValueError

            query = "SELECT " \
                    "overlay_id, auth_access_key " \
                    "FROM hp2p_overlay " \
                    "WHERE overlay_id = %s AND owner_id = %s AND auth_admin_key = %s"
            select_overlay = db_connector.select_one(query, (overlay_id, owner_id, auth_admin_key))

            if select_overlay is None:
                raise ValueError

            update_query = "UPDATE hp2p_overlay SET"
            set_query = ""
            where = " WHERE overlay_id = %s"
            parameters = []

            if title is not None:
                set_query += " title = %s"
                parameters.append(title)
            if expires is not None:
                if len(set_query) > 0:
                    set_query += " ,"
                set_query += " expires = %s"
                parameters.append(expires)
            if description is not None:
                if len(set_query) > 0:
                    set_query += " ,"
                set_query += " description = %s"
                parameters.append(description)
            if auth_access_key is not None:
                if len(set_query) > 0:
                    set_query += " ,"
                set_query += " auth_access_key = %s"
                parameters.append(auth_access_key)

            if len(parameters) > 0 and len(set_query) > 0:
                parameters.append(overlay_id)
                update_query = update_query + set_query + where
                db_connector.update(update_query, parameters)

            if auth_peer_list is not None and len(auth_peer_list) > 0:
                db_connector.delete("DELETE FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))

                auth_peer_query = "INSERT INTO hp2p_auth_peer " \
                                  "(overlay_id, peer_id, updated_at) " \
                                  "VALUES " \
                                  "(%s, %s, now())"

                auth_peer_parameters = []
                for peer_id in auth_peer_list:
                    auth_peer = (overlay_id, peer_id)
                    auth_peer_parameters.append(auth_peer)

                db_connector.insert_all(auth_peer_query, auth_peer_parameters)
            else:
                auth_peer_list = []
                select_auth_peer_list = db_connector.select(
                    "SELECT peer_id FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))

                for peer_id in select_auth_peer_list:
                    auth_peer_list.append(peer_id)

            if auth_access_key is None:
                auth_access_key = select_overlay.get('auth_access_key')

            result = {
                'overlay_id': overlay_id,
                'title': title,
                'owner_id': owner_id,
                'expires': expires,
                'description': description,
                'auth': {
                    'access_key': auth_access_key,
                    'peerlist': auth_peer_list
                }
            }

            if title is None:
                del result['title']

            if expires is None:
                del result['expires']

            if description is None:
                del result['description']

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
        print("[SERVER] Call HybridOverlayRemoval", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            # TODO => OVERLAY expires 관리-삭제
            overlay_id = request_data.get('overlay_id')
            owner_id = request_data.get('owner_id')
            auth_admin_key = request_data.get('auth').get('admin_key')
            overlay_status = 'terminated'

            if overlay_id is None or owner_id is None or auth_admin_key is None:
                raise ValueError

            query = "SELECT " \
                    "overlay_id, expires, overlay_status, auth_type " \
                    "FROM hp2p_overlay " \
                    "WHERE overlay_id = %s AND owner_id = %s AND auth_admin_key = %s"
            select_overlay = db_connector.select_one(query, (overlay_id, owner_id, auth_admin_key))

            if select_overlay is None:
                raise ValueError

            db_connector.delete("DELETE FROM hp2p_overlay WHERE overlay_id = %s", (overlay_id,))
            db_connector.delete("DELETE FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))
            db_connector.delete("DELETE FROM hp2p_peer WHERE overlay_id = %s", (overlay_id,))

            result = {
                'overlay_id': overlay_id,
                'status': {
                    'status': overlay_status
                }
            }
            Factory.instance().delete_overlay(overlay_id)

            db_connector.commit()
            return result, 200
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500
