class RequestPath:
    OverlayQuery = "/HybridOverlayQuery"
    OverlayCreation = "/HybridOverlayCreation"
    OverlayRemoval = "/HybridOverlayRemoval"

    OverlayJoin = "/HybridOverlayJoin"
    OverlayLeave = "/HybridOverlayLeave"
    OverlayRefresh = "/HybridOverlayRefresh"
    OverlayReport = "/HybridOverlayReport"


class RequestMessageType:
    HELLO_PEER = 1
    ESTAB_PEER = 2
    PROBE_PEER = 3
    SET_PRIMARY = 4
    SET_CANDIDATE = 5
    BROADCAST_DATA = 6
    RELEASE_PEER = 7
    HEARTBEAT = 8
    SCAN_TREE = 9
