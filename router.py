import sys
import socket

#class Packet:
#    def __init__(self, dest_ip: str, dest_port: int, mensaje: bytes):
#        self.dest_ip = dest_ip
#        self.dest_port = dest_port
#        self.mensaje = mensaje

    # pasa a bytes la ip (4b), el puerto (2b) y el mensaje
#    def to_bytes(self):
#        partes = self.dest_ip.split('.')
#        letras = []
#        for x in partes:
#            nro = int(x)
#            letras.append(numero)
            
#        ip_bytes = bytes(letras)

#        port_bytes = self.dest_port.to_bytes(2)

#        return ip_bytes + port_bytes + self.payload

    # pasa la tira de bytes a un paquete
#    def from_bytes(raw_bytes: bytes):
#        if len(raw_bytes) < 6:
#            print("debe tener mínimo 6 bytes")
#            return

#       a, b, c, d = raw_bytes[0], raw_bytes[1], raw_bytes[2], raw_bytes[3]
#        dest_ip = f"{a}.{b}.{c}.{d}"

#        dest_port = int.from_bytes(raw_bytes[4:6])

#        mensaje = raw_bytes[6:]

#        return Packet(dest_ip, dest_port, mensaje)
      
# pasa de bytes a diccionario el paquete
def parse_packet(IP_packet: bytes):
    ip_str = f"{IP_packet[0]}.{IP_packet[1]}.{IP_packet[2]}.{IP_packet[3]}"

    port = int.from_bytes(IP_packet[4:6])

    mensaje = IP_packet[6:]

    return {"ip": ip_str, "port": port, "mensaje": mensaje}
    
# pasa a bytes la ip (4b), el puerto (2b) y el mensaje 
def create_packet(parsed_IP_packet):
    partes = parsed_IP_packet["ip"].split('.')
    letras = []
    for x in partes:
        num = int(x)
        letras.append(num)
    ip_bytes = bytes(letras)

    port_bytes = parsed_IP_packet["port"].to_bytes(2)

    return ip_bytes + port_bytes + parsed_IP_packet["mensaje"]

def check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str, int]:
    dest_ip_str, dest_port = destination_address

    with open(routes_file_name, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            partes = line.split(" ")
            
            # minimo 5 cosas
            if len(partes) < 5:
                continue

            try:
                red_cidr = partes[0]
                puerto_inicial = int(partes[1])
                puerto_final = int(partes[2])
                next_hop_IP = partes[3]
                next_hop_puerto = int(partes[4])
            except ValueError:
                # por si hay encabezados o texto suelto o algo así, por si acaso más q nada
                continue

            base_ip = red_cidr.split('/')[0]
            if (dest_ip_str == base_ip) and (puerto_inicial <= dest_port <= puerto_final):
                return (next_hop_IP, next_hop_puerto)

    return None

if __name__ == "__main__":
    router_IP = sys.argv[1]
    router_puerto = sys.argv[2]
    rutas = sys.argv[3]

    print(f"{router_IP}, {router_puerto}, {rutas}")

    buff_size = 4096
    
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind((router_ip, router_port))
    while True:
        data, addr = router_socket(recvfrom(buff_size))
    
    router_socket.close()


