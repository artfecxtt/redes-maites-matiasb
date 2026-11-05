import sys
import socket
from router import parse_packet, create_packet

# script parte 5

if __name__ == "__main__":
    headers = sys.argv[1]
    ip_router = sys.argv[2]
    puerto_router = int(sys.argv[3])
    
    ip_destino, puerto_destino, ttl = headers.split(";")
    
    socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with open("texto_prueba.txt", "r", encoding="utf-8") as f:
        for linea in f:
            paquete = create_packet({"ip": ip_destino, "port": int(puerto_destino), "ttl": int(ttl), "mensaje": linea.rstrip("\n").encode()})
            socket_udp.sendto(paquete, (ip_router, puerto_router))
    socket_udp.close()
