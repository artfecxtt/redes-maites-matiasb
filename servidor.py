import socket
from socketTCP import SocketTCP
 
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
 
if __name__ == "__main__":
    es_test2n = False
    server_socket = SocketTCP()
    
    server_socket.bind(('localhost', 8000))

    connection_socket, client_addr = server_socket.accept()

    if es_test2n:
        n = 25
        pt1 = connection_socket.recv(n)
        pt2 = connection_socket.recv(n)
        mensaje_entero = pt1 + pt2
        print(mensaje_entero.decode("utf-8", errors="ignore"))

    else:
        buff_size = 200
        mensaje_completo = b""
        while True:
            message = connection_socket.recv(buff_size)

            if not message:
                break
            
            if b"__EOF__" in message:
                mensaje_completo+=message.replace(b"__EOF__", b"")
                print("tamos listos")
                break
            mensaje_completo += message
            print(message)
            
        print(mensaje_completo.decode("utf-8"))
    connection_socket.recv_close()
    server_socket.socketUDP.close()
    
    
    

