
def jarvis_keys(k, c, p):
    # key is master key
    # c is list of round constants
    for c_i in c:
        k = (pow(k, p - 2, p) + c_i) % p
        yield k  # emit sequence of derived keys


def jarvis(x, k, c, p):
    # m is a message
    # k is master key
    # c is list of round constants, length is the number of rounds
    s_i = (x + k) % p
    for k_i in jarvis_keys(k, c, p):
        s_i = (pow(s_i, p - 2, p) + k_i) % p
    return s_i


def friday(x, k, c, p):
    for x_i in x:
        k = (k + x_i + jarvis(x_i, k, c, p)) % p
    return k
