def getIntegerAsBlock(i):
    x = unsignedToSigned(i % 4096, 2048)
    i = int((i - x) / 4096)
    y = unsignedToSigned(i % 4096, 2048)
    i = int((i - y) / 4096)
    z = unsignedToSigned(i % 4096, 2048)
    return x,y,z

def unsignedToSigned(i, max_positive):
    if i < max_positive:
        return i
    else:
        return i - 2*max_positive

if __name__ == "__main__":
    print(getIntegerAsBlock(218157062))