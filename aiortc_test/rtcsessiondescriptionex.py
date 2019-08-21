from aiortc import RTCSessionDescription
import attr

@attr.s
class RTCSessionDescriptionEx():
    fromid = attr.ib()
    toid = attr.ib()
    sdp = attr.ib()
    "A string containing the session description's SDP."
    type = attr.ib(validator=attr.validators.in_(['offer', 'pranswer', 'answer', 'rollback']))
    "A string describing the session description's type."

    @staticmethod
    def copy(rsd):
        rsde = RTCSessionDescriptionEx(fromid=None, toid=None, sdp=rsd.sdp, type=rsd.type)
        
        if isinstance(rsd, RTCSessionDescriptionEx):
            rsde.fromid = rsd.fromid
            rsde.toid = rsd.toid

        return rsde