import socket
 
print('Creando socket - Cliente')

if __name__ == "__main__":
    buff_size = 16

    # Socket no orientado a conexión
    dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #bindeamos el snoc
    #dgram_socket.bind(('localhost', 8000))

    ruta = input("ruta: ")
    #message, address = dgram_socket.recvfrom(buff_size)
    #print(message)

    bytes_enviados = 0

    with open(ruta, "rb") as f:
        while True:
            pedacito = f.read(buff_size)
            if not pedacito:
                break
            dgram_socket.sendto(pedacito, ("localhost", 8000))
            bytes_enviados += len(pedacito)

    dgram_socket.sendto(b"__EOF__", ("localhost", 8000))
    dgram_socket.close()