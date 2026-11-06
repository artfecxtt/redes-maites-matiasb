import socket
import time
from router import create_packet, fragment_IP_packet

def ejecutar_test():
    IP_DESTINO = "127.0.0.1"
    PUERTO_DESTINO = 8885
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    msg1 = b"MENSAJE_A_Primer paquete fragmentado con ID 100"
    msg2 = b"MENSAJE_B_Segundo paquete fragmentado con ID 200"

    pkt1 = create_packet({
        "ip": IP_DESTINO, "port": PUERTO_DESTINO, "ttl": 10,
        "id": 100, "offset": 0, "tamaño": len(msg1), "flag": 0, "mensaje": msg1
    })

    pkt2 = create_packet({
        "ip": IP_DESTINO, "port": PUERTO_DESTINO, "ttl": 10,
        "id": 200, "offset": 0, "tamaño": len(msg2), "flag": 0, "mensaje": msg2
    })

    frags_ID_100 = fragment_IP_packet(pkt1, MTU=60)
    frags_ID_200 = fragment_IP_packet(pkt2, MTU=60)

    print(f"Paquete 1 (ID 100) generado con {len(frags_ID_100)} fragmentos.")
    print(f"Paquete 2 (ID 200) generado con {len(frags_ID_200)} fragmentos.")
    print("-" * 50)

    print("\n--- CASO 1: Enviando ID 100 EN ORDEN ---")
    for f in frags_ID_100:
        client_socket.sendto(f, (IP_DESTINO, PUERTO_DESTINO))
        time.sleep(0.05)

    time.sleep(1)

    print("\n--- CASO 2: Enviando ID 101 EN DESORDEN ---")
    pkt1_alt = create_packet({
        "ip": IP_DESTINO, "port": PUERTO_DESTINO, "ttl": 10,
        "id": 101, "offset": 0, "tamaño": len(msg1), "flag": 0, "mensaje": msg1
    })
    frags_desorden = fragment_IP_packet(pkt1_alt, MTU=60)
    frags_desorden_reversed = list(reversed(frags_desorden))

    for f in frags_desorden_reversed:
        client_socket.sendto(f, (IP_DESTINO, PUERTO_DESTINO))
        time.sleep(0.05)

    time.sleep(1)

    print("\n--- CASO 3: Enviando INTERCALANDO ID 100 e ID 200 ---")
    intercalados = []
    max_len = max(len(frags_ID_100), len(frags_ID_200))
    for i in range(max_len):
        if i < len(frags_ID_100):
            intercalados.append(frags_ID_100[i])
        if i < len(frags_ID_200):
            intercalados.append(frags_ID_200[i])

    for f in intercalados:
        client_socket.sendto(f, (IP_DESTINO, PUERTO_DESTINO))
        time.sleep(0.05)

    client_socket.close()

if __name__ == "__main__":
    ejecutar_test()
