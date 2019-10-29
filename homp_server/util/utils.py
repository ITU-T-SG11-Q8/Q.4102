from database.db_connector import DBConnector
from data.factory import Factory
from classes.overlay import Overlay
from classes.peer import Peer


class Utils:
    @staticmethod
    def create_overlay_map():
        print("Call create_overlay_map", flush=True)
        db_connector = DBConnector()
        select_overlay_list = db_connector.select("SELECT * FROM hp2p_overlay")

        for select_overlay in select_overlay_list:
            overlay_id = select_overlay.get('overlay_id')
            overlay = Overlay()
            overlay.overlay_id = overlay_id
            overlay.expires = select_overlay.get('expires')
            overlay.heartbeat_interval = select_overlay.get('heartbeat_interval')
            overlay.heartbeat_timeout = select_overlay.get('heartbeat_timeout')

            select_peer_query = "SELECT * FROM hp2p_peer " \
                                "WHERE overlay_id = %s ORDER BY ticket_id"
            select_peer_list = db_connector.select(select_peer_query, (overlay_id,))
            for select_peer in select_peer_list:
                ticket_id = select_peer.get('ticket_id')
                peer_id = select_peer.get('peer_id')
                overlay.current_ticket_id = ticket_id

                peer = Peer()
                peer.overlay_id = overlay_id
                peer.expires = select_peer.get('expires')
                peer.peer_id = peer_id
                peer.ticket_id = ticket_id
                overlay.add_peer(peer_id, peer)

            Factory.instance().set_overlay(overlay_id, overlay)
