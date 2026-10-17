#debe tener socket UDP, dirección de destino, número de secuencia, todo lo que usted considere necesario.
import socket
import random
from socketUDP import SocketUDP
from slidingWindowCC import SlidingWindowCC
from CongestionControl import CongestionControl

debug = True

def log(mensaje):
    if debug:
        print(f"Debug: {mensaje}")
        
class SocketTCP:
    def __init__(self):
        # inicializamos las variables que definen una mascota

        # los datos que aun no sabemos se ponen como None

        self.socketUDP = SocketUDP()
        self.dirdestino = ("localhost", 8000)
        self.nrosec = 0
        self.congestion_control_on = True
        self.congestion_controler = CongestionControl(MSS=8)
        self.max_ventana = 15
        self.nroack = 0
        self.bytes_por_recibir = 0
        self.buffer_sobrante = b""
        self.seq_prev = 0

    def set_cc(self, var):
        if isinstance(var, bool):
            self.congestion_control_on = var
    
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

        ack_seg = {"seq": self.nrosec % 256, "ack": self.nroack % 256, "syn": False, "fin": False, "data": b""} #aquí cambié ack. antes tb era nrosec, pero estoy probando cosas
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

    # -------------------------------- esto es nuevo de la act goback ----------------------------------------
    #stop_and_wait go_back_n
    def send(self, message, mode="go_back_n"):
        if mode == "stop_and_wait":
            return self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            return self.send_using_go_back_n(message)
    
    def recv(self, buff_size, mode="go_back_n"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

    # -------------------------------- aquí se acaba lo nuevo de la act ---------------------------------------
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

    #----------------------------------------------- actividad goback n -------------------------------------------------------

    def send_using_stop_and_wait(self, message):
        buff_size = 20
        msg_length = len(message)
        
        self.socketUDP.settimeout(2.0)
        
        largo_bytes = str(msg_length).encode('utf-8')
        segmento = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': False, 'data': largo_bytes}
        
        while True:
            try:
                self.socketUDP.sendto(self.create_segment(segmento), self.dirdestino)
                ack, _ = self.socketUDP.recvfrom(buff_size)
                self.nrosec += len(largo_bytes)
                break
            except socket.timeout:
                continue
    
        bytes_enviados = 0

        while True:
            pedacito = message[bytes_enviados:bytes_enviados+16]
            if not pedacito:
                break
            seg = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': False, 'data': pedacito}
            
            while True:
                try:
                    self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)
                    ack, _ = self.socketUDP.recvfrom(buff_size)
                    self.nrosec += len(pedacito)
                    bytes_enviados += len(pedacito)
                    break
                except socket.timeout:
                    continue

    def recv_using_stop_and_wait(self, buff_size):
        udp_buff_size = 20

        # si los bytes_por_recibir son 0, hay q esperar por el mensaje inicial cn el largo
        if self.bytes_por_recibir == 0:
            if self.buffer_sobrante:
                msg = self.buffer_sobrante
                self.buffer_sobrante = b""
            else:
                msg, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)
                
            seg_largo = self.parse_segment(msg)
            # se saca la longitud
            message_length = int(seg_largo['data'].decode('utf-8'))
            self.seq_prev = seg_largo["seq"]
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
            
            if seg_datos["seq"] + len(seg_datos["data"]) != self.seq_prev:
                message_received += seg_datos['data']
                self.seq_prev = seg_datos["seq"] + len(seg_datos["data"])

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

    def detener_timer(self, i=0):
        if self.socketUDP.timer_list[i] is not None:
            self.socketUDP.stop_timer(i)
            
    def send_using_go_back_n(self, message):
        debug = True
        buff_size = 12
        mss = 8
        msg_length = len(message)
        
        self.socketUDP.settimeout(2.0)

        # --- 1. enviar el largo del mensaje (stop & wait) ---
        largo_bytes = str(msg_length).encode('utf-8')
        segmento = {'seq': self.nrosec, 'ack': 0, 'syn': False, 'fin': False, 'data': largo_bytes}
        while True:
            try:
                self.socketUDP.sendto(self.create_segment(segmento), self.dirdestino)
                ack, _ = self.socketUDP.recvfrom(buff_size)
                self.detener_timer(0)
                resp = self.parse_segment(ack)
                if resp['ack'] == (self.nrosec + len(largo_bytes)) % 256:
                    self.nrosec = resp['ack']
                    break
            except TimeoutError:
                self.detener_timer(0)      # limpia el timer vencido antes de reintentar

        if msg_length == 0:
            return

        # --- 2. enviar los datos con Go Back-N ---
        lista_data = [message[i:i + mss] for i in range(0, msg_length, mss)]
        segmentos_totales = len(lista_data)

        init_win = None
        if self.congestion_control_on:
            init_win = max(1, min(int(self.congestion_controler.get_MSS_in_cwnd()), self.max_ventana))
        else:
            init_win = 8
        
        sw = SlidingWindowCC(window_size=init_win, data_list=lista_data, initial_seq=self.nrosec)

        proximo_a_enviar = 0        # cuántos segmentos de la ventana ya se enviaron
        segmentos_confirmados = 0

        if debug:
            print("\n" + "=" * 60)
            print("--- inicio transmisión de go-back-n ---")
            print(f"total de segmentos: {segmentos_totales}, cc activo? -> {self.congestion_control_on}")
            print(f"window_size inicial: {sw.window_size}, cwnd: {self.congestion_controler.get_cwnd()}")
            print("=" * 60)

        while segmentos_confirmados < segmentos_totales:
            # actualizar la ventana dinámicamente si el control de congestión está encendido
            #if self.congestion_control_on:
              #  sw.window_size = max(1, self.congestion_controler.cwnd//mss)
                
            # enviar lo que falte de la ventana
            while (not self.socketUDP.announce_timeout[0] and proximo_a_enviar < sw.window_size and sw.get_data(proximo_a_enviar) is not None):
                seq_num = sw.get_sequence_number(proximo_a_enviar)
                seg = {'seq': sw.get_sequence_number(proximo_a_enviar), 'ack': 0, 'syn': False,
                       'fin': False, 'data': sw.get_data(proximo_a_enviar)}
                self.socketUDP.sendto(self.create_segment(seg), self.dirdestino)

                if debug:
                    base_seq = sw.get_sequence_number(0)
                    print(f"(enviado) seq: {seq_num:<3}, posición ventana: {proximo_a_enviar}/{sw.window_size}, base: {base_seq}, cwnd: {self.congestion_controler.get_cwnd()}")
                proximo_a_enviar += 1

            # si hay segmentos sin confirmar pero no hay timer corriendo,
            # reenviamos el base para reiniciarlo
            if (proximo_a_enviar > 0 and self.socketUDP.timer_list[0] is None and not self.socketUDP.announce_timeout[0]):
                seg_base = {'seq': sw.get_sequence_number(0), 'ack': 0, 'syn': False,
                            'fin': False, 'data': sw.get_data(0)}
                self.socketUDP.sendto(self.create_segment(seg_base), self.dirdestino)
                if debug:
                    print(f"(retransmisión base) timer inactivo. reenviando seq base: {sw.get_sequence_number(0)}")

            try:
                ack_crudo, _ = self.socketUDP.recvfrom(buff_size)
                ack_numero = self.parse_segment(ack_crudo)['ack']

                # ACK acumulativo: buscamos el último segmento enviado que coincide
                base = sw.get_sequence_number(0)
                por_confirmar = (ack_numero-base)%256
                pasos_a_moverse = 0
                for i in range(proximo_a_enviar):
                    ack_esperado = (sw.get_sequence_number(i) + len(sw.get_data(i))) % 256
                    if ack_numero == ack_esperado:
                        pasos_a_moverse = i + 1

                if pasos_a_moverse == 0 and 0 < por_confirmar < 128:
                    while por_confirmar > 0 and sw.get_data(0) is not None:
                        por_confirmar -= len(sw.get_data(0))
                        sw.move_window(1)
                        pasos_a_moverse += 1
                    ya_movida = True
                else:
                    ya_movida = False
                
                if pasos_a_moverse > 0:
                    if proximo_a_enviar - pasos_a_moverse <= 0:
                        self.detener_timer(0)

                    if debug:
                        print(f"(ack recibido) ack #{ack_numero}, avanzando ventana {pasos_a_moverse} posición(es)")

                    if not ya_movida:
                        sw.move_window(pasos_a_moverse)
                    
                    segmentos_confirmados += pasos_a_moverse
                    proximo_a_enviar = max(0, proximo_a_enviar - pasos_a_moverse)
                    self.nrosec = ack_numero

                    if self.congestion_control_on:
                        for _ in range(pasos_a_moverse):
                            self.congestion_controler.event_ack_received()
                        sw.update_window_size(max(1, min(self.congestion_controler.get_MSS_in_cwnd(), self.max_ventana)))
                        proximo_a_enviar = min(proximo_a_enviar, sw.window_size)
                        if debug:
                            if self.congestion_controler.is_state_slow_start():
                                estado = "slow start"
                            else:
                                estado = "congestion avoidance"
                            print(f"actualización cc: nueva cwnd -> {self.congestion_controler.cwnd}, ssthresh: {self.congestion_controler.ssthresh}, window_size: {sw.window_size}, estado: {estado}")
                            
            except TimeoutError:
                self.detener_timer(0)

                if debug:
                    print(f"\n(timeout) hubo pérdida. reiniciando ventana (go-back-n de {proximo_a_enviar} paquetes")
                    
                proximo_a_enviar = 0        # Go Back-N: reenviar toda la ventana
                if self.congestion_control_on:
                    self.congestion_controler.event_timeout()
                    sw.update_window_size(min(self.congestion_controler.get_MSS_in_cwnd(), self.max_ventana))
                    if debug:
                        print(f"actualización cc: nueva cwnd -> {self.congestion_controler.cwnd}, ssthresh: {self.congestion_controler.ssthresh}")
                    
        self.detener_timer(0)
        if debug:
            print("="*60)
            print("--- transmisión bien terminada ---")
            print("="*60+"\n")
                            
    def recv_using_go_back_n(self, buff_size):
        udp_buff_size = 12

        self.detener_timer(0)
        self.socketUDP.settimeout(-1)

        # 1. Mensaje inicial con la longitud
        if self.bytes_por_recibir == 0:
            while True:
                if len(self.buffer_sobrante) > 0:
                    msg = self.buffer_sobrante
                    self.buffer_sobrante = b""
                else:
                    msg, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)

                seg_largo = self.parse_segment(msg)

                # Intentar convertir la longitud a entero
                try:
                    message_length = int(seg_largo['data'].decode('utf-8'))
                    break  # Si es un número válido, salimos del bucle y continuamos
                except (ValueError, UnicodeDecodeError):
                    # Si es basura o un paquete retrasado del mensaje anterior,
                    # respondemos ACK del estado actual y reintentamos la lectura del socket
                    ack_seg = {'seq': self.nrosec % 256, 'ack': self.seq_prev,
                               'syn': False, 'fin': False, 'data': b''}
                    self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)
                    # El bucle 'while True' volverá a ejecutar recvfrom() para sacar el paquete correcto

            # El primer byte de datos esperado empieza en:
            self.seq_prev = (seg_largo["seq"] + len(seg_largo["data"])) % 256
            self.bytes_por_recibir = message_length

            # Confirmar el mensaje de longitud
            ack_seg = {'seq': self.nrosec % 256, 'ack': self.seq_prev,
                       'syn': False, 'fin': False, 'data': b''}
            self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)

        # 2. Rescatar sobrante previo
        message_received = self.buffer_sobrante
        self.buffer_sobrante = b""
        limite_esperado = min(self.bytes_por_recibir, buff_size)

        # 3. Bucle de recepción
        while len(message_received) < limite_esperado:
            raw_data, self.dirdestino = self.socketUDP.recvfrom(udp_buff_size)
            seg_datos = self.parse_segment(raw_data)

            # Go Back-N: solo aceptamos el segmento si su seq es el esperado
            if seg_datos["seq"] == self.seq_prev:
                message_received += seg_datos['data']
                self.seq_prev = (seg_datos["seq"] + len(seg_datos["data"])) % 256

            # siempre se envía ACK acumulativo hasta seq_prev
            ack_seg = {'seq': self.nrosec % 256, 'ack': self.seq_prev,
                       'syn': False, 'fin': False, 'data': b''}
            self.socketUDP.sendto(self.create_segment(ack_seg), self.dirdestino)

        # 4. Manejo de sobrante
        if len(message_received) > buff_size:
            self.buffer_sobrante = message_received[buff_size:]
            resultado = message_received[:buff_size]
        else:
            resultado = message_received

        self.bytes_por_recibir -= len(resultado)
        return resultado
