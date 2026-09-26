import socket
 
print('Creando socket - Cliente')
 
# armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
# socket.SOCK_STREAM = socket orientado a conexión
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
# Como es un socket orientado a conexión debemos conectarlo a la dirección acordada
address = ('localhost', 5000)
client_socket.connect(address)
 
# Definimos un mensaje y una secuencia indicando el fin del mensaje (parte de nuestro protocolo inventado)
message = "Hola, este es un mensaje de prueba"
end_of_message = "\n"
 
# Armamos el mensaje final a enviar y lo pasamos a bytes con encode
send_message = (message + end_of_message).encode()
 
# enviamos el mensaje a través del socket
print(f"... Mandando el mensaje: {send_message.decode()}")
client_socket.send(send_message)
 
print("... Mensaje enviado")
 
# Finalmente esperamos una respuesta
# Para ello debemos definir el tamaño del buffer de recepción
buffer_size = 1024
message = client_socket.recv(buffer_size)
 
# Pasamos el mensaje de bytes a string
decoded_message = message.decode()
 
print(f' -> Respuesta del servidor: {decoded_message}')
 
# cerramos la conexión
client_socket.close()