class RequestPath:
    OverlayCreation = "/HybridOverlayCreation"
    OverlayQuery = "/HybridOverlayQuery"
    OverlayModification = "/HybridOverlayModification"
    OverlayRemoval = "/HybridOverlayRemoval"

    OverlayJoin = "/HybridOverlayJoin"
    OverlayReport = "/HybridOverlayReport"
    OverlayRefresh = "/HybridOverlayRefresh"
    OverlayLeave = "/HybridOverlayLeave"

    OverlayCostMap = "/api/OverlayCostMap"


class MessageType:
    VERSION = 0x01
    TYPE = 0x01

    REQUEST_HELLO_PEER = 1
    RESPONSE_HELLO_PEER = 1202

    REQUEST_ESTAB_PEER = 2
    RESPONSE_ESTAB_PEER = 2200
    RESPONSE_ESTAB_PEER_ERROR = 2603

    REQUEST_PROBE_PEER = 3
    RESPONSE_PROBE_PEER = 3200

    REQUEST_SET_PRIMARY = 4
    RESPONSE_SET_PRIMARY = 4200
    RESPONSE_SET_PRIMARY_ERROR = 4603

    REQUEST_SET_CANDIDATE = 5
    RESPONSE_SET_CANDIDATE = 5200

    REQUEST_BROADCAST_DATA = 6
    RESPONSE_BROADCAST_DATA = 6200

    REQUEST_RELEASE_PEER = 7
    RESPONSE_RELEASE_PEER = 7200

    REQUEST_HEARTBEAT = 8
    RESPONSE_HEARTBEAT = 8200

    REQUEST_SCAN_TREE = 9
    RESPONSE_SCAN_TREE_LEAF = 9200
    RESPONSE_SCAN_TREE_NON_LEAF = 9202
