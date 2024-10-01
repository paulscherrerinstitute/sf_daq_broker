"""
this is a compatibility layer between slsdet versions
in order to support (i.e., not crash) versions 6.1.2 and 8.0.1
to be removed once we updated all JFs to firmware 8.x
"""

import logging

from slsdet import Jungfrau as JungfrauOriginal
from slsdet import *


_logger = logging.getLogger("broker_writer")


try:
    # class added in slsdet 8.0.0
    pedestalParameters
except NameError:
    _logger.warning("slsdet.pedestalParameters not available")
    pedestalParameters = None


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


    # property added in slsdet 7.0.0
    sync = None

    # method added in slsdet 7.0.0
    def setMaster(self, *args, **kwargs):
        printable_args = make_printable_args(args, kwargs)
        _logger.warning("ignoring call Jungfrau.setMaster({printable_args})")
        pass

    # property added in slsdet 8.0.0
    pedestalmode = None



def make_printable_args(args, kwargs):
    args = list(args)
    args += [f"{k}={v}" for k, v in kwargs.items()]
    return ", ".join(str(i) for i in args)



