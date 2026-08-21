import socket
import json

# esta función se encarga de recibir el mensaje completo desde el cliente
# en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
# llegue el resto. Para saber si el mensaje ya llegó por completo, se busca el caracter de fin de mensaje (parte de nuestro protocolo inventado)

def receive_full_message(connection_socket, buff_size, end_sequence):
 
    # recibimos la primera parte del mensaje
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
 
    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    is_end_of_message = contains_end_of_message(full_message, end_sequence)
 
    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    while not is_end_of_message:
        # recibimos un nuevo trozo del mensaje
        recv_message = connection_socket.recv(buff_size)
 
        # lo añadimos al mensaje "completo"
        full_message += recv_message
 
        # verificamos si es la última parte del mensaje
        is_end_of_message = contains_end_of_message(full_message, end_sequence)
 
    # removemos la secuencia de fin de mensaje, esto entrega un mensaje en string
    full_message = remove_end_of_message(full_message, end_sequence)
 
    # finalmente retornamos el mensaje
    return full_message
 
def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)
 
def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

def parse_HTTP_message(decodeado: bytes):
    diccionario = {}
    string = b""
    clave = b""
    indicePrimero = 0
    indiceSegundo = 0
    
    for k in range(len(decodeado)):
        if decodeado[k:k+1] == b"\r":
            indicePrimero = k + 2
            diccionario[b"SL"] = string
            string = b""
            break
        string += decodeado[k:k+1]
        
    for i in range(indicePrimero, len(decodeado)):
        if decodeado[i:i+1] == b":" and clave == b"":
            clave = string
            string = b""
        elif decodeado[i:i+1] == b"\r":
            if clave != b"":
                diccionario[clave] = string.strip()
                string = b""
                clave = b""
            else:
                indiceSegundo = i + 2
                string = b""
                break
        elif decodeado[i:i+1] == b"\n":
            continue
        else:
            string += decodeado[i:i+1]
            
    diccionario[b"body"] = decodeado[indiceSegundo:]
    return diccionario

def create_HTTP_message(dicc: dict):
    baits = b""
    end_message = b"\r\n"
    for i in dicc:
        if i == b"SL":
            baits = baits + dicc[i] + end_message
        elif i == b"body":
            baits = baits + end_message + dicc[i]# + "\n"
        else:
            val = b""
            if isinstance(dicc[i], bytes):
                val = dicc[i]
            else:
                str(dicc[i]).encode()
            baits = baits + i + b": " + val + end_message
    #baits =  baits.encode()
    return baits

def create_HTTP_message2(dicc: dict):
    baits = b""
    end_message = b"\r\n"
    for i in dicc:
        if i == b"SL":
            baits = baits + dicc[i] + end_message
        elif i == b"body":
            baits = baits + b"Connection: close\r\n"
            baits = baits + b"X-ElQuePregunta: Matias y Maite\r\n"
            baits = baits + end_message + dicc[i]# + "\n"
        else:
            val = b""
            if isinstance(dicc[i], bytes):
                val = dicc[i]
            else:
                str(dicc[i]).encode()
            baits = baits + i + b": " + val + end_message
    #baits =  baits.encode()
    return baits

def leerJSON(nombre):
    with open(nombre) as archivoJSON:
        datos = json.load(archivoJSON)
        if "blocked" in datos:
            return "X-ElQuePregunta: "+datos["X-ElQuePregunta"]

def leerJSON_dominio(nombre, dominio):
    with open(nombre, "r", encoding="utf-8") as archivoJSON:
        datos = json.load(archivoJSON)
        if "blocked" in datos:
            url_str = b""
            if isinstance(dominio, bytes):
                url_str = dominio.decode("utf-8", errors="ignore")
            else:
                url_str = dominio
            url_str = url_str.rstrip("/")
            for bloqueado in datos["blocked"]:
                if url_str == bloqueado.rstrip("/"):
                    return True
    return False

def leerJSON_reemplazar(nombre):
    with open(nombre) as archivoJSON:
        datos = json.load(archivoJSON)
        if "forbidden_words" in datos:
            return datos["forbidden_words"]

