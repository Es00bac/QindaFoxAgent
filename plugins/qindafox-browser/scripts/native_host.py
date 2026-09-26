#!/usr/bin/env python3
"""Firefox native messaging ↔ private Unix socket. No listening TCP port."""
import json
import os
from pathlib import Path
import queue
import socket
import struct
import sys
import threading
import uuid

MAX_FRAME = 8 * 1024 * 1024


def runtime_dir():
    root = Path(os.environ.get('XDG_RUNTIME_DIR', f'/tmp/qindafox-agent-{os.getuid()}')) / 'qindafox-agent'
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise RuntimeError('Unsafe runtime directory permissions/owner')
    return root


def read_exact(stream, size):
    result = bytearray()
    while len(result) < size:
        chunk = stream.read(size - len(result))
        if not chunk:
            raise EOFError('Browser disconnected')
        result.extend(chunk)
    return bytes(result)


def read_native(stream):
    length = struct.unpack('=I', read_exact(stream, 4))[0]
    if not 0 < length <= MAX_FRAME:
        raise ValueError('Native frame too large')
    return json.loads(read_exact(stream, length))


def write_native(stream, value):
    body = json.dumps(value, separators=(',', ':')).encode()
    # Firefox caps native application → extension messages at 1 MiB.
    if len(body) > 1024 * 1024:
        raise ValueError('Command too large')
    stream.write(struct.pack('=I', len(body)) + body)
    stream.flush()


def main():
    os.umask(0o077)
    path = runtime_dir() / f'{os.getpid()}.sock'
    pending, lock, output_lock = {}, threading.Lock(), threading.Lock()
    server = socket.socket(socket.AF_UNIX)
    server.bind(str(path))
    server.listen(16)

    def reader():
        try:
            while True:
                reply = read_native(sys.stdin.buffer)
                with lock:
                    target = pending.get(reply.get('id'))
                if target:
                    target.put(reply)
        except (EOFError, ValueError, OSError):
            path.unlink(missing_ok=True)
            os._exit(0)

    def handle(conn):
        ident = uuid.uuid4().hex
        try:
            if hasattr(socket, 'SO_PEERCRED'):
                _, uid, _ = struct.unpack('3i', conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                if uid != os.getuid():
                    return
            conn.settimeout(25)
            with conn.makefile('rb') as stream:
                line = stream.readline(1024 * 1024 + 1)
                if not line.endswith(b'\n') or len(line) > 1024 * 1024:
                    raise ValueError('Invalid request frame')
                request = json.loads(line)
                if not isinstance(request, dict) or not isinstance(request.get('method'), str):
                    raise ValueError('Invalid request')
                request['id'] = ident
                target = queue.Queue(maxsize=1)
                with lock:
                    pending[ident] = target
                with output_lock:
                    write_native(sys.stdout.buffer, request)
                try:
                    result = target.get(timeout=20)
                except queue.Empty:
                    result = {'error': {'message': 'BROWSER_TIMEOUT: action outcome unknown; inspect before retry'}}
                conn.sendall(json.dumps(result).encode() + b'\n')
        except (ValueError, OSError, TypeError) as e:
            try:
                conn.sendall(json.dumps({'error': {'message': str(e)}}).encode() + b'\n')
            except OSError:
                pass
        finally:
            with lock:
                pending.pop(ident, None)
            conn.close()

    threading.Thread(target=reader, daemon=True).start()
    try:
        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle, args=(conn,), daemon=True).start()
    finally:
        server.close()
        path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
