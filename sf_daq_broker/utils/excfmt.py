
def dueto(exc):
    ef = excfmt(exc)
    return f"(due to: {ef})"


def excfmt(exc):
    tn = typename(exc)
    return f"{tn}: {exc}"


def typename(obj):
    return type(obj).__name__





if __name__ == "__main__":
    try:
        int("a")
    except Exception as e:
        assert excfmt(e) == "ValueError: invalid literal for int() with base 10: 'a'"
        assert dueto(e) == "(due to: ValueError: invalid literal for int() with base 10: 'a')"



