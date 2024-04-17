import telnetlib
import warnings


ID_TO_HOST = {
    2:  "jf4m5-ctrl",
    6:  "jf16ma-ctrl",
    7:  "jf16mb-ctrl",
    15: "jf4mg-ctrl",
    17: "jf8ma-ctrl"
}



class JFCtrl(telnetlib.Telnet):

    PROMPT = ":/> "
    BIN_PROMPT = PROMPT.encode()

    ERRADIC_PROMPT = "root:/> "

    ENTER = b"\n"
    NEWLINE = "\r\n"

    def __init__(self, ID, *args, **kwargs):
        host = ID_TO_HOST.get(ID)
        if not host:
            self.sock = None # circumvent a crash in Telnet.close when raising here
            raise ValueError(f"cannot match Jungfrau ID {ID} to host name")
        super().__init__(host, *args, **kwargs)
        self.read_until_prompt()

    def get_monitor(self):
        cmd = "power_control_user/monitor"
        raw = self.execute(cmd)
        res = {}
        for line in raw:
            name, val = line.rsplit(":", 1)
            val = int(val)
            name, val = adjust_units(name, val)
            res[name] = val
        return res

    def execute(self, cmd):
        bin_cmd = cmd.encode()
        self.write(bin_cmd)
        self.write(self.ENTER)
        res = self.read_until_prompt().decode()
        return self.parse_result(res, cmd)

    def read_until_prompt(self):
        return self.read_until(self.BIN_PROMPT)

    def parse_result(self, res, cmd):
        res = res.split(self.NEWLINE)
        last = res.pop()
        if last == self.PROMPT:
            return res
        msg = f'expected prompt "{self.PROMPT}" but got "{last}" instead'
        if last == self.ERRADIC_PROMPT:
            warnings.warn(msg, RuntimeWarning, stacklevel=2)
            first = res.pop(0)
            assert first == cmd, repr(first)
            return res
        raise ValueError(msg)



def adjust_units(name, value):
    milli = " [m"
    if milli in name:
        name = name.replace(milli, " [")
        value /= 1000
    return name, value





if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("ID", choices=ID_TO_HOST, type=int, help="Jungfrau ID")

    clargs = parser.parse_args()

    with JFCtrl(clargs.ID) as jfc:
        mon = jfc.get_monitor()
        for k, v in mon.items():
            print(k, "=", v)



