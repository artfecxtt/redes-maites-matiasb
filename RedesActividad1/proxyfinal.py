import socket
import json

# esta función se encarga de recibir el mensaje completo desde el cliente
# en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
# llegue el resto. para saber si el mensaje ya llegó por completo, se busca el caracter de fin de mensaje
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

# esta función se encarga de identificar si es que en el mensaje entregado se encuentra la secuencia final del mensaje
def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)

# esta función se encarga de remover la secuencia final del mensaje, retornando solo el cuerpo del mensaje en sí
def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

# parece sospechoso pero, el argumento de esta función se llama así porque en un inicio estábamos decodeando los mensajes. en ese ensayo y error, era más fácil dejar como nombre
# del argumento 'decodeado' en vez de reemplazar todo en la función. se quedó así por los jajas. lo importante es que no se encodea y decodea nada en el código. todo se está
# trabajando en bytes
#
# esta función se encarga de, dado un mensaje HTTP en bytes, lo transfiere a una estructura de datos, la cuál será un diccionario, para acceder 
# facilmente a la información del mensaje
def parse_HTTP_message(decodeado: bytes):
    diccionario = {}
    string = b"" #se llama string pero realmente son bytes, es una variable que se nos quedó por no cambiar le nombre temprano en el desarrollo
    clave = b""
    indicePrimero = 0
    indiceSegundo = 0

    # se extrae la start line del mensaje, colocando como llave "SL" en el diccionario y luego
    # el contenido extraído del mensaje.
    for k in range(len(decodeado)):
        if decodeado[k:k+1] == b"\r":
            indicePrimero = k + 2
            diccionario[b"SL"] = string
            string = b""
            break
        string += decodeado[k:k+1]
    # se extrae cada header del HEAD del mensaje    
    for i in range(indicePrimero, len(decodeado)):
        # se coloca como llave el texto que se encuentre antes de lo ":" que separan el nombre del header con su contenido
        if decodeado[i:i+1] == b":" and clave == b"":
            clave = string
            string = b""
        # en caso de estar al final de una línea señalizado por el "\r", se tienen 2 opciones
        # si la clave no está vacía entonces se guarda el contenido del mensaje leído en el cuerpo señalado por la llave en el diccionario
        # si no, estamos al final del HEAD, así que se rompe este cico
        elif decodeado[i:i+1] == b"\r":
            if clave != b"":
                diccionario[clave] = string.strip()
                string = b""
                clave = b""
            else:
                indiceSegundo = i + 2
                string = b""
                break
        # si se lee un "\n" entonces se continua el ciclo
        elif decodeado[i:i+1] == b"\n":
            continue
        # para cualquier otro caso se continuan leyendo los bytes
        else:
            string += decodeado[i:i+1]
    # por último, se guarda el body del mensaje dentro de la llave "body  del diccionario       
    diccionario[b"body"] = decodeado[indiceSegundo:]
    return diccionario

# esta función toma un diccionario y lo convierte en un mensaje HTTP en bytes
def create_HTTP_message(dicc: dict):
    baits = b""
    end_message = b"\r\n"
    # por cada clave en el diccionario
    for i in dicc:
        # si es la llave "SL" se guarda la startline
        if i == b"SL":
            baits = baits + dicc[i] + end_message
        # si es la llave "body" se guarda el body en el mensaje
        # esto terminaría con el ciclo porque es la última llave
        elif i == b"body":
            baits = baits + end_message + dicc[i]# + "\n"
        # si no, estamos tratando con un header, donde nos aseguramos que su contenido sea bytes antes de colocarlo en el mensaje
        else:
            val = b""
            if isinstance(dicc[i], bytes):
                val = dicc[i]
            else:
                str(dicc[i]).encode()
            # se coloca el nombre de la llave, luego ":" y por último el contenido junto al fin del mensaje
            baits = baits + i + b": " + val + end_message
    return baits

# esta función toma un diccionario y lo convierte en un mensaje HTTP en bytes
# lo diferente de esta función con el create_HTTP_message es que se encarga del tratamiento necesario de la parte 2 para colocar el header personalizado
def create_HTTP_message2(dicc: dict):
    baits = b""
    end_message = b"\r\n"
    for i in dicc:
        if i == b"SL":
            baits = baits + dicc[i] + end_message
        elif i == b"body":
            # esta es la única diferencia con la otra función, donde añade el header extra pedido al mensaje 
            # antes de colocar el body como lo hacía la función anterior
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
    return baits

