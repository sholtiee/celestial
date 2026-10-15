#!/usr/bin/env python3
"""Мини-клиент RCON для dev-сервера: python3 tools/rcon.py "команда" ["команда" ...]"""
import re
import socket
import time
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
        cmds = []
        for a in sys.argv[1:]:
            # @файл: команды построчно; "#sleep N" ждёт N секунд; печатаются только ответы-ошибки
            cmds += [(l.strip(), True) for l in open(a[1:], encoding='utf-8') if l.strip()] if a.startswith('@') else [(a, False)]
        for i, (cmd, quiet) in enumerate(cmds, 2):
            if cmd.startswith('#sleep '):
                time.sleep(float(cmd.split()[1]))
                continue
            s.sendall(packet(i, 2, cmd))
            out = read(s)[1]
            if not quiet or re.search(r'Unknown|Expected|Incorrect|Could not|Invalid|Cannot|rror|not loaded|Failed|No ', out):
                print(f'> {cmd[:160]}\n{out}')


if __name__ == '__main__':
    main()
