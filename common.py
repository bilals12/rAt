import crypto
import os
import socket

class Client:
    def __init__(self, conn: socket.socket, addr: str, IV: int = 0, uid: int = 0):
        """initialize a new client object."""
        self.conn = conn
        self.addr = addr
        self.dh_key = crypto.diffiehellman(self.conn)
        self.GCM = crypto.AES_GCM(self.dh_key)
        self.IV = IV
        self.uid = uid
        self.conn.setblocking(0)

    def send_encrypted(self, plaintext: str) -> int:
        """encrypt plaintext data using the AES-GCM object + send it over the network."""
        ciphertext, tag = self.GCM.encrypt(self.IV, plaintext)
        self.increment_iv()
        return self.send_data(ciphertext, tag)

    def increment_iv(self):
        """increment the IV. this should only be called from the send_encrypted method."""
        self.IV += 2

    def send_data(self, ciphertext: str, tag: str) -> int:
        """send the encrypted data + tag over the network."""
        return self.conn.send(
            crypto.long_to_bytes(self.IV-2, 12) +
            ciphertext +
            crypto.long_to_bytes(tag, 16)

        )

    def recv_encrypted(self) -> str:
    """receive data over the network + decrypt it using the AES-GCM object + return plaintext."""
    encrypted_data = self.recv_data()
    if not encrypted_data:
        return encrypted_data
    IV = crypto.bytes_to_long(encrypted_data[-16:])
    try:
        return self.GCM.decrypt(IV, ciphertext, tag)
    except crypto.InvalidTagException:
        print("[!] data was tampered with or corrupted [!]")
        return ''

    def recv_data(self) -> str:
        """receive data over the network."""
        data = ''
        while True:
            try:
                data += self.conn.recv(4096)
            except socket.error:
                break
        return data

    def recv_file(self, fname: str):
        """receive file over the network and write it locally."""
        if os.path.isfile(fname):
            print(f"[!] {fname} already exists. overwriting [!]")
        data = self.recv_encrypted()
        data = data.split(',')
        data = filter(lambda a: a != '', data)
        data = ''.join(map(chr, map(int, data)))
        with open(fname, 'wb') as f:
            f.write(data)


    def send_file(self, fname: str):
        """read a file + encrypt + send it over network."""
        if not os.path.isfile(fname):
            print(f"[!] {fname} doesn't exist [!]")
            return
        with open(fname, 'rb') as f:
            data = f.read()
        data = ','.join(map(str, map(ord, data)))
        self.send_encrypted(data)
