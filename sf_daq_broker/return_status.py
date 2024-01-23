from functools import wraps


def return_status(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        except Exception as e: #TODO: also store type(e).__name__ as "exception" ?
            return {
                "status": "failed",
                "message": str(e)
            }
        else:
            if is_message_dict(res):
                res.setdefault("status", "ok")
            else:
                res = {
                    "status": "ok",
                    "message": res
                }
            #TODO: check for allowed values in status?
            return res
    return wrapper


def is_message_dict(d):
    return isinstance(d, dict) and "message" in d





if __name__ == "__main__":
    @return_status
    def test_str_works(x):
        return f"test works {x}"

    @return_status
    def test_str_fails(x):
        raise ValueError(f"test fails {x}")

    @return_status
    def test_dict_nostatus():
        return {"message": "already a dict"}

    @return_status
    def test_dict_status():
        return {"status": "stat", "message": "already a dict"}

    @return_status
    def test_dict_nostatus_extra():
        return {"message": "already a dict", "other": "whatever"}

    @return_status
    def test_dict_status_extra():
        return {"status": "stat", "message": "already a dict", "other": "whatever"}


    assert test_str_works(123) == {"status": "ok",     "message": "test works 123"}
    assert test_str_fails(123) == {"status": "failed", "message": "test fails 123"}
    assert test_str_works()    == {"status": "failed", "message": "test_str_works() missing 1 required positional argument: 'x'"}

    assert test_dict_nostatus()       == {"status": "ok",   "message": "already a dict"}
    assert test_dict_status()         == {"status": "stat", "message": "already a dict"}
    assert test_dict_nostatus_extra() == {"status": "ok",   "message": "already a dict", "other": "whatever"}
    assert test_dict_status_extra()   == {"status": "stat", "message": "already a dict", "other": "whatever"}



