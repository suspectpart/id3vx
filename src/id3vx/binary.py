# Ported from https://en.wikipedia.org/wiki/Synchsafe
def synchsafe(integer):
    out = 0
    mask = 0x7F

    while mask ^ 0x7FFFFFFF:
        out = integer & ~mask
        out <<= 1
        out |= integer & mask
        mask = ((mask + 1) << 8) - 1
        integer = out

    return out


def unsynchsafe(integer):
    out = 0
    mask = 0x7F000000

    while mask:
        out >>= 1
        out |= integer & mask
        mask >>= 8

    return out
