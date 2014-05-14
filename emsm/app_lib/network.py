#!/usr/bin/python3
# Benedikt Schmitt <benedikt@benediktschmitt.de>


import socket
import random


__all__ = ["get_unused_port"]


_FOUND_PORTS = list()
def get_unused_port(min_port, max_port, interface=""):
    """
    Returns an unused port in the intervall *[min_, max_]* on the
    *interface*.
    """
    global _FOUND_PORTS
    
    if max_port > 65535:
        raise ValueError("max_port has to be less than 65535")    
    if min_port < 0:
        raise ValueError("min_port has to be greater or equal to 0")

    while True:
        port = random.randint(min_port, max_port)
        if port in _FOUND_PORTS:
            continue
        
        # Check the port.
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)        
            try:
                s.bind((interface, port))
            except OSError as error:
                pass
            else:
                _FOUND_PORTS.append(port)
                return port
    return None


if __name__=="__main__":
    port = get_unused_port(1000, 20000, "127.0.0.1")
    
    socket = socket.socket()
    socket.bind(("127.0.0.1", port))
    socket.listen(1)
    socket.close()