#def create_HTTP_message(dicc: dict):
#    baits = ""
#    for i in dicc:
#        if i == "SL" or i == "body":
#            baits+=dicc[i]
#        else:
#            baits += i
#            baits += dicc[i]
#    baits = baits.encode()
#    return baits
 
if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 4
    end_of_message = b"\r\n\r\n"
    new_socket_address = ('localhost', 8000) #maite: 192.168.1.8 ;;;;;;;; mati: 192.168.1.63
 
    print('Creando socket - Servidor')
    # armamos el socket
    # los parámetros que recibe el socket indican el tipo de conexión
    # socket.SOCK_STREAM = socket orientado a conexión
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(new_socket_address)
 
    # luego con listen (función de sockets de python) le decimos que puede
    # tener hasta 3 peticiones de conexión encoladas
    # si recibiera una 4ta petición de conexión la va a rechazar
    server_socket.listen(3)

    # nos quedamos esperando a que llegue una petición de conexión
    print('... Esperando clientes')
    while True:
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        new_socket, new_socket_address = server_socket.accept()
        #response = open("respuesta.html", "r", encoding = "utf-8")
        response = b""
 
        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
        recv_message = receive_full_message(new_socket, buff_size, end_of_message)
        print(recv_message)
        recv_message2 = recv_message+end_of_message
        #print(recv_message2)
        procesado = parse_HTTP_message(recv_message)
        print(procesado)
        
        if b"Host" in procesado:
            separado = procesado[b"Host"].split(b":")
            #print(separado)
            newer_socket_address = b""
            if len(separado) == 1:
                newer_socket_address = (separado[0], 80)
            else:
                newer_socket_address = (separado[0], int(separado[1]))

            SL_separado = procesado[b"SL"].split(b" ")
            #print(SL_separado)
            url_pedida = SL_separado[1]

            ## item 2
            if url_pedida.startswith(b"http://"):
                url_pedida=url_pedida[7:]
            elif url_pedida.startswith(b"/"):
                url_pedida = separado[0]+url_pedida

            if url_pedida.endswith(b"gatoglup.png"):
                with open("gatoglup.png", "rb") as f:
                    img_bytes = f.read()

                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: image/png\r\n"
                    f"Content-Length: {len(img_bytes)}\r\n"
                    "Connection: close\r\n\r\n"
                )
                new_socket.send(headers.encode("utf-8") + img_bytes)
                
            elif leerJSON_dominio("bloqueos.json", url_pedida):
                with open("forbidden.html", "r", encoding = "utf-8") as gatoglup:
                    gatoglup_txt = gatoglup.read().encode("utf-8")
                    
                start_line = b"HTTP/1.1 403 Forbidden\r\n"
                CT = b"Content-Type: text/html; charset=utf-8\r\n"
                CL = b"Content-Length: " + str(len(gatoglup_txt)).encode("utf-8") + b"\r\n"
                conn = b"Connection: close\r\n"
                end_head = b"\r\n"
                respuesta = start_line + CT + CL + conn + end_head + gatoglup_txt
                
                new_socket.send(respuesta)
            else:    
                cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cliente_socket.connect(newer_socket_address)
                recv_parse = parse_HTTP_message(recv_message2)
                recv_create = create_HTTP_message2(recv_parse)
                print(recv_create)
                cliente_socket.send(recv_create)
                respuesta_cruda = b"" #revisar todo esto último
                while True:
                    pedazo = cliente_socket.recv(buff_size)
                    if not pedazo:
                        break
                    respuesta_cruda+=pedazo
                
                if respuesta_cruda:
                    #datos = respuesta_cruda.decode("utf-8", errors = "replace")
                    datos2 = parse_HTTP_message(respuesta_cruda)
                    
                    print(datos2)
                    prohibidas = leerJSON_reemplazar("bloqueos.json")
                    if prohibidas and b"body" in datos2:
                        for par in prohibidas:
                            llave = list(par.keys())[0]
                            print(llave)
                            print(datos2[b"body"])
                            datos2[b"body"] = datos2[b"body"].replace(llave.encode(), par[llave].encode())
                            #print(datos2)
                    datos2[b"Content-Length"] = str(len(datos2[b"body"])).encode()
                    datos3 = create_HTTP_message(datos2)
                    new_socket.send(datos3)
                cliente_socket.close()
        new_socket.close()
