import crypto
import os
import socket

class Client:
    def __init__(self, conn: socket.socket, addr: str):
        """initialize a new client object with a connection + address.
        the diffie-hellman key is established and an AES-GCM cipher object is created."""
        self.conn = conn
        self.addr = addr
        self.dh_key = crypto.diffiehellman(self.conn)
        self.GCM = crypto.AES_GCM(self.dh_key)
        self.conn.setblocking(0)

    def send_encrypted(self, plaintext: bytes) -> int:
        """encrypt plaintext data using the AES-GCM object + send it over the network."""
        IV = os.urandom(12)  # Generating a random IV for each message
        ciphertext, tag = self.GCM.encrypt(IV, plaintext)
        return self.send_data(IV, ciphertext, tag)

    def send_data(self, IV: bytes, ciphertext: bytes, tag: bytes) -> int:
        """Send the IV, encrypted data, and tag over the network."""
        return self.conn.send(IV + ciphertext + tag)

    def recv_encrypted(self) -> str:
        """receive data over the network + decrypt it using the AES-GCM object + return plaintext."""
        encrypted_data = self.recv_data()
        if not encrypted_data:
            return ''
        try:
            iv = encrypted_data[:12]
            tag = encrypted_data[-16:]
            ciphertext = encrypted_data[12:-16]
            return self.GCM.decrypt(iv, ciphertext, tag).decode()
        except crypto.InvalidTagException:
            print("[!] data was tampered with or corrupted [!]")
            return ''

    def recv_data(self) -> bytes:
        """receive data over the network."""
        data = b''
        while True:
            try:
                packet = self.conn.recv(4096)
                if not packet:
                    break
                data += packet
            except socket.error:
                break
        return data

    def recv_file(self, fname: str):
        """receive a file over the network + write it."""
        if os.path.isfile(fname):
            print(f"[!] {fname} already exists. overwriting [!]")
        with open(fname, 'wb') as f:
            f.write(self.recv_encrypted())

    def send_file(self, fname: str):
        """read a file + encrypt it + send it over the network."""
        if not os.path.isfile(fname):
            print(f"[!] {fname} doesn't exist [!]")
            return
        with open(fname, 'rb') as f:
            self.send_encrypted(f.read())
