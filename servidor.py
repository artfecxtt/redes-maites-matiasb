import socket

# esta función se encarga de recibir el mensaje completo desde el cliente
# en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
# llegue el resto. Para saber si el mensaje ya llegó por completo, se busca el caracter de fin de mensaje (parte de nuestro protocolo inventado)

def receive_full_message(connection_socket, buff_size, end_sequence):
 
    # recibimos la primera parte del mensaje
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
 
    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)
 
    # entramos a un while para recibir el resto y seguimos esperando información
    # mientras el buffer no contenga secuencia de fin de mensaje
    while not is_end_of_message:
        # recibimos un nuevo trozo del mensaje
        recv_message = connection_socket.recv(buff_size)
 
        # lo añadimos al mensaje "completo"
        full_message += recv_message
 
        # verificamos si es la última parte del mensaje
        is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)
 
    # removemos la secuencia de fin de mensaje, esto entrega un mensaje en string
    full_message = remove_end_of_message(full_message.decode(), end_sequence)
 
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
        string += decodeado[k]
        #print(decodeado[k])
        #print(string)
        #print("k actual: "+ str(k))
        if decodeado[k] == '\r':
            indicePrimero = k
            diccionario["SL"] = string
            string = ""
            break
    #print("donde terminé: " + str(indicePrimero))
    #print("donde terminaré: " + str(len(decodeado)+1))
    for i in range(indicePrimero, len(decodeado)):
        #print("donde estoy: " + str(i))
        if decodeado[i] == ":":
            diccionario[string]=None
            clave = string
            string = ""
        elif decodeado[i] == '\n':
            if ultimoString == '\r':
                if clave != "":
                    diccionario[clave]=string
                    string = ""
                    clave = ""
                    ultimoString = ""
                elif decodeado[i+1] == '\r' and decodeado[i+2] == '\n':
                    indiceSegundo = i+3
                    break
        elif i == '\r':
            ultimoString = '\r'
        else:
            string+=decodeado[i]
    for j in range(indiceSegundo, len(decodeado)):
        bodyString+=decodeado[j]
    diccionario["body"]=bodyString
    return diccionario


def create_HTTP_message(dicc: dict):
    baits = ""
    for i in dicc:
        if i == "SL" or i == "body":
            baits+=dicc[i]
        else:
            baits += i
            baits += dicc[i]
    baits = baits.encode()
    return baits
 
if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 4
    end_of_message = "\n"
    new_socket_address = ('192.168.1.63', 8000)
 
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
 
        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
        recv_message = receive_full_message(new_socket, buff_size, end_of_message)

        print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')
        
        parseado = parse_HTTP_message(recv_message)
        print('parseado')

        creado = create_HTTP_message(parseado)
        print('creado desde el parse')
 
        # respondemos indicando que recibimos el mensaje
        response_message = f"Se ha sido recibido con éxito el mensaje: {creado}"
 
        # el mensaje debe pasarse a bytes antes de ser enviado, para ello usamos encode
        new_socket.send(response_message.encode())
 
        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")
 
        # seguimos esperando por si llegan otras conexiones
