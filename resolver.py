import binascii
import socket

# esta función toma un mensaje DNS junto al offset dado y extrae el nombre, tipo, 
# clase, ttl, rdlengt y data en un diccionario de la sección que se trabaja
def parse_record(message, offset):
    baits_name = b""
    while offset < len(message):
        byte_actual = message[offset]
        if byte_actual >= 0xC0:
            baits_name += message[offset:offset+2]
            offset += 2
            break
        elif byte_actual == 0x00:
            baits_name += message[offset:offset+1]
            offset += 1
            break
        else:
            longitud = byte_actual
            baits_name += message[offset:offset + 1 + longitud]
            offset += 1 + longitud

    rtype = message[offset:offset+2]
    offset += 2
    rclass = message[offset:offset+2]
    offset += 2
    rttl = message[offset:offset+4]
    offset += 4
    rdlength = message[offset:offset+2]
    offset += 2

    len_rdata = int.from_bytes(rdlength, 'big')
    rdata = message[offset:offset+len_rdata]
    offset += len_rdata

    return {
        "NAME": baits_name,
        "TYPE": rtype,
        "CLASS": rclass,
        "TTL": rttl,
        "RDLENGTH": rdlength,
        "RDATA": rdata
    }, offset

# esta función toma un mensaje DNS y lo transforma a un diccionario para que sea manejable
def parse_dns_message(message):
    dicc = {}
    baits = b""

    # guarda la ID en el diccionario
    for k in range(2):
        baits+=message[k:k+1]
    dicc["ID"]= baits
    baits=b""
    ultimo=2
    
    # guarda las flags en el diccionario
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["flags"]=baits
    baits=b""
    ultimo+=2
    
    # guarda el QDCOUNT
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["QDCOUNT"]= baits
    baits=b""
    ultimo+=2
    
    # guarda el ANCOUNT
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["ANCOUNT"]= baits
    baits=b""
    ultimo+=2
    
    # guarda el NSCOUNT
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["NSCOUNT"]= baits
    baits=b""
    ultimo+=2
    
    # guarda el ARCOUNT
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["ARCOUNT"]= baits
    baits=b""
    ultimo+=2
    
    # guarda el QNAME
    for k in range(ultimo, len(message)):
        if message[k:k+1] == b"\x00":
            ultimo = k+1
            dicc["QNAME"] = baits
            baits = b""
            break
        baits+=message[k:k+1]
        
    # guarda el QTYPE
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["QTYPE"]= baits
    baits=b""
    ultimo+=2
    
    # guarda el QCLASS
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["QCLASS"]= baits
    baits=b""
    ultimo+=2
    
    #SECCIÓN ANSWER
    # inicia una lista dentro del diccionario para guardar toda la información 
    # respecto a la sección de answer
    dicc["Answers"] = []
    ancount = int.from_bytes(dicc["ANCOUNT"])
    for _ in range(ancount):
        # se parsea según la estructura dada en el parse_record
        rec, ultimo = parse_record(message, ultimo)
        dicc["Answers"].append(rec)
    if ancount > 0:
        # si es que indica en ancount, se guarda el type y data de la sección
        dicc["ans_TYPE"] = dicc["Answers"][0]["TYPE"]
        dicc["ans_RDATA"] = dicc["Answers"][0]["RDATA"]
    
    #SECCIÓN AUTHORITY
    # inicia una lista dentro del diccionario para guardar toda la información 
    # respecto a la sección de authority
    dicc["Authorities"] = []
    nscount = int.from_bytes(dicc["NSCOUNT"], 'big')
    for _ in range(nscount):
        # se parsea según la estructura dada en el parse_record
        rec, ultimo = parse_record(message, ultimo)
        dicc["Authorities"].append(rec)
    if nscount > 0:
        # si es que indica en nscount, se guarda el type y data de la sección
        dicc["auth_TYPE"] = dicc["Authorities"][0]["TYPE"]
        dicc["auth_RDATA"] = dicc["Authorities"][0]["RDATA"]
    
    #SECCIÓN ADDITONIALS 
    # inicia una lista dentro del diccionario para guardar toda la información 
    # respecto a la sección de additionals
    dicc["Additionals"] = []
    arcount = int.from_bytes(dicc["ARCOUNT"], 'big')
    for _ in range(arcount):
        # se parsea según la estructura dada en el parse_record
        rec, ultimo = parse_record(message, ultimo)
        dicc["Additionals"].append(rec)
    if arcount > 0:
        # si es que indica en nscount, se guarda el type y data de la sección
        dicc["add_TYPE"] = dicc["Additionals"][0]["TYPE"]
        dicc["add_RDATA"] = dicc["Additionals"][0]["RDATA"]

    return dicc

