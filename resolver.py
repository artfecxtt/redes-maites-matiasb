import binascii
import socket


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

    for k in range(2):
        baits+=message[k:k+1]
    dicc["ID"]= baits
    baits=b""
    ultimo=2
    
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["flags"]=baits
    baits=b""
    ultimo+=2
    
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["QDCOUNT"]= baits
    baits=b""
    ultimo+=2
    
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["ANCOUNT"]= baits
    baits=b""
    ultimo+=2
    
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["NSCOUNT"]= baits
    baits=b""
    ultimo+=2
    
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["ARCOUNT"]= baits
    baits=b""
    ultimo+=2
    
    for k in range(ultimo, len(message)):
        if message[k:k+1] == b"\x00":
            ultimo = k+1
            dicc["QNAME"] = baits
            baits = b""
            break
        baits+=message[k:k+1]
        
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["QTYPE"]= baits
    baits=b""
    ultimo+=2
    
    for k in range(ultimo, ultimo + 2):
        baits+=message[k:k+1]
    dicc["QCLASS"]= baits
    baits=b""
    ultimo+=2
    
    #SECCIÓN ANSWER
    dicc["Answers"] = []
    ancount = int.from_bytes(dicc["ANCOUNT"], 'big')
    for _ in range(ancount):
        rec, ultimo = parse_record(message, ultimo)
        dicc["Answers"].append(rec)
    if ancount > 0:
        dicc["ans_TYPE"] = dicc["Answers"][0]["TYPE"]
        dicc["ans_RDATA"] = dicc["Answers"][0]["RDATA"]
    
    #SECCIÓN AUTHORITY
    dicc["Authorities"] = []
    nscount = int.from_bytes(dicc["NSCOUNT"], 'big')
    for _ in range(nscount):
        rec, ultimo = parse_record(message, ultimo)
        dicc["Authorities"].append(rec)
    if nscount > 0:
        dicc["auth_TYPE"] = dicc["Authorities"][0]["TYPE"]
        dicc["auth_RDATA"] = dicc["Authorities"][0]["RDATA"]
    
    #SECCIÓN ADDITONIALS 
    dicc["Additionals"] = []
    arcount = int.from_bytes(dicc["ARCOUNT"], 'big')
    for _ in range(arcount):
        rec, ultimo = parse_record(message, ultimo)
        dicc["Additionals"].append(rec)
    if arcount > 0:
        dicc["add_TYPE"] = dicc["Additionals"][0]["TYPE"]
        dicc["add_RDATA"] = dicc["Additionals"][0]["RDATA"]

    return dicc

root_ip = "198.41.0.4"

# esta función recibe el mensaje de query en bytes obtenido desde el cliente. envía un mensaje query a la ip raíz y trata si esta es una delegación a otro NS
def resolver(mensaje_consulta: bytes, ip_addr=root_ip) -> bytes:
    print("Creando socket.................................")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(4.0)
    try:
        print(f"Enviando query a {ip_addr}.............................")
        sock.sendto(mensaje_consulta, (ip_addr, 53))
        respuesta, _ = sock.recvfrom(4096)
    except Exception:
        return b""
    finally:
        sock.close()

    
    parsed = parse_dns_message(respuesta)

    for ans in parsed.get("Answers", []):
        if ans["TYPE"] == b"\x00\x01":
            return respuesta

    if int.from_bytes(parsed.get("NSCOUNT", b"\x00\x00"), 'big') > 0:
        for add in parsed.get("Additionals", []):
            if add["TYPE"] == b"\x00\x01":
                rdata = add["RDATA"]
                siguiente_ip = f"{rdata[0]}.{rdata[1]}.{rdata[2]}.{rdata[3]}"
                dominio = parsed.get("QNAME", b"\x00\x00").decode()
                if parsed.get("Authority", []) != []:
                    raiz = parsed.get("Authority", [])[0]["NAME"]
                    print(f"Consultando {dominio} a {raiz} con la dirección IP {siguiente_ip}")
                else:
                    print(f"Consultando {dominio} a '.' con la dirección IP {siguiente_ip}")
                return resolver(mensaje_consulta, siguiente_ip)

    return b""


#def send_dns_message(address, port):
#    # Encabezado con ID 0 (00 00 en hexadecimal), preguntamos por example.com
#    header = "00 00 00 00 00 01 00 00 00 00 00 00 ".replace(" ","")
#    data = "07 65 78 61 6D 70 6C 65 03 63 6F 6D 00 00 01 00 01".replace(" ","")
#    message = header + data
    # Lo escribimos así para que se entendiera, lo concatenamos para hacer la cadena de hexadecimales
#    server_address = (address, port)
#    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#    try:
        # usamos binascii para pasar el mensaje al formato apropiado
#        binascii_msg = binascii.unhexlify(message)
        # y lo enviamos
#        sock.sendto(binascii_msg, server_address)
        # En data quedará la respuesta a nuestra consulta
#        data, _ = sock.recvfrom(4096)
#    finally:
#        sock.close()
    # Ojo que los datos de la respuesta van en hexadecimal, no en binario
#    return binascii.hexlify(data).decode("utf-8")

#print (send_dns_message("1.1.1.1", 53))
 
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
        
