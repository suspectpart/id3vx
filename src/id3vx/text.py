def shorten(string, length=50):
    short = string[:length]

    return short if short == string else f"{short} ..."
