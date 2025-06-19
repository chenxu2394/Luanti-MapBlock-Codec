def getBlockAsInteger(p):
    return int64(p[2]*16777216 + p[1]*4096 + p[0])

def int64(u):
    while u >= 2**63:
        u -= 2**64
    while u <= -2**63:
        u += 2**64
    return u

if __name__ == "__main__":
    print(getBlockAsInteger([0, 85, 0]))