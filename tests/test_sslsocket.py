# -*- coding: utf-8 -*-

from __future__ import absolute_import

import socket
import ssl
import threading

import pytest

from thriftpy.transport import TTransportException
from thriftpy.transport.sslsocket import TSSLSocket, TSSLServerSocket


def _echo_server(sock):
    c = sock.accept()
    try:
        b = c.read(1024)
        c.write(b)
    except TTransportException:
        pass
    finally:
        c.close()


def _test_socket(server_socket, client_socket):
    server_socket.listen()
    t = threading.Thread(target=_echo_server, args=(server_socket,))
    t.start()

    try:
        buff = b"Hello World!"
        client_socket.open()
        client_socket.write(buff)
        buff2 = client_socket.read(1024)
        assert buff == buff2

    finally:
        t.join(0)
        client_socket.close()
        server_socket.close()


def test_inet_ssl_socket():
    server_socket = TSSLServerSocket(host="localhost", port=12345,
                                     certfile="ssl/server.pem")
    client_socket = TSSLSocket(
        host="localhost", port=12345, socket_timeout=3000,
        cafile="ssl/CA.pem", certfile="ssl/client.crt",
        keyfile="ssl/client.key")

    _test_socket(server_socket, client_socket)


def test_inet6_ssl_socket():
    server_socket = TSSLServerSocket(host="localhost", port=12345,
                                     socket_family=socket.AF_INET6,
                                     certfile="ssl/server.pem")
    client_socket = TSSLSocket(
        host="localhost", port=12345, socket_timeout=3000,
        socket_family=socket.AF_INET6,
        cafile="ssl/CA.pem", certfile="ssl/client.crt",
        keyfile="ssl/client.key")

    _test_socket(server_socket, client_socket)


def test_ssl_hostname_validate():
    server_socket = TSSLServerSocket(host="localhost", port=12345,
                                     certfile="ssl/server.pem")

    # the ssl cert lock hostname to "localhost"
    client_socket = TSSLSocket(
        host="127.0.0.1", port=12345, socket_timeout=3000,
        cafile="ssl/CA.pem", certfile="ssl/client.crt",
        keyfile="ssl/client.key")
    with pytest.raises(ssl.CertificateError):
        _test_socket(server_socket, client_socket)

    # bypass check with validate False
    client_socket = TSSLSocket(
        host="127.0.0.1", port=12345, socket_timeout=3000,
        validate=False,
        cafile="ssl/CA.pem", certfile="ssl/client.crt",
        keyfile="ssl/client.key")
    _test_socket(server_socket, client_socket)


def test_ssl_ciphers():
    server_socket = TSSLServerSocket(host="localhost", port=12345,
                                     certfile="ssl/server.pem")
    client_socket = TSSLSocket(
        host="localhost", port=12345, socket_timeout=3000,
        cafile="ssl/CA.pem", certfile="ssl/client.crt",
        keyfile="ssl/client.key")

    _test_socket(server_socket, client_socket)


def test_persist_ssl_context():
    server_ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    server_ssl_context.load_cert_chain(certfile="ssl/server.pem")
    server_socket = TSSLServerSocket(host="localhost", port=12345,
                                     ssl_context=server_ssl_context)

    client_ssl_context = ssl.create_default_context(cafile="ssl/CA.pem")
    client_ssl_context.load_cert_chain(
        certfile="ssl/client.crt", keyfile="ssl/client.key")
    client_socket = TSSLSocket(host="localhost", port=12345,
                               ssl_context=client_ssl_context)

    _test_socket(server_socket, client_socket)
