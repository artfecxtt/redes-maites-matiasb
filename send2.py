import sys
import socket
from router2 import parse_packet, create_packet

# script parte 5

if __name__ == "__main__":
    ip_router_final = sys.argv[1]
    puerto_router_final = int(sys.argv[2])
    mensaje_str = sys.argv[3]
    
    ip_envio = sys.argv[4]
    port_envio = int(sys.argv[5])

    parsed_packet = {"ip": ip_router_final, "port": puerto_router_final, "mensaje": mensaje_str.encode('utf-8')}

    packet_bytes = create_packet(parsed_packet)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    client_socket.sendto(packet_bytes, (ip_envio, port_envio))
    print(f"{ip_envio}:{port_envio}); destino ({ip_router_final}:{puerto_router_final}, mensaje {mensaje_str}")

    client_socket.close()
