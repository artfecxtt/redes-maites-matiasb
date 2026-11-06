import sys
import socket
    
# pasa de bytes a diccionario el paquete
def parse_packet(IP_packet: bytes):
    ip_str = f"{IP_packet[0]}.{IP_packet[1]}.{IP_packet[2]}.{IP_packet[3]}"

    port = int.from_bytes(IP_packet[4:6])

    ttl = int.from_bytes(IP_packet[6:7])
    
    #se le van a dar 2 bytes a la id
    ide = int.from_bytes(IP_packet[7:9])
    
    #se le van a dat 3 bytes al offset
    offset = int.from_bytes(IP_packet[9:12])
    
    size = int.from_bytes(IP_packet[12:16])
    
    flag = int.from_bytes(IP_packet[16:17])
    
    # el header queda con tamaño fijo de 17
    
    mensaje = IP_packet[17:]

    return {"ip": ip_str, "port": port, "ttl": ttl, "id": ide, "offset": offset, "tamaño": size, "flag":flag, "mensaje": mensaje}
    
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
    
    id_bytes = parsed_IP_packet["id"].to_bytes(2)
    
    offset_bytes = parsed_IP_packet["offset"].to_bytes(3)
    
    size_bytes = parsed_IP_packet["tamaño"].to_bytes(4)
    
    flag_bytes = parsed_IP_packet["flag"].to_bytes(1)

    return ip_bytes + port_bytes + ttl_bytes + id_bytes + offset_bytes + size_bytes + flag_bytes + parsed_IP_packet["mensaje"]

# esto es para la parte 8, round robin. se necesita mantener el historial de revisiones, y en vez de implementar una clase,
# es más simple meter un diccionario "global"

# aquí se guarda el índice de la próxima ruta
contadores = {}

def check_routes(routes_file_name: str, destination_address: tuple[str, int]):
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
            if len(partes) < 6:
                continue

            try:
                red_cidr = partes[0]
                puerto_inicial = int(partes[1])
                puerto_final = int(partes[2])
                next_hop_IP = partes[3]
                next_hop_puerto = int(partes[4])
                mtu = int(partes[5])
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
                    candidatas.append([next_hop_IP, int(next_hop_puerto), mtu])

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
    next_hop = candidatas[i % len(candidatas)]
    next_ip, next_port, hop_mtu = next_hop
    
    #devuelve una tupla con el primer coso siendo otra tupla con la ip y puerto del next hop, y en la 2da parte el mtu
    return ((next_ip, next_port), hop_mtu)
    
def fragment_IP_packet(IP_packet, MTU):
    size_packet = len(IP_packet)
    fragmentos = []
    
    if size_packet <= MTU:
        return [IP_packet]
    else:
        max_msg = MTU - 17 #17 es el tamaño fijo del header
        pack_parsed = parse_packet(IP_packet)
        if pack_parsed["tamaño"] >= max_msg:
            msg = pack_parsed["mensaje"]
            trozos = (pack_parsed["tamaño"] + max_msg - 1)//max_msg
            for i in range(trozos):
                frag_msg = msg[max_msg*i:max_msg*(i+1)]
                if i == trozos - 1:
                    flag = 0
                else:
                    flag = 1
                
                frag = {"ip": pack_parsed["ip"], "port": pack_parsed["port"], "ttl": pack_parsed["ttl"], 
                "id": pack_parsed["id"], "offset": pack_parsed["offset"] + max_msg*i, "tamaño": len(frag_msg), "flag": flag, "mensaje": frag_msg}
                frag_bytes = create_packet(frag)
                fragmentos.append(frag_bytes)
        return fragmentos
        
def reassemble_IP_packet(fragment_list):
    tot_msg = b""    
    
    if len(fragment_list) == 1:
        packet = parse_packet(fragment_list[0])
        if packet["offset"] == 0 and packet["flag"] == 0:
            return fragment_list[0]
        else:
            return None
    else:
        # ordenamos la lista de menor a mayor por offset
        fragmentos_ordenados = sorted(fragment_list, key=lambda packet: parse_packet(packet)["offset"])
        
        primero = parse_packet(fragmentos_ordenados[0])
        if primero["offset"] != 0:
            return None
            
        ultimo = parse_packet(fragmentos_ordenados[-1])
        if ultimo["flag"] != 0:
            return None 
        
        for pkt in fragmentos_ordenados:
            parsed = parse_packet(pkt)
            
            if parsed["offset"] != len(tot_msg):
                return None
            
            tot_msg+= parsed["mensaje"]
            
        base = parse_packet(fragment_list[0])
        dicc = {"ip":base["ip"], "port": base["port"], "ttl": base["ttl"], "id": base["id"], "offset": 0, "tamaño": len(tot_msg), "flag": 0, "mensaje": tot_msg}
        
        return create_packet(dicc)
         

if __name__ == "__main__":
    router_IP = sys.argv[1]
    router_puerto = int(sys.argv[2])
    rutas = sys.argv[3]

    print(f"{router_IP}, {router_puerto}, {rutas}")

    buff_size = 4096
    
    frag_recibidos = {}
    
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind((router_IP, router_puerto))
    while True:
        data, addr = router_socket.recvfrom(buff_size)
        parseado = parse_packet(data)
        paquete_ttl = parseado["ttl"]
        paquete_id = parseado["id"]

        if paquete_ttl <= 0:
            print(f"Se recibió paquete {data} con TTL 0")
            continue
        else:
            paquete_ip = parseado["ip"]
            paquete_puerto = parseado["port"]
            paquete_mensaje = parseado["mensaje"]
            if paquete_puerto == router_puerto and paquete_ip == router_IP:
                #print(paquete_mensaje.decode())
                
                if paquete_id not in frag_recibidos:
                    frag_recibidos[paquete_id] = []
                
                frag_recibidos[paquete_id].append(data)
                
                pkt_reasmb = reassemble_IP_packet(frag_recibidos[paquete_id])
                
                if pkt_reasmb is not None:
                    parsed = parse_packet(pkt_reasmb)
                    print(parsed["mensaje"].decode())

            else:
                datos_check = check_routes(rutas, (paquete_ip, paquete_puerto))
                if datos_check == None:
                    print(f"No hay rutas hacia {(paquete_ip, paquete_puerto)} para paquete {data}")
                else:
                    salto = datos_check[0]
                    mtu = datos_check[1]
                    
                    salto_ip = salto[0]
                    salto_puerto = salto[1]
                    parseado["ttl"] -= 1
                    
                    nuevo = create_packet(parseado)
                    
                    fragmentos = fragment_IP_packet(nuevo, mtu)
                    
                    for frag in fragmentos:
                        print(f"Redirigiendo fragmento {frag} con destino final {(paquete_ip, paquete_puerto)} desde {(router_IP, router_puerto)} hacia {(salto_ip, salto_puerto)}")
                        router_socket.sendto(frag, (salto_ip, salto_puerto))
            
    router_socket.close()


