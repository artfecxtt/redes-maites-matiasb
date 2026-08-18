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
                i=i+4
                string = ""
                break
        elif decodeado[i] == "\n":
            continue
        else:
            string+=decodeado[i]
        indiceSegundo = i+2
            
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

def leerJSON(nombre, ruta):
    with open(ruta+'/'+nombre) as archivoJSON:
        datos = json.load(archivoJSON)
        if "X-ElQuePregunta" in datos:
            return "X-ElQuePregunta: "+datos["X-ElQuePregunta"]

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
    end_of_message = "\n"
    new_socket_address = ('192.168.1.13', 8000) #maite: 192.168.1.8 ;;;;;;;; mati: 192.168.1.63
 
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
        recv_message2 = recv_message+end_of_message
        procesado = parse_HTTP_message(recv_message)
        
        if "Host" in procesado:
            separado = procesado["Host"].split(":")
            newer_socket_address = ""
            if len(separado) == 1:
                newer_socket_address = (separado[0], 80)
            else:
                newer_socket_address = (separado[0], int(separado[1]))
                
            cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cliente_socket.connect(newer_socket_address)
            cliente_socket.send(recv_message2.encode())
            while True:
                datos = receive_full_message(cliente_socket, buff_size, end_of_message)
                if not datos:
                    break
                datos2 = datos+end_of_message
                new_socket.send(datos2.encode())
            cliente_socket.close()
        new_socket.close()
