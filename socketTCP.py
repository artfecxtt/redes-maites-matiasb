#debe tener socket UDP, dirección de destino, número de secuencia, todo lo que usted considere necesario.
import socket
import random
import time

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
        self.seq_prev = 0

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
        seq = segmento_dict.get('seq', 0) % 256
        ack = segmento_dict.get('ack', 0) % 256
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

        while True:
            try:
                # se envia el mensaje SYN
                syn_seg = {"seq": self.nrosec, "ack": 0, "syn": True, "fin": False, "data": b""}
                self.socketUDP.sendto(self.create_segment(syn_seg), self.dirdestino)
                
                # esperamos por el SYN + ACK
                response, server_new_addr = self.socketUDP.recvfrom(16)
                resp = self.parse_segment(response)
                
                if resp["syn"] and resp["ack"] == (self.nrosec + 1):
                    self.dirdestino = server_new_addr
                    self.nrosec = resp["ack"]
                    self.nroack = resp["seq"] + 1
                    break
            except socket.timeout:
                continue

        ack_seg = {"seq": self.nrosec, "ack": self.nrosec, "syn": False, "fin": False, "data": b""}
        self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)
        print("ta lista la conexión")
    
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
        nuevo_socket.socketUDP.settimeout(2.0)
        syn_ack = {'seq': nuevo_socket.nrosec, 'ack': nuevo_socket.nroack, 'syn': True, 'fin': False, 'data': b''}
        
        while True:
            try:
                nuevo_socket.socketUDP.sendto(self.create_segment(syn_ack), nuevo_socket.dirdestino)
                
                # se espera el ACK final en el 8001
                ack, _ = nuevo_socket.socketUDP.recvfrom(16)
                ack_final = self.parse_segment(ack)
                
                if ack_final['ack'] == (nuevo_socket.nrosec + 1):
                    nuevo_socket.nrosec = ack_final['ack']
                    nuevo_socket.nroack = ack_final['seq']
                    break
                    
                if not ack_final["syn"] and not ack_final["fin"] and len(ack_final["data"]) > 0:
                    nuevo_socket.nrosec = ack_final['ack']
                    nuevo_socket.nroack = ack_final['seq']
                    
                    nuevo_socket.buffer_sobrante = ack
                    break
            except socket.timeout:
                continue
        
        return nuevo_socket, nueva_dir

    def send(self, message):
        buff_size = 20
        msg_length = len(message)
        
        self.socketUDP.settimeout(2.0)
        
        largo_bytes = str(msg_length).encode('utf-8')
        segmento = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': False, 'data': largo_bytes}
        esperado_ack = (self.nrosec + len(largo_bytes)) % 256
        
        while True:
            try:
                self.socketUDP.sendto(self.create_segment(segmento), self.dirdestino)
                ack, _ = self.socketUDP.recvfrom(buff_size)
                ack_seg = self.parse_segment(ack)

                if ack_seg['ack'] == esperado_ack:
                    self.nrosec = esperado_ack
                    break
                
            except socket.timeout:
                continue
    
        bytes_enviados = 0

        while True:
            pedacito = message[bytes_enviados:bytes_enviados+16]
            if not pedacito:
                break
            seg = {'seq': self.nrosec % 256, 'ack': 0, 'syn': False, 'fin': False, 'data': pedacito}
            esperado_ack = (self.nrosec + len(pedacito)) % 256
            
            while True:
                try:
                    self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
                    ack, _ = self.socketUDP.recvfrom(buff_size)
                    ack_seg = self.parse_segment(ack)

                    if ack_seg['ack'] == esperado_ack:
                        self.nrosec = esperado_ack
                        bytes_enviados += len(pedacito)
                        break
                except socket.timeout:
                    continue

        #fin_seg = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': True, 'data': b""}
        #self.socketUDP.sendto(self.create_segment(fin_seg), self.dirdestino)
    
    def recv(self, buff_size):
        udp_buff_size = 20
        self.socketUDP.settimeout(None)
        
        # si los bytes_por_recibir son 0, hay q esperar por el mensaje inicial cn el largo
        if self.bytes_por_recibir == 0:
            while True:
                if self.buffer_sobrante:
                    msg = self.buffer_sobrante
                    self.buffer_sobrante = b""
                else:
                    msg, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)
                    
                seg_largo = self.parse_segment(msg)

                if seg_largo["fin"]:
                    self.buffer_sobrante = msg
                    return b""

                # tolerancia pérdidas
                try:
                    # se saca la longitud
                    message_length = int(seg_largo['data'].decode('utf-8'))
                    self.seq_prev = (seg_largo["seq"] + len(seg_largo['data'])) % 256
                    self.bytes_por_recibir = message_length

                    # se envía el ACK de confirmación al emisor
                    ack_seg = {
                        'seq': self.nrosec % 256,
                        'ack': self.seq_prev,
                        'syn': False,
                        'fin': False,
                        'data': b''
                    }
                    self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)
                    break
                except ValueError:
                    ack_seg = {
                        'seq': self.nrosec % 256,
                        'ack': self.seq_prev,
                        'syn': False,
                        'fin': False,
                        'data': b''
                    }
                    self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)
                    continue
                    

        # se agarran los datos q sobrearon d cosas anteriores
        message_received = self.buffer_sobrante
        self.buffer_sobrante = b""

        # cálculo de máximo a retornar en esta llamada
        limite_esperado = min(self.bytes_por_recibir, buff_size)

        # se recibe contenido hasta cumplir la condición
        while len(message_received) < limite_esperado:
            raw_data, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)
            seg_datos = self.parse_segment(raw_data)

            if seg_datos["fin"]:
                self.buffer_sobrante = raw_data
                return message_received

            siguiente_seq = (seg_datos["seq"] + len(seg_datos["data"])) % 256
            
            if siguiente_seq != self.seq_prev:
                message_received += seg_datos['data']
                self.seq_prev = siguiente_seq

            # se envía ACK de confirmación solo al emisor
            ack_seg = {
                'seq': self.nrosec % 256,
                'ack': self.seq_prev,
                'syn': False,
                'fin': False,
                'data': b''
            }
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
        buff_size = 20
        
        #print(self.nrosec)
        segmento = {'seq': (self.nrosec)%256, 'ack': 0, 'syn': False, 'fin': True, 'data': b""}
        exito = False
        #print(msg)
        
        self.socketUDP.settimeout(2.0)

        fin_recibido = None
        i = 0
        while i < 3:
            try:
                self.socketUDP.sendto(self.create_segment(segmento), self.dirdestino)
                ack, _ = self.socketUDP.recvfrom(buff_size)
                msg = self.parse_segment(ack)
                
                if msg["fin"] == True and msg["ack"] == (self.nrosec + 1)%256:
                    fin_recibido = msg
                    #seg = {'seq': self.nrosec + 2, 'ack': self.nrosec + 2, 'syn': False, 'fin': False, 'data': b""}
                    #self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
                    break
            except socket.timeout:
                i+=1
                print(f"Timeout {i}/3 esperando fin+ack")

        if fin_recibido is not None:
            seg = {'seq': (self.nrosec + 1)%256, 'ack': (fin_recibido['seq'] + 1)%256, 'syn': False, 'fin': False, 'data': b""}
            for i in range(3):
                print(f"ack {i}")
                self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
        else:
            print("3 timeouts")
                
        self.socketUDP.close()

    def recv_close(self):
        buff_size = 20
        self.socketUDP.settimeout(2.0)

        msg = None
        intentos = 0
        # Esperamos el primer FIN
        while intentos < 3:
            try:
                if self.buffer_sobrante:
                    ack = self.buffer_sobrante
                    self.buffer_sobrante = b""
                else:
                    ack, remitente = self.socketUDP.recvfrom(buff_size)
                    self.dirdestino = remitente
                    
                parseado = self.parse_segment(ack)
                if parseado["fin"]:
                    self.dirdestino = remitente
                    msg = parseado
                    break
            except socket.timeout:
                intentos += 1
                continue

        if msg is None:
            self.socketUDP.close()
            return
        
        # Enviamos FIN + ACK y esperamos el ACK final
        seg = {
            'seq': self.nrosec,
            'ack': (msg["seq"] + 1) % 256,
            'syn': False,
            'fin': True,
            'data': b""
        }
        
        intentos2 = 0
        while intentos2 < 3:
            try:
                self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
                final, _ = self.socketUDP.recvfrom(buff_size)
                final_ack = self.parse_segment(final)
                if not final_ack["fin"] and not final_ack["syn"]:
                    break
            except socket.timeout:
                intentos2 += 1
                
        self.socketUDP.close()

