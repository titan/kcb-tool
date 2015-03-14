import math

w = 32
r = 20
e = math.e
goldenRatio = 1.6180339887496482
Pw = 0xb7e15163
Qw = 0x9e3779b9
modulo = 2**32

def zeroFillShiftRight32(a:int, b:int) -> int:
    mask = 2 ** (32 - b) - 1
    return (a >> b) & mask

def arraycopy(src, soff, dst, doff, length):
    for i in range(length):
        dst[doff + i] = src[soff + i]

def convBytesWords(key:bytes, c:int) -> [int]:
    tmp = [0] * c
    off = 0
    for i in range(c):
        b0 = key[off] & 0xFF
        off += 1
        b1 = (key[off] & 0xFF) <<  8
        off += 1
        b2 = (key[off] & 0xFF) << 16
        off += 1
        b3 = (key[off] & 0xFF) << 24
        off += 1
        tmp[i] = b0 | b1 | b2 | b3
    return tmp

def generateSubkeys(key:bytes) -> [int]:
    u = int(w / 8)
    c = int(len(key) / u)
    t = 2 * r + 4

    L = convBytesWords(key, c)
    S = [0] * t
    S[0] = Pw
    for i in range(1, t):
        S[i] = S[i - 1] + Qw

    A = 0
    B = 0
    k = 0
    j = 0
    v = 3 * max(c, t)

    for i in range(v):
        A = S[k] = rotl((S[k] + A + B) % modulo, 3)
        B = L[j] = rotl((L[j] + A + B) % modulo, (A + B) % 32)
        k = (k + 1) % t
        j = (j + 1) % c

    return S

def rotl(val:int, pas:int) -> int:
    return (val << pas) | zeroFillShiftRight32(val, (32 - pas))

def rotr(val:int, pas:int) -> int:
    return zeroFillShiftRight32(val, pas) | (val << (32 - pas))

def decryptBlock(S:[int], input:bytes) -> bytes:
    tmp = [0] * len(input)
    data = [0] * int(len(input) / 4)
    off = 0
    for i in range(len(data)):
        b0 = input[off] & 0xFF
        off += 1
        b1 = (input[off] & 0xFF) <<  8
        off += 1
        b2 = (input[off] & 0xFF) << 16
        off += 1
        b3 = (input[off] & 0xFF) << 24
        off += 1
        data[i] = b0 | b1 | b2 | b3
    A = data[0]
    B = data[1]
    C = data[2]
    D = data[3]
    C = (C - S[2 * r + 3]) % modulo
    A = (A - S[2 * r + 2]) % modulo
    for i in range(r, 0, -1):
        aux = D
        D = C
        C = B
        B = A
        A = aux
        u = rotl((D * (2 * D + 1)) % modulo, 5)
        t = rotl((B * (2 * B + 1)) % modulo, 5)
        C = rotr((C - S[2 * i + 1]) % modulo, t % 32) ^ u
        A = rotr((A - S[2 * i]) % modulo, u % 32) ^ t

    D = (D - S[1]) % modulo
    B = (B - S[0]) % modulo

    data[0] = A
    data[1] = B
    data[2] = C
    data[3] = D

    for i in range(len(tmp)):
        tmp[i] = zeroFillShiftRight32(data[int(i / 4)], (i % 4) * 8) & 0xFF
    return tmp

def encryptBlock(S:[int], input:bytes) -> bytes:
    tmp = [0] * len(input)
    data = [0] * int(len(input) / 4)
    off = 0
    for i in range(len(data)):
        b0 = input[off] & 0xFF
        off += 1
        b1 = (input[off] & 0xFF) <<  8
        off += 1
        b2 = (input[off] & 0xFF) << 16
        off += 1
        b3 = (input[off] & 0xFF) << 24
        off += 1
        data[i] = b0 | b1 | b2 | b3
    A = data[0]
    B = data[1]
    C = data[2]
    D = data[3]

    B = (B + S[0]) % modulo
    D = (D + S[1]) % modulo

    for i in range(1, r + 1):
        t = rotl((B * (2 * B + 1)) % modulo, 5)
        u = rotl((D * (2 * D + 1)) % modulo, 5)
        A = (rotl(A ^ t, u % 32) + S[2 * i]) % modulo
        C = (rotl(C ^ u, t % 32) + S[2 * i + 1]) % modulo

        aux = A
        A = B
        B = C
        C = D
        D = aux

    A = (A + S[2 * r + 2]) % modulo
    C = (C + S[2 * r + 3]) % modulo

    data[0] = A
    data[1] = B
    data[2] = C
    data[3] = D

    for i in range(len(tmp)):
        tmp[i] = zeroFillShiftRight32(data[int(i / 4)], (i % 4) * 8) & 0xFF
    return tmp

def paddingKey(key:bytes) -> bytes:
    l = len(key)
    for i in range(len(key) % 4):
        key.append(0)
    return key

def deletePadding(input:bytes) -> bytes:
    count = 0

    i = len(input) - 1
    while input[i] == 0:
        count += 1
        i -= 1
    tmp = [0] * (len(input) - count - 1)
    arraycopy(input, 0, tmp, 0, len(tmp))
    return tmp

def encrypt(data:bytes, key:bytes) -> bytes:
    block = [0] * 16
    key = paddingKey(key)
    S = generateSubkeys(key)

    length = 16 - len(data) % 16
    padding = [0] * length
    padding[0] = 0x80
    count = 0
    tmp = [0] * (len(data) + length)
    for i in range(len(data) + length):
        if i > 0 and i % 16 == 0:
            block = encryptBlock(S, block)
            arraycopy(block, 0, tmp, i - 16, len(block))
        if i < len(data):
            block[i % 16] = data[i]
        else:
            block[i % 16] = padding[count]
            count += 1
            if count > length - 1:
                count = 1
    block = encryptBlock(S, block)
    arraycopy(block, 0, tmp, len(data) + length - 16, len(block))
    return tmp

def decrypt(data:bytes, key:bytes) -> bytes:
    tmp = [0] * len(data)
    block = [0] * 16
    key = paddingKey(key)
    S = generateSubkeys(key)

    for i in range(len(data)):
        if i > 0 and i % 16 == 0:
            block = decryptBlock(S, block)
            arraycopy(block, 0, tmp, i - 16, len(block))
        if i < len(data):
            block[i % 16] = data[i]
    block = decryptBlock(S, block)
    arraycopy(block, 0, tmp, len(data) - 16, len(block))
    return deletePadding(tmp)

if __name__ == "__main__":
    # f = open("test.dat", 'rb')
    # c = f.read()
    # f.close()
    # d = decrypt(c, bytearray("test", "ascii"))
    # print(d.decode("ascii"))
    c = encrypt(bytearray("This is a test.", "ascii"), bytearray("test", "ascii"))
    f = open("test1.dat", 'wb')
    f.write(bytearray(c))
    f.close()
