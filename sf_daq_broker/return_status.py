from functools import wraps


def return_status(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            stat = "ok"
            msg = func(*args, **kwargs)
        except Exception as e: #TODO: also store type(e).__name__ as "exception" ?
            stat = "failed"
            msg = str(e)
        res = {
            "status": stat,
            "message": msg
        }
        return res
    return wrapper



if __name__ == "__main__":
    @return_status 
    def test_works(x): 
        return f"test works {x}"

    @return_status 
    def test_fails(x): 
        raise ValueError(f"test fails {x}")

    assert test_works(123) == {"status": "ok",     "message": "test works 123"}
    assert test_fails(123) == {"status": "failed", "message": "test fails 123"}
    assert test_works()    == {"status": "failed", "message": "test_works() missing 1 required positional argument: 'x'"}



