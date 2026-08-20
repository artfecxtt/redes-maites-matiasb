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
    is_end_of_message = contains_end_of_message(full_message.decode("utf-8", errors="ignore"), end_sequence)
 
    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    while not is_end_of_message:
        # recibimos un nuevo trozo del mensaje
        recv_message = connection_socket.recv(buff_size)
 
        # lo añadimos al mensaje "completo"
        full_message += recv_message
 
        # verificamos si es la última parte del mensaje
        is_end_of_message = contains_end_of_message(full_message.decode("utf-8", errors="ignore"), end_sequence)
 
    # removemos la secuencia de fin de mensaje, esto entrega un mensaje en string
    full_message = remove_end_of_message(full_message.decode("utf-8", errors="replace"), end_sequence)
 
    # finalmente retornamos el mensaje
    return full_message
 
def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)
 
def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

def parse_HTTP_message(decodeado: bytes):
    #decodeado = http_message.decode()
    diccionario = {}
    string = ""
    clave = ""
    ultimoString = ""
    indicePrimero = 0
    indiceSegundo = 0
    bodyString = ""
    for k in range(len(decodeado)):
        #print(decodeado[k])
        #print(string)
        #print("k actual: "+ str(k))
        if decodeado[k] == "\r":
            indicePrimero = k+2
            diccionario["SL"] = string
            string = ""
            break
        string += decodeado[k]
    #print("donde terminé: " + str(indicePrimero))
    #print("donde terminaré: " + str(len(decodeado)+1))
    for i in range(indicePrimero, len(decodeado)):
        #print("donde estoy: " + str(i))
        if decodeado[i] == ":" and clave == "":
            diccionario[string]=None
            clave = string
            string = ""
        elif decodeado[i] == "\r":
            if clave != "":
                diccionario[clave]=string.strip()
                string = ""
                clave = ""
                i=i+2
            else:
                indiceSegundo = i+2
                string = ""
                break
        elif decodeado[i] == "\n":
            continue
        else:
            string+=decodeado[i]
            
    for j in range(indiceSegundo, len(decodeado)):
        bodyString+=decodeado[j]
    diccionario["body"]=bodyString
    return diccionario

def create_HTTP_message(dicc: dict):
    baits = ""
    end_message = "\r\n"
    for i in dicc:
        if i == "SL":
            baits = baits + dicc[i] + end_message
        elif i == "body":
            baits = baits + end_message + dicc[i]# + "\n"
        else:
            baits = baits + i + ": " + dicc[i] + end_message
    #baits =  baits.encode()
    return baits

def create_HTTP_message2(dicc: dict):
    baits = ""
    end_message = "\r\n"
    for i in dicc:
        if i == "SL":
            baits = baits + dicc[i] + end_message
        elif i == "body":
            baits = baits + "Connection: close\r\n"
            baits = baits + "X-ElQuePregunta: Matias y Maite\r\n"
            baits = baits + end_message + dicc[i]# + "\n"
        else:
            baits = baits + i + ": " + dicc[i] + end_message
    #baits =  baits.encode()
    return baits

def leerJSON(nombre):
    with open(nombre) as archivoJSON:
        datos = json.load(archivoJSON)
        if "blocked" in datos:
            return "X-ElQuePregunta: "+datos["X-ElQuePregunta"]

def leerJSON_dominio(nombre, dominio):
    with open(nombre) as archivoJSON:
        datos = json.load(archivoJSON)
        if "blocked" in datos:
            if dominio in datos["blocked"]:
                return True
            else:
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
    end_of_message = "\r\n\r\n"
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
        response = ""
 
        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
        recv_message = receive_full_message(new_socket, buff_size, end_of_message)
        print(recv_message)
        recv_message2 = recv_message+end_of_message
        #print(recv_message2)
        procesado = parse_HTTP_message(recv_message)
        print(procesado)
        
        if "Host" in procesado:
            separado = procesado["Host"].split(":")
            #print(separado)
            newer_socket_address = ""
            if len(separado) == 1:
                newer_socket_address = (separado[0], 80)
            else:
                newer_socket_address = (separado[0], int(separado[1]))

            SL_separado = procesado["SL"].split(" ")
            #print(SL_separado)
            url_pedida = SL_separado[1]

            ## item 2
            if url_pedida.startswith("http://"):
                url_pedida=url_pedida[7:]
            elif url_pedida.startswith("/"):
                url_pedida = separado[0]+url_pedida
            dominio = url_pedida.rstrip("/")

            if url_pedida.endswith("gatoglup.png"):
                with open("gatoglup.png", "rb") as f:
                    img_bytes = f.read()

                headers = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: image/png\r\n"
                    f"Content-Length: {len(img_bytes)}\r\n"
                    "Connection: close\r\n\r\n"
                )
                new_socket.send(headers.encode("utf-8") + img_bytes)
                
            elif leerJSON_dominio("bloqueos.json", dominio):
                gatoglup = open("forbidden.html", "r", encoding = "utf-8")
                gatoglup_txt = gatoglup.read()
                start_line = "HTTP/1.1 403 Forbidden\r\n"
                CT = "Content-Type: text/html; charset=utf-8\r\n"
                CL = "Content-Length: " + str(len(gatoglup_txt.encode("utf-8"))) + "\r\n"
                end_head = "\r\n"
                respuesta = start_line + CT + CL + end_head + gatoglup_txt
                
                parseado = parse_HTTP_message(respuesta)
                gatoglup_response = create_HTTP_message(parseado)
                
                new_socket.send(gatoglup_response.encode())
            else:    
                cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cliente_socket.connect(newer_socket_address)
                recv_parse = parse_HTTP_message(recv_message2)
                recv_create = create_HTTP_message2(recv_parse)
                print(recv_create)
                cliente_socket.send(recv_create.encode())
                respuesta_cruda = b"" #revisar todo esto último
                while True:
                    pedazo = cliente_socket.recv(buff_size)
                    if not pedazo:
                        break
                    respuesta_cruda+=pedazo
                
                if respuesta_cruda:
                    datos = respuesta_cruda.decode("utf-8", errors = "replace")
                    datos2 = parse_HTTP_message(datos)
                    
                    print(datos2)
                    prohibidas = leerJSON_reemplazar("bloqueos.json")
                    if prohibidas and "body" in datos2:
                        for par in prohibidas:
                            llave = list(par.keys())[0]
                            print(llave)
                            print(datos2["body"])
                            datos2["body"] = datos2["body"].replace(llave, par[llave])
                            #print(datos2)
                    datos2["Content-Length"] = str(len(datos2["body"].encode("utf-8")))
                    datos3 = create_HTTP_message(datos2).encode("utf-8")
                    new_socket.send(datos3)
                cliente_socket.close()
        new_socket.close()