# esta función se encarga de leer archivos JSON
# fue utilizada para la parte 1 de la actividad, por lo tanto no es relevante
def leerJSON(nombre):
    with open(nombre) as archivoJSON:
        datos = json.load(archivoJSON)
        if "blocked" in datos:
            return "X-ElQuePregunta: "+datos["X-ElQuePregunta"]

# esta función recibe el nombre de un archivo JSON y un dominio cualquiera. busca dentro del archivo JSON si este tiene la sección blocked, si es así, busca si el
# dominio entregado se encuentra bloqueado, si es así retorna True, si no False
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

# esta función recibe el nombre de un archivo JSON y busca si tiene la sección "forbidden_words", si es así retorna
# el contenido de esta sección, si no, no retorna nada
def leerJSON_reemplazar(nombre):
    with open(nombre) as archivoJSON:
        datos = json.load(archivoJSON)
        if "forbidden_words" in datos:
            return datos["forbidden_words"]

#FUNCIONAMIENTO PRINCIPAL DEL SOCKET
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
        #print(recv_message)
        
        #se le añade el end_of_message
        recv_message2 = recv_message+end_of_message
        #print(recv_message2)
        
        # luego se parsea el mensaje para que se encuentre en el formato de un diccionario a través de la función ya programada
        procesado = parse_HTTP_message(recv_message)
        #print(procesado)
        
        # si es que hay una clave en el diccionario llamada "Host
        if b"Host" in procesado:
            # se separa el host identificando la IP y el puerto
            separado = procesado[b"Host"].split(b":")
            #print(separado)
            newer_socket_address = b""
            if len(separado) == 1:
                newer_socket_address = (separado[0], 80)
            else:
                newer_socket_address = (separado[0], int(separado[1]))

            # se procesa la start line separando por el caracter " " debido a la estructura general de una start line
            SL_separado = procesado[b"SL"].split(b" ")
            #print(SL_separado)
            
            url_pedida = SL_separado[1]

            ## item 2
            # se trata la url obtenida por conveniencia para cumplir con los formatos necesarios más adelante
            if url_pedida.startswith(b"http://"):
                url_pedida=url_pedida[7:]
            elif url_pedida.startswith(b"/"):
                url_pedida = separado[0]+url_pedida

            # si es que la URL está pidiendo la imágen ocupada para el mensaje 403 Forbidden, entonces se crea el mensaje con sus header, se añade la imágen
            # y luego se envía a quien la pedía
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

            # si es que la URL se encontraba dentro de la lista de urls bloqueadas
            # se envía un mensaje de respuesta informando el mensaje de error junto a otros headers relevantes
            # además se envía como texto el html correspondiente al mensaje  
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

            # si no ocurre ninguna de las anteriores, entonces estamos recibiendo una página que hay que dejar pasar
            else:  
                # se crea el socket proxy-servidor 
                cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cliente_socket.connect(newer_socket_address)

                # se parsea y crea el mensaje HTTP
                recv_parse = parse_HTTP_message(recv_message2)
                recv_create = create_HTTP_message2(recv_parse)
                #print(recv_create)
                
                # se envía el mensaje al cliente
                cliente_socket.send(recv_create)
                respuesta_cruda = b""
                while True:
                    # se recibe información entregada por el cliente en pedazos según el tamaño del buffer para juntarlo en una respuesta completa
                    pedazo = cliente_socket.recv(buff_size)
                    if not pedazo:
                        break
                    respuesta_cruda+=pedazo
                
                if respuesta_cruda:
                    # la respuesta completa la pasamos al diccionario
                    datos2 = parse_HTTP_message(respuesta_cruda)
                    
                    #print(datos2)
                    
                    # extraemos las palabras prohibidad
                    prohibidas = leerJSON_reemplazar("bloqueos.json")
                    if prohibidas and b"body" in datos2:
                        # se reemplazan las palabras prohibidas en el cuerpo del mensaje por la censura respectiva
                        for par in prohibidas:
                            llave = list(par.keys())[0]
                            #print(llave)
                            #print(datos2[b"body"])
                            datos2[b"body"] = datos2[b"body"].replace(llave.encode(), par[llave].encode())
                    # se define correctamente el Content-Length con los cambios realizados
                    datos2[b"Content-Length"] = str(len(datos2[b"body"])).encode()
                    # se crea el mensaje HTTP nuevo
                    datos3 = create_HTTP_message(datos2)
                    # se envía de vuelta
                    new_socket.send(datos3)

                # para finalizar se cierran los 2 sockets abiertos
                cliente_socket.close()
        new_socket.close()
