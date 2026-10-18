import socket
from socketTCP import SocketTCP

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
        buff_size = 20
        mensaje_completo = b""
        while True:
            message = connection_socket.recv(buff_size, mode="go_back_n")

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
    
    
    

