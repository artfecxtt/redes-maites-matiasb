#debe tener socket UDP, dirección de destino, número de secuencia, todo lo que usted considere necesario.
import socket
import random

class SocketTCP:
    def __init__(self):
        # inicializamos las variables que definen una mascota
        # los datos que aun no sabemos se ponen como None
        self.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dirdestino = ("localhost", 8000)
        self.nrosec = 0
        
        self.nroack = 0
        self.bytes_por_recibir = 0
        self.buffer_sobrante = b""

    @staticmethod
    #estructura de headers TCP debemos usar bytes directamente. notar forma en que dichos bytes codifican
    #esto es para que pueda pasar segmentos tcp a alguna estructura de datos más cómoda
    def parse_segment(segment_bytes):
        # Los primeros 4 bytes son los campos fijos
        seq = segment_bytes[0]
        ack = segment_bytes[1]
        syn = bool(segment_bytes[2])
        fin = bool(segment_bytes[3])

        # desde el índice 4 hasta el final son los datos (en bytes)
        data = segment_bytes[4:]

        return {'seq': seq, 'ack': ack, 'syn': syn, 'fin': fin, 'data': data}
    
    @staticmethod
    #crea segmentos a partir de dicha estructura de datos
    def create_segment(segmento_dict):
        seq = segmento_dict.get('seq', 0)
        ack = segmento_dict.get('ack', 0)
        if "syn" in segmento_dict and segmento_dict["syn"] == True:
            syn = 1
        else:
            syn = 0
            
        if "fin" in segmento_dict and segmento_dict["fin"] == True:
            fin = 1
        else:
            fin = 0
        
        # le sacamos la data al diccionario
        data = segmento_dict.get('data', b'')
        
        # si es q está en strings, se pasa a bytes por si acaso
        if isinstance(data, str):
            data = data.encode('utf-8')

        # se crea la cabecera y se le une la data
        header = bytes([seq, ack, syn, fin])
        return header + data

    def bind(self, address):
        self.socketUDP.bind(address)
        
    def connect(self, address):
        self.dirdestino = address
        self.nrosec = random.randint(0, 100)

        # se envia el mensaje SYN
        syn_seg = {"seq": self.nrosec, "ack": 0, "syn": True, "fin": False, "data": b""}
        self.socketUDP.sendto(self.create_segment(syn_seg), self.dirdestino)

        # esperamos por el SYN + ACK
        response, server_new_addr = self.socketUDP.recvfrom(16)
        resp = self.parse_segment(response)

        if resp["syn"] and resp["ack"] == (self.nrosec + 1):
            # se actualiza el destino a la nueva dirección y puerto q respondió
            self.dirdestino = server_new_addr

            # se avanza y guarda el ACK
            self.nrosec = resp["ack"]
            self.nroack = resp["seq"] + 1

            # se envía el ack para completar el handshake
            ack_seg = {"seq": self.nrosec, "ack": self.nroack, "syn": False, "fin": False, "data": b""}
            self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)
            print("ta lista la conexión")
        else:
            print("fallo en el handshake")
    
    def accept(self):
        # se espera por el SYN
        while True:
            msg, client_addr = self.socketUDP.recvfrom(16)
            seg = self.parse_segment(msg)
            if seg['syn']:
                break

        # se crea un socket en un nuevo puerto
        nueva_dir = ('localhost', 8001)
        nuevo_socket = SocketTCP()
        nuevo_socket.bind(nueva_dir)

        # destino y seq
        nuevo_socket.dirdestino = client_addr
        nuevo_socket.nrosec = random.randint(0, 100)
        nuevo_socket.nroack = seg['seq'] + 1

        # se envía el SYN + ACK por el nuevo socket
        syn_ack = {'seq': nuevo_socket.nrosec, 'ack': nuevo_socket.nroack, 'syn': True, 'fin': False, 'data': b''}
        nuevo_socket.socketUDP.sendto(self.create_segment(syn_ack), nuevo_socket.dirdestino)

        # se espera el ACK final en el 8001
        ack, _ = nuevo_socket.socketUDP.recvfrom(16)
        ack_final = self.parse_segment(ack)

        if ack_final['ack'] == (nuevo_socket.nrosec + 1):
            nuevo_socket.nrosec = ack_final['ack']
            nuevo_socket.nroack = ack_final['seq']
            return nuevo_socket, nueva_dir
        else:
            nuevo_socket.close()
            print("no se recibió último ack")

    def send(self, message):
        buff_size = 20
        msg_length = len(message)
        
        largo_bytes = str(msg_length).encode('utf-8')
        segmento = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': False, 'data': largo_bytes}
        self.socketUDP.sendto(self.create_segment(segmento), self.dirdestino)
        ack, _ = self.socketUDP.recvfrom(buff_size)
        self.nrosec += len(largo_bytes)
    
        bytes_enviados = 0

        while True:
            pedacito = message[bytes_enviados:bytes_enviados+16]
            if not pedacito:
                break
            seg = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': False, 'data': pedacito}
            self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
            
            ack, _ = self.socketUDP.recvfrom(buff_size)
            
            self.nrosec += len(pedacito)
            bytes_enviados += len(pedacito)
            
        #fin_seg = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': True, 'data': b""}
        #self.socketUDP.sendto(self.create_segment(fin_seg), self.dirdestino)
    
    def recv(self, buff_size):
        udp_buff_size = 20

        # si los bytes_por_recibir son 0, hay q esperar por el mensaje inicial cn el largo
        if self.bytes_por_recibir == 0:
            msg, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)
            seg_largo = self.parse_segment(msg)
            
            # se saca la longitud
            message_length = int(seg_largo['data'].decode('utf-8'))
            self.bytes_por_recibir = message_length

            # se envía el ACK de confirmación al emisor
            ack_seg = {'seq': self.nrosec, 'ack': seg_largo['seq'] + len(seg_largo['data']), 'syn': False, 'fin': False, 'data': b''}
            self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)

        # se agarran los datos q sobrearon d cosas anteriores
        message_received = self.buffer_sobrante
        self.buffer_sobrante = b""

        # cálculo de máximo a retornar en esta llamada
        limite_esperado = min(self.bytes_por_recibir, buff_size)

        # se recibe contenido hasta cumplir la condición
        while len(message_received) < limite_esperado:
            raw_data, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)
            seg_datos = self.parse_segment(raw_data)

            #se acumula solo la data
            message_received += seg_datos['data']

            # se envía ACK de confirmación solo al emisor
            ack_seg = {'seq': self.nrosec, 'ack': seg_datos['seq'] + len(seg_datos['data']), 'syn': False, 'fin': False, 'data': b''}
            self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)

        # si se recibe más de buff_size
        if len(message_received) > buff_size:
            self.buffer_sobrante = message_received[buff_size:] #se guarda lo q sobre
            resultado = message_received[:buff_size] # se retorna lo q se pide
        else:
            resultado = message_received

        # se restan los bytes entregado
        self.bytes_por_recibir -= len(resultado)

        return resultado
        
    def close(self):
        pass
        
    def recv_close(self):
        pass