root_ip = "198.41.0.4"
cache=[]
historial_consultas = []

# esta función recibe el mensaje de query en bytes obtenido desde el cliente. envía un mensaje query a la ip raíz y trata si esta es una delegación a otro NS
def resolver(mensaje_consulta: bytes, ip_addr=root_ip) -> bytes:
    # se obtiene el dominio del mensaje que llegó
    parsed_msg = parse_dns_message(mensaje_consulta)
    dominio = parsed_msg.get("QNAME", b"\x00\x00").decode()

    # si está en la consulta inicial (ip_addr == root_ip), verificar caché
    if ip_addr == root_ip:
        if len(historial_consultas) == 20:
            historial_consultas.pop(0)
        historial_consultas.append(dominio)

        conteo = {x: historial_consultas.count(x) for x in set(historial_consultas)}
        top_3 = [item[0] for item in sorted(conteo.items(), key=lambda item: item[1], reverse=True)[:3]]

        # si está en el top 3 se supone que la respuesta ya está guardada
        if dominio in top_3:
            match = [resp for d, resp in cache if d == dominio]
            if match:
                print(f"Utilizando caché para {dominio}")
                # Reemplazamos los primeros 2 bytes (ID) para coincidir con la query actual
                return mensaje_consulta[:2] + match[-1][2:]

    # si no estaba en caché, se crea el socket
    print("Creando socket.................................")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        print(f"Enviando query a {ip_addr}.............................")
        sock.sendto(mensaje_consulta, (ip_addr, 53))
        respuesta, _ = sock.recvfrom(4096)
    except Exception:
        return b""
    finally:
        sock.close()
        
    parsed = parse_dns_message(respuesta)

    # si se tiene la respuesta final, se guarda en el caché
    for ans in parsed.get("Answers", []):
        if ans["TYPE"] == b"\x00\x01":
            if len(cache) == 20:
                cache.pop(0)
            cache.append((dominio, respuesta))
            return respuesta
            
    # se delega
    if int.from_bytes(parsed.get("NSCOUNT", b"\x00\x00"), 'big') > 0:
        siguiente_ip = None

        # se busca la ip tipo A en additional
        for add in parsed.get("Additionals", []):
            if add["TYPE"] == b"\x00\x01":
                rdata = add["RDATA"]
                siguiente_ip = f"{rdata[0]}.{rdata[1]}.{rdata[2]}.{rdata[3]}"
                break

        # si no está en additionals, se ve en authorities
        if siguiente_ip is None and parsed.get("Authorities", []):
            ns_record = parsed["Authorities"][0]
            ns_name_bytes = ns_record.get("RDATA", b"")
            
            # se construye la query
            header = mensaje_consulta[:2] + b"\x01 \x00\x01\x00\x00\x00\x00\x00\x00"
            query_ns = header + ns_name_bytes + b"\x00\x01\x00\x01"
            
            resp_ns = resolver(query_ns, root_ip)
            parsed_ns = parse_dns_message(resp_ns)
            
            for ans in parsed_ns.get("Answers", []):
                if ans["TYPE"] == b"\x00\x01":
                    rdata = ans["RDATA"]
                    siguiente_ip = f"{rdata[0]}.{rdata[1]}.{rdata[2]}.{rdata[3]}"
                    break

        # si se encuentra la ip se sigue con la recursión
        if siguiente_ip:
            if parsed.get("Authorities", []):
                raiz = parsed.get("Authorities", [])[0]["NAME"]
                print(f"Consultando {dominio} a {raiz} con la dirección IP {siguiente_ip}")
            else:
                print(f"Consultando {dominio} a '.' con la dirección IP {siguiente_ip}")
            return resolver(mensaje_consulta, siguiente_ip)
    
    #cualquier otro caso se ignora
    return b""
 
if __name__ == "__main__":
    end_qname = b"\x00"
    buff_size = 4096

    # Socket no orientado a conexión
    dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    dgram_socket.bind(('localhost', 8000))
    
    #message, address = dgram_socket.recvfrom(buff_size)
    #print(message)
    
    while True:
        # Recibir mensajes. Este método nos entrega el mensaje junto a la dirección de origen del mensaje
        message, address = dgram_socket.recvfrom(buff_size)
        print(message)
        print(len(message))
        
        resolve = resolver(message)
        
        print(resolve)
        
        if resolve:
            dgram_socket.sendto(resolve, address)

       
        message2=parse_dns_message(message)
        print(message2)
         
        # Enviar mensajes. Este método debe especificar la dirección a la que se va a enviar el mensaje
        #dgram_socket.sendto(message, address)
        
