from rtc.rtc_connection import RtcConnection
from data.factory import Factory, Peer

if __name__ == '__main__':
    peer_id = input('id:')
    rtc_connection = RtcConnection(peer_id)
    rtc_connection.web_socket_send_hello()
    Factory.instance().set_rtc_connection(rtc_connection)

    peer = Peer()
    peer.peer_id = peer_id
    peer.ticket_id = 1
    peer.overlay_id = "asdasdasdasd0"

    while True:
        print('')
        input_peer_id = input('peer id:')

        if input_peer_id == 'bye':
            rtc_connection.web_socket_send_bye()
            break

        if len(input_peer_id) > 0:
            rtc_connection.web_socket_send_hello_peer(peer, input_peer_id)

    rtc_connection.close()

    input('')
