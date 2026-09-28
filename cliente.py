import socket
from socketTCP import SocketTCP
 
print('Creando socket - Cliente')

if __name__ == "__main__":
    buff_size = 16 

    # socket no orientado a conexión
    dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_x = SocketTCP()

    #bindeamos el snoc
    #dgram_socket.bind(('localhost', 8000))

    ruta = input("ruta: ")
    #message, address = dgram_socket.recvfrom(buff_size)
    #print(message)

    nro_secuencia = 0
    bytes_enviados = 0

    with open(ruta, "rb") as f:
        while True:
            pedacito = f.read(buff_size)
            if not pedacito:
                break
            segmento = {'seq': nro_secuencia, 'ack': 0, 'syn': False, 'fin': False, 'data': pedacito}
            paquete_bytes = socket_x.create_segment(segmento)
            dgram_socket.sendto(paquete_bytes, ("localhost", 8000))
            bytes_enviados += len(pedacito)
            nro_secuencia = (nro_secuencia + 1) % 256

    fin_segmento = {'seq': nro_secuencia, 'ack': 0, 'syn': False, 'fin': True, 'data': b''}
    dgram_socket.sendto(socket_x.create_segment(fin_segmento), ("localhost", 8000))
    dgram_socket.close()
    
    
    
    
    
    