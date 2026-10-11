#debe tener socket UDP, dirección de destino, número de secuencia, todo lo que usted considere necesario.
import socket
import random
import time

debug = True

def log(mensaje):
    if debug:
        print(f"Debug: {mensaje}")
        
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
        log(f"Socket enlazado a {address}")
        
    def connect(self, address):
        self.dirdestino = address
        self.nrosec = random.randint(0, 100)
        log(f"Iniciando connect hacia {address} con seq={self.nrosec}")

        while True:
            try:
                # se envia el mensaje SYN
                syn_seg = {"seq": self.nrosec % 256, "ack": 0, "syn": True, "fin": False, "data": b""}
                log(f"connect: Enviando SYN (seq = {self.nrosec}")
                self.socketUDP.sendto(self.create_segment(syn_seg), self.dirdestino)
                
                # esperamos por el SYN + ACK
                response, server_new_addr = self.socketUDP.recvfrom(16)
                resp = self.parse_segment(response)
                
                if resp["syn"] and resp["ack"] == (self.nrosec + 1) % 256:
                    log(f"connect: SYN+ACK recibido de {server_new_addr} (seq={resp['seq']}, ack={resp['ack']})")
                    self.dirdestino = server_new_addr
                    self.nrosec = resp["ack"]
                    self.nroack = (resp["seq"] + 1) % 256
                    break
                else:
                    log(f"connect: paquete descartado en handshake, {resp}")
            except socket.timeout:
                log("connect: Timeout esperando SYN+ACK. Reintentando")
                continue

        ack_seg = {"seq": self.nrosec % 256, "ack": self.nroack % 256, "syn": False, "fin": False, "data": b""} #aquí cambié ack. antes tb era nrosec, pero estoy probando cosasS
        log(f"connect: Enviando ACK final de handshake (seq={self.nrosec}, ack={self.nroack})")
        self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)
        print("ta lista la conexión")
    
    def accept(self):
        # se espera por el SYN
        log("Servidor en accept esperando peticiones SYN")
        while True:
            msg, client_addr = self.socketUDP.recvfrom(16)
            seg = self.parse_segment(msg)
            if seg['syn']:
                log(f"accept: SYN recibido desde {client_addr} (seq={seg['seq']})")
                break

        # se crea un socket en un nuevo puerto
        nueva_dir = ('localhost', 8001)
        nuevo_socket = SocketTCP()
        nuevo_socket.bind(nueva_dir)

        # destino y seq
        nuevo_socket.dirdestino = client_addr
        nuevo_socket.nrosec = random.randint(0, 100)
        nuevo_socket.nroack = (seg['seq'] + 1) % 256

        # se envía el SYN + ACK por el nuevo socket
        nuevo_socket.socketUDP.settimeout(2.0)
        syn_ack = {'seq': nuevo_socket.nrosec % 256, 'ack': nuevo_socket.nroack % 256, 'syn': True, 'fin': False, 'data': b''}
        
        while True:
            try:
                log(f"accept: Enviando SYN+ACK hacia {nuevo_socket.dirdestino} (seq={nuevo_socket.nrosec % 256}, ack={nuevo_socket.nroack % 256})")
                nuevo_socket.socketUDP.sendto(self.create_segment(syn_ack), nuevo_socket.dirdestino)
                
                # se espera el ACK final en el 8001
                ack, _ = nuevo_socket.socketUDP.recvfrom(16)
                ack_final = self.parse_segment(ack)
                
                if ack_final['ack'] == (nuevo_socket.nrosec + 1) % 256:
                    log(f"accept: ACK final de handshake recibido correctamente (seq={ack_final['seq']})")
                    nuevo_socket.nrosec = ack_final['ack']
                    nuevo_socket.nroack = (ack_final['seq'] + 1) % 256
                    break
                    
                if not ack_final["syn"] and not ack_final["fin"] and len(ack_final["data"]) > 0:
                    log(f"accept: Caso borde, el ACK final se perdió y llegaron datos anticipados ({len(ack_final['data'])} bytes)")
                    nuevo_socket.nrosec = ack_final['ack'] % 256
                    nuevo_socket.nroack = ack_final['seq'] % 256
                    nuevo_socket.buffer_sobrante = ack
                    break
            except socket.timeout:
                log("accept: Timeout esperando ACK final del handshake. Reenviando SYN+ACK")
                continue
        
        return nuevo_socket, nueva_dir

    def send(self, message):
        buff_size = 20
        msg_length = len(message)
        
        self.socketUDP.settimeout(2.0)
        
        largo_bytes = str(msg_length).encode('utf-8')
        segmento = {'seq': self.nrosec % 256, 'ack': 0, 'syn': False, 'fin': False, 'data': largo_bytes}
        esperado_ack = (self.nrosec + len(largo_bytes)) % 256
        log(f"send: Enviando paquete de longitud ({msg_length} bytes, seq={self.nrosec % 256})")
        
        while True:
            try:
                self.socketUDP.sendto(self.create_segment(segmento), self.dirdestino)
                ack, _ = self.socketUDP.recvfrom(buff_size)
                ack_seg = self.parse_segment(ack)

                if ack_seg['ack'] == esperado_ack:
                    log(f"send: Longitud confirmada con éxito (ACK={ack_seg['ack']})")
                    self.nrosec = esperado_ack
                    break
                else:
                    log(f"send: ACK desalineado o duplicado esperando longitud (recibido={ack_seg['ack']}, esperado={esperado_ack})")
                
            except socket.timeout:
                log("send: Timeout esperando ACK de longitud. Reenviando")
                continue
    
        bytes_enviados = 0
        fragmento_num = 1

        while True:
            pedacito = message[bytes_enviados:bytes_enviados+16]
            if not pedacito:
                break
            seg = {'seq': self.nrosec % 256, 'ack': 0, 'syn': False, 'fin': False, 'data': pedacito}
            esperado_ack = (self.nrosec + len(pedacito)) % 256
            log(f"send: Enviando fragmento número {fragmento_num} (seq={self.nrosec % 256}, len={len(pedacito)})")
            
            while True:
                try:
                    self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
                    ack, _ = self.socketUDP.recvfrom(buff_size)
                    ack_seg = self.parse_segment(ack)

                    if ack_seg['ack'] == esperado_ack:
                        log(f"send: Fragmento número {fragmento_num} confirmado con ACK={ack_seg['ack']}")
                        self.nrosec = esperado_ack
                        bytes_enviados += len(pedacito)
                        fragmento_num += 1
                        break
                    else:
                        log(f"send: ACK repetido/descartado (recibido={ack_seg['ack']}, esperado={esperado_ack})")
                except socket.timeout:
                    log(f"send: Timeout esperando ACK del fragmento número {fragmento_num}. Reenviando por Stop & Wait")
                    continue

        #fin_seg = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': True, 'data': b""}
        #self.socketUDP.sendto(self.create_segment(fin_seg), self.dirdestino)
    
    def recv(self, buff_size):
        udp_buff_size = 20
        self.socketUDP.settimeout(None)
        
        # si los bytes_por_recibir son 0, hay q esperar por el mensaje inicial cn el largo
        if self.bytes_por_recibir == 0:
            log("recv: Iniciando recepción: esperando longitud total del mensaje")
            while True:
                try:
                    if self.buffer_sobrante:
                        msg = self.buffer_sobrante
                        self.buffer_sobrante = b""
                        log("recv: Consumiendo paquete de longitud almacenado previamente en buffer")
                    else:
                        msg, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)
                        
                    seg_largo = self.parse_segment(msg)

                    if seg_largo["fin"]:
                        log("recv: Paquete FIN detectado antes de iniciar transmisión")
                        self.buffer_sobrante = msg
                        return b""

                    # tolerancia pérdidas
                    try:
                        # se saca la longitud
                        message_length = int(seg_largo['data'].decode('utf-8'))
                        self.seq_prev = (seg_largo["seq"] + len(seg_largo['data'])) % 256
                        self.bytes_por_recibir = message_length
                        log(f"recv: Longitud total decodificada: {message_length} bytes. Próximo seq esperado={self.seq_prev}")

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
                        log("recv: Segmento residual o duplicado recibido. Reenviando ACK acumulativo para desatascar al emisor")
                        ack_seg = {
                            'seq': self.nrosec % 256,
                            'ack': self.seq_prev,
                            'syn': False,
                            'fin': False,
                            'data': b''
                        }
                        self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)
                        continue
                except socket.timeout:
                    log("recv: Timeout esperando longitud. Continuando escucha activa")
                    

        # se agarran los datos q sobrearon d cosas anteriores
        message_received = self.buffer_sobrante
        self.buffer_sobrante = b""

        # cálculo de máximo a retornar en esta llamada
        limite_esperado = min(self.bytes_por_recibir, buff_size)
        log(f"recv: Reuniendo datos: actualmente {len(message_received)}/{limite_esperado} bytes solicitados")

        # se recibe contenido hasta cumplir la condición
        while len(message_received) < limite_esperado:
            try:
                raw_data, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)
                seg_datos = self.parse_segment(raw_data)

                if seg_datos["fin"]:
                    log("recv: FIN detectado durante transferencia de datos. Finalizando lectura")
                    self.buffer_sobrante = raw_data
                    return message_received

                siguiente_seq = (seg_datos["seq"] + len(seg_datos["data"])) % 256
                
                if siguiente_seq != self.seq_prev:
                    log(f"recv: Datos nuevos recibidos, {len(seg_datos['data'])} bytes (seq={seg_datos['seq']})")
                    message_received += seg_datos['data']
                    self.seq_prev = siguiente_seq
                else:
                    log(f"recv: Paquete duplicado detectado (seq={seg_datos['seq']}). Descartando carga útil")

                # se envía ACK de confirmación solo al emisor
                ack_seg = {
                    'seq': self.nrosec % 256,
                    'ack': self.seq_prev,
                    'syn': False,
                    'fin': False,
                    'data': b''
                }
                self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)
            except socket.timeout:
                log("recv: Timeout esperando fragmento de datos. Manteniendo socket en escucha")
                continue

        # si se recibe más de buff_size
        if len(message_received) > buff_size:
            self.buffer_sobrante = message_received[buff_size:] #se guarda lo q sobre
            resultado = message_received[:buff_size] # se retorna lo q se pide
            log(f"recv: Buffer saturado, retornando {len(resultado)} bytes, guardando {len(self.buffer_sobrante)} bytes sobrantes")
        else:
            resultado = message_received

        # se restan los bytes entregado
        self.bytes_por_recibir -= len(resultado)
        log(f"recv: Llamada lista. Bytes restantes por recibir en el flujo: {self.bytes_por_recibir}")
        return resultado
        
    def close(self):
        buff_size = 20
        
        #print(self.nrosec)
        segmento = {'seq': (self.nrosec)%256, 'ack': 0, 'syn': False, 'fin': True, 'data': b""}
        exito = False
        #print(msg)
        
        self.socketUDP.settimeout(2.0)
        log("close: Iniciando protocolo de cierre activo")

        fin_recibido = None
        i = 0
        while i < 3:
            try:
                log(f"close: Enviando paquete FIN (intento {i+1}/3, seq={self.nrosec % 256})")
                self.socketUDP.sendto(self.create_segment(segmento), self.dirdestino)
                ack, _ = self.socketUDP.recvfrom(buff_size)
                msg = self.parse_segment(ack)
                
                if msg["fin"] == True and msg["ack"] == (self.nrosec + 1)%256:
                    log(f"close: FIN+ACK recibido con éxito desde la contraparte (seq={msg['seq']})")
                    fin_recibido = msg
                    #seg = {'seq': self.nrosec + 2, 'ack': self.nrosec + 2, 'syn': False, 'fin': False, 'data': b""}
                    #self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
                    break
                else:
                    log(f"close: Paquete ignorado mientras se esperaba FIN+ACK: {msg}")
            except socket.timeout:
                i+=1
                log(f"close: Timeout {i}/3 esperando confirmación FIN+ACK")

        if fin_recibido is not None:
            seg = {'seq': (self.nrosec + 1)%256, 'ack': (fin_recibido['seq'] + 1)%256, 'syn': False, 'fin': False, 'data': b""}
            log("close: Enviando 3 ráfagas de confirmación final ACK espaciadas por timeout")
            for j in range(3):
                log(f"close: Enviando ACK final de cierre número {j+1}/3")
                self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
        else:
            log("close: 3 timeouts alcanzados sin respuesta, asumiendo cierre unilateral")
                
        self.socketUDP.close()
        log("close: Socket liberado")

    def recv_close(self):
        buff_size = 20
        self.socketUDP.settimeout(2.0)
        log("recv_close: Iniciando protocolo de cierre pasivo")

        msg = None
        intentos = 0
        # Esperamos el primer FIN
        while intentos < 3:
            try:
                if self.buffer_sobrante:
                    ack = self.buffer_sobrante
                    self.buffer_sobrante = b""
                    log("recv_close: Consumiendo FIN residual almacenado previamente en buffer")
                else:
                    ack, remitente = self.socketUDP.recvfrom(buff_size)
                    self.dirdestino = remitente
                    
                parseado = self.parse_segment(ack)
                if parseado["fin"]:
                    log(f"recv_close: FIN recibido desde {self.dirdestino} (seq={parseado['seq']})")
                    self.dirdestino = remitente
                    msg = parseado
                    break
                else:
                    log(f"recv_close: Paquete no-FIN ignorado: {parseado}")
            except socket.timeout:
                intentos += 1
                log(f"recv_close: Timeout {intentos}/3 esperando primer FIN")
                continue

        if msg is None:
            log("recv_close: No se recibió FIN tras 3 timeouts, cerrando conexión unilateralmente")
            self.socketUDP.close()
            return
        
        # Enviamos FIN + ACK y esperamos el ACK final
        seg = {
            'seq': self.nrosec % 256,
            'ack': (msg["seq"] + 1) % 256,
            'syn': False,
            'fin': True,
            'data': b""
        }
        
        intentos2 = 0
        while intentos2 < 3:
            try:
                log(f"recv_close: Enviando FIN+ACK (intento {intentos2+1}/3)")
                self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
                final, _ = self.socketUDP.recvfrom(buff_size)
                final_ack = self.parse_segment(final)
                if not final_ack["fin"] and not final_ack["syn"]:
                    log("recv_close: ACK final de la contraparte recibido con éxito")
                    break
            except socket.timeout:
                intentos2 += 1
                log(f"recv_close: Timeout {intentos2}/3 esperando el último ACK de la contraparte")
                
        self.socketUDP.close()
        log("recv_close: Socket liberado")
