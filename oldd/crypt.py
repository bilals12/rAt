from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto.Util.number import long_to_bytes, bytes_to_long

def gf_2_128_mul(x: int, y: int) -> int:
    assert 0 <= x < (1 << 128) and 0 <= y < (1 << 128)
    res = 0
    for i in range(127, -1, -1):
        res ^= x * ((y >> i) & 1) # branchless multiplication
        x = x = (x >> 1) ^ ((x & 1) * 0xE1000000000000000000000000000000)
    assert res < (1 << 128)
    return res

class InvalidInputException(Exception):
    """[!] exception raised for invalid inputs to aes_gcm [!]"""
    def __init__(self, message: str):
        super().__init__(message)

class InvalidTagException(Exception):
    """[!] exception raised when the authentication tag is invalid [!]"""
    pass

# galois counter mode with aes-128 and 96-bit IV
class AES_GCM:
    def __init__(self, master_key: bytes):
        self.change_key(master_key)

    def change_key(self, master_key: bytes):
        if len(master_key) * 8 not in (128, 192, 256):
            raise InvalidInputException('master key must be 128, 192, or 256 bits.')

        self.__master_key = master_key
        self.__aes_ecb = AES.new(self.__master_key, AES.MODE_ECB)
        self.__auth_key = bytes_to_long(self.__aes_ecb.encrypt(b'\x00' * 16))

        # precompute the table for multiplication in the finite field
        self.__pre_table = tuple(tuple(gf_2_128_mul(self.__auth_key, j << (8 * i)) 
                                       for j in range(256)) for i in range(16))

        self.prev_init_value = None  # reset previous initial value

    def __times_auth_key(self, val: int) -> int:
        res = 0
        for i in range(16):
            res ^= self.__pre_table[i][val & 0xFF]
            val >>= 8
        return res

    def __ghash(self, aad: bytes, txt: bytes) -> int: # compute ghash
        padded_aad = aad + b'\x00' * (-len(aad) % 16)
        padded_txt = txt + b'\x00' * (-len(txt) % 16)

        tag = 0
        for i in range(0, len(padded_aad + padded_txt), 16):
            tag ^= bytes_to_long((padded_aad + padded_txt)[i:i + 16])
            tag = self.__times_auth_key(tag)
        tag ^= ((8 * len(aad)) << 64) | (8 * len(txt))
        return self.__times_auth_key(tag)

    def encrypt(self, init_value: int, plaintext: bytes, auth_data: bytes = b'') -> tuple:
        if init_value >= (1 << 96):
            raise InvalidInputException('[!] IV should be 96-bit [!]')

        if init_value == self.prev_init_value:
            raise InvalidInputException('[!] IV must not be reused [!]')
        self.prev_init_value = init_value

        padded_plaintext = plaintext + b'\x00' * (-len(plaintext) % 16)
        counter = Counter.new(32, prefix=long_to_bytes(init_value, 12), initial_value=2, allow_wraparound=False)
        aes_ctr = AES.new(self.__master_key, AES.MODE_CTR, counter=counter)
        ciphertext = aes_ctr.encrypt(padded_plaintext)[:len(plaintext)]

        auth_tag = self.__ghash(auth_data, ciphertext) ^ bytes_to_long(
            self.__aes_ecb.encrypt(long_to_bytes((init_value << 32) | 1, 16)))

        assert auth_tag < (1 << 128)
        return ciphertext, auth_tag

    def decrypt(self, init_value: int, ciphertext: bytes, auth_tag: int, auth_data: bytes = b'') -> bytes:
        if init_value >= (1 << 96) or auth_tag >= (1 << 128):
            raise InvalidInputException('[!] IV and tag should be 96-bit and 128-bit respectively []')

        computed_tag = self.__ghash(auth_data, ciphertext) ^ bytes_to_long(
            self.__aes_ecb.encrypt(long_to_bytes((init_value << 32) | 1, 16)))
        if auth_tag != computed_tag:
            raise InvalidTagException

        padded_ciphertext = ciphertext + b'\x00' * (-len(ciphertext) % 16)
        counter = Counter.new(32, prefix=long_to_bytes(init_value, 12), initial_value=2, allow_wraparound=True)
        aes_ctr = AES.new(self.__master_key, AES.MODE_CTR, counter=counter)
        plaintext = aes_ctr.decrypt(padded_ciphertext)[:len(ciphertext)]

        return plaintext
