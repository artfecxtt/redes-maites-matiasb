import sys
import socket
from socketTCP import SocketTCP
 
print('Creando socket - Cliente')

if __name__ == "__main__":
    buff_size = 16

    # socket no orientado a conexión
    dgram_socket = SocketTCP()

    #bindeamos el snoc
    dgram_socket.connect(('localhost', 8000))

    #message, address = dgram_socket.recvfrom(buff_size)
    #print(message)

    nro_secuencia = 0
    bytes_enviados = 0

    while True:
        pedacito = sys.stdin.buffer.read(buff_size)
        if not pedacito:
            break
        dgram_socket.send(pedacito)
          
    dgram_socket.send(b"__EOF__")  
    dgram_socket.close()
    
    
    
    
    
    
