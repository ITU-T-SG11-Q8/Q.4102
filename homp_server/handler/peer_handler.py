from flask import request
from flask_restful import Resource
from database.db_connector import DBConnector
from data.factory import Factory
from classes.overlay import Overlay
from classes.peer import Peer
from config import HOMS_CONFIG
import json
import math
from datetime import datetime


class HybridOverlayJoin(Resource):
    def post(self):
        print("[SERVER] Call HybridOverlayJoin", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = request_data.get('overlay_id')
            overlay_type = request_data.get('type')
            sub_type = request_data.get('sub_type')

            expires = request_data.get('expires') if 'expires' in request_data else 3600
            auth_access_key = request_data.get('auth').get('access_key') if request_data.get('auth') is not None \
                else None

            peer_info = request_data.get('peer_info')
            peer_id = peer_info.get('peer_id')
            peer_address = peer_info.get('address')
            peer_auth_password = peer_info.get('auth').get('password')

            recovery = request_data.get('recovery') if 'recovery' in request_data else False
            ticket_id = request_data.get('ticket_id')

            if overlay_id is None or overlay_type is None or sub_type is None or peer_id is None or \
                    peer_address is None or peer_auth_password is None:
                raise ValueError

            query = "SELECT " \
                    "overlay_id, overlay_type, sub_type, overlay_status, auth_type, auth_access_key, " \
                    "expires, heartbeat_interval, heartbeat_timeout " \
                    "FROM hp2p_overlay " \
                    "WHERE overlay_id = %s"
            select_overlay = db_connector.select_one(query, (overlay_id,))

            if select_overlay is None:
                raise ValueError

            if select_overlay.get('auth_type') == 'closed':
                is_auth_peer = False
                auth_query = "SELECT peer_id FROM hp2p_auth_peer " \
                             "WHERE " \
                             "overlay_id = %s AND peer_id = %s"
                select_auth_peer = db_connector.select_one(auth_query, (overlay_id, peer_id))

                if select_auth_peer is not None or select_overlay.get('auth_access_key') == auth_access_key:
                    is_auth_peer = True

                if not is_auth_peer:
                    return {'overlay_id': overlay_id}, 407

            get_overlay: Overlay = Factory.instance().get_overlay(overlay_id)

            if get_overlay is None:
                raise ValueError

            status_code = 202 if sub_type == 'tree' else 200

            peer_info_list_count = HOMS_CONFIG["PEER_INFO_LIST_COUNT"] \
                if HOMS_CONFIG["PEER_INFO_LIST_COUNT"] is not None else 3
            recovery_entrypoint_pos = HOMS_CONFIG["RECOVERY_ENTRYPOINT_POS"] \
                if HOMS_CONFIG["RECOVERY_ENTRYPOINT_POS"] is not None else 20
            initial_entrypoint_pos = HOMS_CONFIG["INITIAL_ENTRYPOINT_POS"] \
                if HOMS_CONFIG["INITIAL_ENTRYPOINT_POS"] is not None else 80
            peer_info_list = None

            if recovery:
                select_peer_query = "SELECT * FROM hp2p_peer " \
                                    "WHERE " \
                                    "peer_id = %s AND overlay_id = %s AND auth_password = %s"
                select_peer = db_connector.select_one(select_peer_query, (peer_id, overlay_id, peer_auth_password))
                if select_peer is None:
                    raise ValueError

                get_peer: Peer = get_overlay.get_peer(peer_id)
                if ticket_id is None or get_peer is None:
                    raise ValueError

                rank_pos = math.floor(get_overlay.get_peer_dict_len() * (recovery_entrypoint_pos / 100))
                rank_pos = max(rank_pos, 1)
                select_peers_recovery_query = "SELECT v_p_t.peer_id, v_p_t.address FROM " \
                                              " (SELECT p_t.*,@rownum := @rownum + 1 AS rank FROM hp2p_peer p_t," \
                                              " (SELECT @rownum := 0) r " \
                                              " WHERE p_t.overlay_id = %s ORDER BY p_t.ticket_id) v_p_t " \
                                              "WHERE v_p_t.rank <= %s AND v_p_t.ticket_id < %s " \
                                              "ORDER BY v_p_t.rank DESC LIMIT %s"
                peer_info_list = db_connector.select(select_peers_recovery_query,
                                                     (overlay_id, rank_pos, ticket_id, peer_info_list_count))
            else:
                # rank_pos = 0 # 테스트 용..
                rank_pos = math.floor(get_overlay.get_peer_dict_len() * (initial_entrypoint_pos / 100))
                select_peers_query = "SELECT v_p_t.peer_id, v_p_t.address FROM " \
                                     " (SELECT p_t.*,@rownum := @rownum + 1 AS rank FROM hp2p_peer p_t," \
                                     " (SELECT @rownum := 0) r " \
                                     " WHERE p_t.overlay_id = %s ORDER BY p_t.ticket_id) v_p_t " \
                                     "WHERE v_p_t.rank >= %s LIMIT %s"
                peer_info_list = db_connector.select(select_peers_query,
                                                     (overlay_id, rank_pos, peer_info_list_count))

                ticket_id = get_overlay.current_ticket_id + 1
                get_overlay.current_ticket_id = ticket_id

                insert_peer_query = "INSERT INTO hp2p_peer " \
                                    "(peer_id, overlay_id, ticket_id ,overlay_type, sub_type, expires, address, " \
                                    "auth_password, created_at, updated_at) " \
                                    "VALUES " \
                                    "(%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"
                db_connector.insert(insert_peer_query, (
                    peer_id, overlay_id, ticket_id, overlay_type, sub_type, expires, peer_address, peer_auth_password))

                new_peer = Peer()
                new_peer.overlay_id = overlay_id
                new_peer.expires = expires
                new_peer.peer_id = peer_id
                new_peer.ticket_id = ticket_id
                new_peer.update_time = datetime.now()
                get_overlay.add_peer(peer_id, new_peer)

            result = {
                'overlay_id': overlay_id,
                'type': overlay_type,
                'sub_type': sub_type,
                'expires': expires,
                'heartbeat_interval': select_overlay.get('heartbeat_interval'),
                'heartbeat_timeout': select_overlay.get('heartbeat_timeout'),
                'ticket_id': ticket_id,
                'status': {
                    'peer_info_list': peer_info_list
                }
            }

            if status_code == 200:
                del result['heartbeat_interval']
                del result['heartbeat_timeout']
                del result['ticket_id']

            # TODO => WebSocket 메시지 전송->Peer 추가 / 브라우저 D3 관계도 업데이트
            db_connector.commit()
            return result, status_code
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500


# if HOMS_CONFIG["APPLY_PEER_CAPA"]: # APPLY_PEER_CAPA 무시
#     select_peers_info_query = "SELECT peer_id,address FROM " \
#                               "(SELECT peer_id , overlay_id , ticket_id, address, " \
#                               "(max_capa - num_primary - num_out_candidate - num_in_candidate) " \
#                               "as capa FROM hp2p_peer WHERE overlay_id = %s) AS t_capa " \
#                               "WHERE capa > 0 ORDER BY capa DESC , ticket_id ASC LIMIT %s"
#
# else:
#     select_peers_info_query = "SELECT v_p_t.peer_id, v_p_t.address FROM " \
#                               " (SELECT p_t.*,@rownum := @rownum + 1 AS rank FROM hp2p_peer p_t," \
#                               " (SELECT @rownum := 0) r " \
#                               " WHERE p_t.overlay_id = %s ORDER BY p_t.ticket_id) v_p_t " \
#                               "WHERE v_p_t.rank >= %s limit %s"

class HybridOverlayReport(Resource):
    def put(self):
        print("[SERVER] Call HybridOverlayReport", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()
            overlay_id = request_data.get('overlay_id')
            peer_status = request_data.get('status')

            if overlay_id is None or peer_status is None:
                raise ValueError

            num_primary = peer_status.get('num_primary')
            num_out_candidate = peer_status.get('num_out_candidate')
            num_in_candidate = peer_status.get('num_in_candidate')
            costmap = peer_status.get('costmap')
            peer_id = costmap.get('peer_id')

            if num_primary is None or num_out_candidate is None or num_in_candidate is None or \
                    costmap is None or peer_id is None:
                raise ValueError

            select_overlay_query = "SELECT * " \
                                   "FROM hp2p_overlay " \
                                   "WHERE overlay_id = %s"
            select_overlay = db_connector.select_one(select_overlay_query, (overlay_id,))

            if select_overlay is None:
                raise ValueError

            select_peer_query = "SELECT * " \
                                "FROM hp2p_peer " \
                                "WHERE overlay_id = %s AND peer_id = %s"
            select_peer = db_connector.select_one(select_peer_query, (overlay_id, peer_id))

            if select_peer is None:
                raise ValueError

            get_overlay: Overlay = Factory.instance().get_overlay(overlay_id)
            if get_overlay is None:
                raise ValueError

            get_peer: Peer = get_overlay.get_peer(peer_id)
            if get_peer is None:
                raise ValueError

            if get_peer.costmap != costmap:
                # TODO => WebSocket 메시지 전송->Peer 상태 갱신 / 브라우저 D3 관계도 업데이트
                get_peer.num_primary = num_primary
                get_peer.num_in_candidate = num_in_candidate
                get_peer.num_out_candidate = num_out_candidate
                get_peer.costmap = costmap

                update_peer_query = "UPDATE hp2p_peer SET " \
                                    "num_primary = %s, num_out_candidate = %s, " \
                                    "num_in_candidate = %s, costmap = %s, report_time = NOW() " \
                                    "WHERE overlay_id = %s AND peer_id = %s"
                parameters = (
                    num_primary, num_out_candidate, num_in_candidate, json.dumps(costmap), overlay_id, peer_id)
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


class HybridOverlayRefresh(Resource):
    def put(self):
        print("[SERVER] Call HybridOverlayRefresh", flush=True)
        db_connector = DBConnector()
        try:
            request_data = request.get_json()

            overlay_id = request_data.get('overlay_id')
            expires = request_data.get('expires')
            auth_access_key = request_data.get('auth').get('access_key') if request_data.get(
                'auth') is not None else None

            peer_info = request_data.get('peer_info')
            peer_id = peer_info.get('peer_id')
            peer_address = peer_info.get('address')
            peer_auth_password = peer_info.get('auth').get('password')

            if overlay_id is None or peer_id is None or peer_address is None or peer_auth_password is None:
                raise ValueError

            select_peer_query = "SELECT * FROM hp2p_peer " \
                                "WHERE " \
                                "peer_id = %s AND overlay_id = %s AND auth_password = %s"
            select_peer = db_connector.select_one(select_peer_query, (peer_id, overlay_id, peer_auth_password))

            if select_peer is None:
                raise ValueError

            get_overlay: Overlay = Factory.instance().get_overlay(overlay_id)
            if get_overlay is None:
                raise ValueError

            get_peer: Peer = get_overlay.get_peer(peer_id)
            if get_peer is None:
                raise ValueError

            get_peer.update_time = datetime.now()
            if expires is None:
                expires = select_peer.get('expires')
            else:
                get_peer.expires = expires

            select_overlay_query = "SELECT " \
                                   "* " \
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
                                "updated_at = NOW() " \
                                "WHERE " \
                                "peer_id = %s AND overlay_id = %s "
            db_connector.update(update_peer_query, (peer_id, overlay_id))

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

            overlay_id = request_data.get('overlay_id')
            overlay_type = request_data.get('type')
            sub_type = request_data.get('sub_type')

            peer_info = request_data.get('peer_info')
            peer_id = peer_info.get('peer_id')
            peer_auth_password = peer_info.get('auth').get('password')

            if overlay_id is None or overlay_type is None or sub_type is None or peer_id is None or \
                    peer_auth_password is None:
                raise ValueError

            select_overlay_query = "SELECT " \
                                   "* " \
                                   "FROM hp2p_overlay " \
                                   "WHERE overlay_id = %s"
            select_overlay = db_connector.select_one(select_overlay_query, (overlay_id,))

            if select_overlay is None:
                raise ValueError

            select_peer_query = "SELECT " \
                                "* " \
                                "FROM hp2p_peer " \
                                "WHERE peer_id = %s AND overlay_id = %s AND auth_password = %s"
            select_peer = db_connector.select_one(select_peer_query, (peer_id, overlay_id, peer_auth_password))
            if select_peer is None:
                raise ValueError

            db_connector.delete("DELETE FROM hp2p_peer WHERE peer_id = %s AND overlay_id = %s", (peer_id, overlay_id))

            get_overlay: Overlay = Factory.instance().get_overlay(overlay_id)
            if get_overlay is None:
                raise ValueError

            get_peer: Peer = get_overlay.get_peer(peer_id)
            if get_peer is None:
                raise ValueError

            get_overlay.delete_peer(peer_id)
            result = {
                'overlay_id': overlay_id,
            }
            # TODO => WebSocket 메시지 전송->Peer 삭제 / 브라우저 D3 관계도 업데이트
            db_connector.commit()
            return result, 200
        except ValueError:
            db_connector.rollback()
            return 'BAD REQUEST', 400
        except Exception as exception:
            db_connector.rollback()
            return str(exception), 500
