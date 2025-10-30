from multiprocessing import Process


def run_timeout(func, *args, timeout=1, **kwargs):
    p = Process(target=func, args=args, kwargs=kwargs)
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        call = format_call(func, args, kwargs)
        raise TimeoutError(f"function call timed out (>{timeout}s): {call}")


def format_call(func, args, kwargs):
    fargs = [truncated_repr(i) for i in args]
    fargs += [f"{k}={truncated_repr(v)}" for k, v in kwargs.items()]
    fargs = ", ".join(fargs)
    return f"{func.__name__}({fargs})"

def truncated_repr(x, length=10, ellipsis="..."):
    thresh = 2 * length + len(ellipsis)
    x = repr(x)
    if len(x) <= thresh:
        return x
    return x[:length] + ellipsis + x[-length:]





if __name__ == "__main__":
    from string import ascii_lowercase
    from time import sleep

    def slooow(x, y=123):
        for i in range(x):
            print(i)
            sleep(0.1)
        return "done"

    run_timeout(slooow, 10, y=ascii_lowercase[:22], timeout=0.5)



