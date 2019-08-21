from server.db_connector import DBConnector
from server.factory import Factory
from server.classes import Overlay


class Utils:

    @staticmethod
    def CreateOverlayMap():
        print("Call CreateOverlayMap", flush=True)
        db_connector = DBConnector()
        select_overlay_list = db_connector.select("SELECT overlay_id FROM hp2p_overlay")

        for select_overlay in select_overlay_list:
            overlay_id = select_overlay.get('overlay_id')
            overlay = Overlay(overlay_id)

            select_peer_query = "SELECT peer_id, peer_index FROM hp2p_peer " \
                                "WHERE overlay_id = %s ORDER BY peer_index"
            select_peer_list = db_connector.select(select_peer_query, (overlay_id,))
            for select_peer in select_peer_list:
                overlay.peer_id_list.append(select_peer.get('peer_id'))
                overlay.peer_index = select_peer.get('peer_index')

            Factory.instance().set_overlay(overlay_id, overlay)
