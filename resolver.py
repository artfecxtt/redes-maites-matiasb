import binascii
import socket

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
    if int.from_bytes(dicc["ANCOUNT"]) > 0:
        for k in range(ultimo, len(message)):
            if message[k:k+1] == b"\x00":
                ultimo = k+1
                dicc["ans_NAME"] = baits
                baits = b""
                break
            baits+=message[k:k+1]
            
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["ans_TYPE"]= baits
        baits=b""
        ultimo+=2
            
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["ans_CLASS"]= baits
        baits=b""
        ultimo+=2
        
        for k in range(ultimo, ultimo + 4):
            baits+=message[k:k+1]
        dicc["ans_TTL"]= baits
        baits=b""
        ultimo+=4
        
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["ans_RDLENGTH"]= baits
        baits=b""
        ultimo+=2
        
        for k in range(ultimo, ultimo+int.from_bytes(dicc["ans_RDLENGTH"])):
            baits+=message[k:k+1]
        dicc["ans_RDATA"]= baits
        baits=b""
        ultimo+=int.from_bytes(dicc["ans_RDLENGTH"])
    
    #SECCIÓN AUTHORITY
    if int.from_bytes(dicc["NSCOUNT"]) > 0:
        for k in range(ultimo, len(message)):
            if message[k:k+1] == b"\x00":
                ultimo = k+1
                dicc["auth_NAME"] = baits
                baits = b""
                break
            baits+=message[k:k+1]
            
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["auth_TYPE"]= baits
        baits=b""
        ultimo+=2
            
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["auth_CLASS"]= baits
        baits=b""
        ultimo+=2
        
        for k in range(ultimo, ultimo + 4):
            baits+=message[k:k+1]
        dicc["auth_TTL"]= baits
        baits=b""
        ultimo+=4
        
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["auth_RDLENGTH"]= baits
        baits=b""
        ultimo+=2
        
        for k in range(ultimo, ultimo+int.from_bytes(dicc["auth_RDLENGTH"])):
            baits+=message[k:k+1]
        dicc["auth_RDATA"]= baits
        baits=b""
        ultimo+=int.from_bytes(dicc["auth_RDLENGTH"])
    
    #SECCIÓN ADDITONIALS 
    if int.from_bytes(dicc["ARCOUNT"]) > 0:
    
        for k in range(ultimo, len(message)):
            if message[k:k+1] == b"\x00":
                ultimo = k+1
                dicc["add_NAME"] = baits
                baits = b""
                break
            baits+=message[k:k+1]
            
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["add_TYPE"]= baits
        baits=b""
        ultimo+=2
            
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["add_CLASS"]= baits
        baits=b""
        ultimo+=2
        
        for k in range(ultimo, ultimo + 4):
            baits+=message[k:k+1]
        dicc["add_TTL"]= baits
        baits=b""
        ultimo+=4
        
        for k in range(ultimo, ultimo + 2):
            baits+=message[k:k+1]
        dicc["add_RDLENGTH"]= baits
        baits=b""
        ultimo+=2
        
        for k in range(ultimo, ultimo+int.from_bytes(dicc["add_RDLENGTH"])):
            baits+=message[k:k+1]
        dicc["add_RDATA"]= baits
        baits=b""
        ultimo+=int.from_bytes(dicc["add_RDLENGTH"])

    return dicc

# esta función recibe el mensaje de query en bytes obtenido desde el cliente. envía un mensaje query a la ip raíz y trata si esta es una delegación a otro NS
def resolver(mensaje_consulta: bytes, ip_addr=root_ip):
    buff_size = 4096
    dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    #dgram_socket.bind(('localhost', 8000))
    
    dgram_socket.sendto(mensaje_consulta, ip_addr)
    
    datos, direccion = dgram_socket.recv_from(buff_size)
    
    datos_parseados = parse_dns_message(datos)
    
    if dicc["ans_NAME"] in datos_parseados:
        return dicc["ans_RDATA"]
    elif dicc["auth_NAME"] in datos_parseados:
        if b"NS" in dicc["auth_RDATA"]:
            if dicc["add_RDATA"] != b"":
                dgram_socket.send_to(mensaje_consulta, dicc["add_RDATA"])
            else:
                dgram_socket.send_to(mensaje_consulta, dicc["auth_RDATA"])


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
        
        message2=parse_dns_message(message)
        print(message2)
         
        # Enviar mensajes. Este método debe especificar la dirección a la que se va a enviar el mensaje
        #dgram_socket.sendto(message, address)
        
