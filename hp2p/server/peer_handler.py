from flask import request
from flask_restful import Resource
from server.db_connector import DBConnector
from server.factory import Factory
from server.classes import Overlay
import json


class HybridOverlayJoin(Resource):
    def post(self):
        print("[SERVER] Call HybridOverlayJoin", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = request_data.get('overlay_id')
            # TODO => type & sub_type 관계 및 기능, 제약조건
            overlay_type = request_data.get('type')
            sub_type = request_data.get('sub_type')
            # TODO => PEER expires 관리-추가
            expires = request_data.get('expires') if 'expires' in request_data else 3600
            auth_access_key = request_data.get('auth').get('access_key') if request_data.get(
                'auth') is not None else None
            peer_info_data = request_data.get('peer_info') if 'peer_info' in request_data else {}
            peer_id = peer_info_data.get('peer_id')
            peer_address = peer_info_data.get('address')

            if overlay_id is None or overlay_type is None or sub_type is None or peer_id is None or peer_address is None:
                raise ValueError

            query = "SELECT " \
                    "overlay_id, overlay_type, sub_type, overlay_status, auth_type, auth_access_key " \
                    "FROM hp2p_overlay " \
                    "WHERE overlay_id = %s"
            select_overlay = db_connector.select_one(query, (overlay_id,))

            if select_overlay is None:
                raise ValueError

            status_code = 202 if select_overlay.get('sub_type') == 'tree' else 200
            if select_overlay.get('auth_type') == 'closed':
                is_auth_peer = False
                auth_query = "SELECT peer_id FROM hp2p_auth_peer " \
                             "WHERE " \
                             "overlay_id = %s AND peer_id = %s"
                select_auth_peer = db_connector.select_one(auth_query, (overlay_id, peer_id))

                if select_auth_peer is not None:
                    is_auth_peer = True
                elif select_overlay.get('auth_access_key') == auth_access_key:
                    is_auth_peer = True

                if not is_auth_peer:
                    return {'overlay_id': overlay_id}, 407

            select_peers_info_query = "SELECT peer_id,address FROM " \
                                      "(SELECT peer_id , overlay_id , peer_index, address, " \
                                      "(max_capa - num_primary - num_out_candidate - num_in_candidate) " \
                                      "as capa FROM hp2p_peer WHERE overlay_id = %s) AS t_capa " \
                                      "WHERE capa > 0 ORDER BY capa DESC , peer_index ASC LIMIT 5"
            peer_info_list = db_connector.select(select_peers_info_query, (overlay_id,))

            overlay: Overlay = Factory.instance().get_overlay(overlay_id)
            if overlay is None:
                raise ValueError

            peer_index = overlay.peer_index + 1
            insert_peer_query = "INSERT INTO hp2p_peer " \
                                "(peer_id, overlay_id, overlay_type, sub_type, expires, address, " \
                                "peer_index, created_at, updated_at) " \
                                "VALUES " \
                                "(%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"
            peer_parameters = (peer_id, overlay_id, overlay_type, sub_type, expires, peer_address, peer_index)
            db_connector.insert(insert_peer_query, peer_parameters)

            result = {
                'overlay_id': overlay_id,
                'type': overlay_type,
                'sub_type': sub_type,
                'expires': expires,
                'status': {
                    'peer_index': peer_index,
                    'peer_info_list': peer_info_list
                }
            }

            if status_code == 202:
                del result['expires']

            overlay.peer_index = peer_index
            overlay.peer_id_list.append(peer_id)

            db_connector.commit()
            return result, status_code
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


class HybridOverlayRefresh(Resource):
    def put(self):
        print("[SERVER] Call HybridOverlayRefresh", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = request_data.get('overlay_id')
            auth_access_key = request_data.get('auth').get('access_key') if request_data.get(
                'auth') is not None else None
            # TODO => PEER expires 관리-갱신
            expires = request_data.get('expires') if 'expires' in request_data else 3600
            peer_info_data = request_data.get('peer_info') if 'peer_info' in request_data else {}
            peer_id = peer_info_data.get('peer_id')
            peer_address = peer_info_data.get('address')

            if overlay_id is None or peer_id is None or peer_address is None:
                raise ValueError

            select_peer_query = "SELECT peer_id FROM hp2p_peer " \
                                "WHERE " \
                                "peer_id = %s AND overlay_id = %s"
            select_peer = db_connector.select_one(select_peer_query, (peer_id, overlay_id))

            if select_peer is None:
                raise ValueError

            select_overlay_query = "SELECT " \
                                   "overlay_id, overlay_type, sub_type, overlay_status, auth_type, auth_access_key " \
                                   "FROM hp2p_overlay " \
                                   "WHERE overlay_id = %s"
            select_overlay = db_connector.select_one(select_overlay_query, (overlay_id,))

            if select_overlay is None:
                raise ValueError

            if select_overlay.get('auth_type') == 'closed':
                is_auth_peer = False
                auth_query = "SELECT peer_id FROM hp2p_auth_peer " \
                             "WHERE " \
                             "overlay_id = %s AND peer_id = %s"
                select_auth_peer = db_connector.select_one(auth_query, (overlay_id, peer_id))

                if select_auth_peer is not None:
                    is_auth_peer = True
                elif select_overlay.get('auth_access_key') == auth_access_key:
                    is_auth_peer = True

                if not is_auth_peer:
                    return {'overlay_id': overlay_id}, 407

            update_peer_query = "UPDATE hp2p_peer SET " \
                                "expires = %s , updated_at = NOW() " \
                                "WHERE " \
                                "peer_id = %s AND overlay_id = %s "
            db_connector.update(update_peer_query, (expires, peer_id, overlay_id))

            result = {
                'overlay_id': overlay_id,
                'expires': expires
            }

            db_connector.commit()
            return result, 200
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


class HybridOverlayLeave(Resource):
    def delete(self):
        print("[SERVER] Call HybridOverlayLeave", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            # TODO => PEER expires 관리-갱신
            overlay_id = request_data.get('overlay_id')
            overlay_type = request_data.get('type')
            sub_type = request_data.get('sub_type')
            peer_id = request_data.get('peer_info').get('peer_id') if request_data.get(
                'peer_info') is not None else None

            if overlay_id is None or overlay_type is None or sub_type is None or peer_id is None:
                raise ValueError

            # select_overlay_query = "SELECT " \
            #                        "* " \
            #                        "FROM hp2p_overlay " \
            #                        "WHERE overlay_id = %s"
            # select_overlay = db_connector.select_one(select_overlay_query, (overlay_id,))
            #
            # if select_overlay is None:
            #     raise ValueError

            select_peer_query = "SELECT " \
                                "* " \
                                "FROM hp2p_peer " \
                                "WHERE peer_id = %s AND overlay_id = %s"
            select_peer = db_connector.select_one(select_peer_query, (peer_id, overlay_id))

            if select_peer is None:
                raise ValueError

            db_connector.delete("DELETE FROM hp2p_peer WHERE peer_id = %s AND overlay_id = %s", (peer_id, overlay_id))

            result = {
                'overlay_id': overlay_id,
            }

            overlay: Overlay = Factory.instance().get_overlay(overlay_id)
            if overlay is not None:
                overlay.peer_id_list.remove(peer_id)

            db_connector.commit()
            return result, 200
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


class HybridOverlayReport(Resource):
    def put(self):
        print("[SERVER] Call HybridOverlayReport", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()
            overlay_id = request_data.get('overlay_id')
            peer_status = request_data.get('peer_status')

            max_capa = peer_status.get('max_capa')
            num_primary = peer_status.get('num_primary')
            num_out_candidate = peer_status.get('num_out_candidate')
            num_in_candidate = peer_status.get('num_in_candidate')
            costmap = peer_status.get('costmap')
            peer_id = costmap.get('peer_id')

            if overlay_id is None or peer_status is None or peer_id is None or costmap is None:
                raise ValueError

            select_peer_query = "SELECT " \
                                "* " \
                                "FROM hp2p_peer " \
                                "WHERE overlay_id = %s AND peer_id = %s"
            select_peer = db_connector.select_one(select_peer_query, (overlay_id, peer_id))

            if select_peer is None:
                raise ValueError

            update_peer_query = "UPDATE hp2p_peer SET " \
                                "max_capa = %s, num_primary = %s, num_out_candidate = %s, " \
                                "num_in_candidate = %s, costmap = %s " \
                                "WHERE overlay_id = %s AND peer_id = %s"
            parameters = (max_capa, num_primary, num_out_candidate, num_in_candidate, json.dumps(costmap),
                          overlay_id, peer_id)
            db_connector.update(update_peer_query, parameters)

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
