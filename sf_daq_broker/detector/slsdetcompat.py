"""
this is a compatibility layer between slsdet versions
in order to support (i.e., not crash) versions 6.1.2 and 8.0.1
to be removed once we updated all JFs to firmware 8.x
"""

import logging

from slsdet import Jungfrau as JungfrauOriginal
from slsdet import detectorSettings, gainMode, timingMode


_logger = logging.getLogger("broker_writer")


# class added in slsdet 8.0.0
try:
    from slsdet import pedestalParameters
except ImportError:
    _logger.warning("slsdet.pedestalParameters not available")
    pedestalParameters = None



def make_mock_property(cls, name):
    msg = f"{cls}.{name} not available"

    def getter(self):
        _logger.warning(msg)
        return None

    def setter(self, _value):
        _logger.warning(msg)

    return property(getter, setter)



class Jungfrau(JungfrauOriginal):

    # property renamed from txndelay_frame (slsdet <= 6.1.2) to txdelay_frame (slsdet >= 7.0.0)
    if not hasattr(JungfrauOriginal, "txdelay_frame"):

        @property
        def txdelay_frame(self):
            _logger.warning("actually returning Jungfrau.txndelay_frame")
            return self.txndelay_frame

        @txdelay_frame.setter
        def txdelay_frame(self, value):
            _logger.warning("actually setting Jungfrau.txndelay_frame")
            self.txndelay_frame = value


    # method added in slsdet 7.0.0
    if not hasattr(JungfrauOriginal, "setMaster"):
        def setMaster(self, *args, **kwargs):
            printable_args = make_printable_args(args, kwargs)
            _logger.warning(f"ignoring call Jungfrau.setMaster({printable_args})")

    # property added in slsdet 7.0.0
    if not hasattr(JungfrauOriginal, "sync"):
        sync = make_mock_property("Jungfrau", "sync")

    # property added in slsdet 8.0.0
    if not hasattr(JungfrauOriginal, "pedestalmode"):
        pedestalmode = make_mock_property("Jungfrau", "pedestalmode")



def make_printable_args(args, kwargs):
    args = list(args)
    args += [f"{k}={v}" for k, v in kwargs.items()]
    return ", ".join(str(i) for i in args)



