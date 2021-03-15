import epics


class EpicsBuffer(object):

    def __init__(self, channel_list):
        self.channel_list = channel_list
        self.buffer = {}

        for pv in channel_list:
            epics.get_pv(pvname=pv,
                         form="time",
                         connect=True,
                         timeout=1,
                         auto_monitor=True,
                         connection_callback=self._connection_callback,
                         callback=self._value_callback
                         )

    def _connection_callback(self, pvname, conn, **kwargs):
        new_status = {
            "status": conn
        }

        self.buffer[pvname]["connection"] = new_status

    def _value_callback(self, pvname, value, status, posixseconds, nanoseconds, **kwargs):
        new_value = {
            "value": value,
            "status": status,
            "seconds": posixseconds,
            "nano_seconds": nanoseconds
        }

        self.buffer[pvname]["data"] = new_value

    def get_buffer(self):
        return self.buffer()
