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

    ttl = int.from_bytes(IP_packet[6:7])
    
    mensaje = IP_packet[7:]

    return {"ip": ip_str, "port": port, "ttl": ttl, "mensaje": mensaje}
    
# pasa a bytes la ip (4b), el puerto (2b) y el mensaje 
def create_packet(parsed_IP_packet):
    partes = parsed_IP_packet["ip"].split('.')
    letras = []
    for x in partes:
        num = int(x)
        letras.append(num)
    ip_bytes = bytes(letras)

    port_bytes = parsed_IP_packet["port"].to_bytes(2)

    ttl_bytes = parsed_IP_packet["ttl"].to_bytes(1)

    return ip_bytes + port_bytes + ttl_bytes + parsed_IP_packet["mensaje"]

# esto es para la parte 8, round robin. se necesita mantener el historial de revisiones, y en vez de implementar una clase,
# es más simple meter un diccionario "global"

# aquí se guarda el índice de la próxima ruta
contadores = {}

def check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str, int]:
    dest_ip_str, dest_port = destination_address

    # junta todos los saltos posibles para este router
    candidatas = []

    # guarda qué área coincidió. iniciado como None pq todavía no se encuentran áreas
    clave = None

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

                # en la primera línea que coincide, fijamos clave como el área de esa línea
                if clave == None:
                    clave = (red_cidr, puerto_inicial, puerto_final)

                # cada línea que coincida y tenga esa misma clave agrega el salto a candidatas. así, si hay otra línea que tb coincide
                # pero con otro rango, no se mezcla con el ciclo. así, se revisa la tabla en orden
                if (red_cidr, puerto_inicial, puerto_final) == clave:
                    candidatas.append((next_hop_IP, int(next_hop_puerto)))

    # si ninguna línea coincide, la lista está vacía y devolvermos None (para la condición de "no hay rutas")
    if not candidatas:
        return None
        #return (next_hop_IP, next_hop_puerto)

    # aquí es donde se maneja el Round Robin en sí.
    # esta primera línea busca el índice guardado para esa área. si es la primera vez, se parte con 0
    i = contadores.get(clave, 0)

    # deja guardado el índice para la próxima vez en el diccionario
    contadores[clave] = i + 1

    # i % len(candidatas) convierte el contador en una posición válida de la lista. el módulo hace que al pasar del último, se vuelva al primero
    return candidatas[i % len(candidatas)]

if __name__ == "__main__":
    router_IP = sys.argv[1]
    router_puerto = int(sys.argv[2])
    rutas = sys.argv[3]

    print(f"{router_IP}, {router_puerto}, {rutas}")

    buff_size = 4096
    
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind((router_IP, router_puerto))
    while True:
        data, addr = router_socket.recvfrom(buff_size)
        parseado = parse_packet(data)
        paquete_ttl = parseado["ttl"]

        if paquete_ttl <= 0:
            print(f"Se recibió paquete {data} con TTL 0")
            continue
        else:
            paquete_ip = parseado["ip"]
            paquete_puerto = parseado["port"]
            paquete_mensaje = parseado["mensaje"]
            if paquete_puerto == router_puerto and paquete_ip == router_IP:
                print(paquete_mensaje.decode())
            else:
                datos_check = check_routes(rutas, (paquete_ip, paquete_puerto))
                if datos_check == None:
                    print(f"No hay rutas hacia {(paquete_ip, paquete_puerto)} para paquete {data}")
                else:
                    salto_ip = datos_check[0]
                    salto_puerto = datos_check[1]
                    parseado["ttl"] -= 1
                    nuevo = create_packet(parseado)
                    print(f"Redirigiendo paquete {nuevo} con destino final {(paquete_ip, paquete_puerto)} desde {(router_IP, router_puerto)} hacia {(salto_ip, salto_puerto)}")
                    router_socket.sendto(nuevo, (salto_ip, salto_puerto))
            
    router_socket.close()


