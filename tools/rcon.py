#!/usr/bin/env python3
"""Мини-клиент RCON для dev-сервера: python3 tools/rcon.py "команда" ["команда" ...]"""
import socket
import struct
import sys


def packet(req_id, kind, body):
    data = struct.pack('<ii', req_id, kind) + body.encode('utf-8') + b'\x00\x00'
    return struct.pack('<i', len(data)) + data


def read(sock):
    size = struct.unpack('<i', sock.recv(4))[0]
    data = b''
    while len(data) < size:
        data += sock.recv(size - len(data))
    req_id, kind = struct.unpack('<ii', data[:8])
    return req_id, data[8:-2].decode('utf-8', 'replace')


def main():
    with socket.create_connection(('127.0.0.1', 25575), timeout=600) as s:
        s.sendall(packet(1, 3, 'celestial-dev'))
        if read(s)[0] == -1:
            sys.exit('rcon: неверный пароль')
        for i, cmd in enumerate(sys.argv[1:], 2):
            s.sendall(packet(i, 2, cmd))
            print(f'> {cmd}\n{read(s)[1]}')


if __name__ == '__main__':
    main()
