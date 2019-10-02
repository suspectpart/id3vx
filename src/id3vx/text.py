def shorten(string, length):
    short = string[:length]

    return short if short == string else f"{short} ..."
