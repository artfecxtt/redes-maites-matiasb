#debe tener socket UDP, dirección de destino, número de secuencia, todo lo que usted considere necesario.
import socket

class SocketTCP:
    def __init__(self):
        # inicializamos las variables que definen una mascota
        # los datos que aun no sabemos se ponen como None
        self.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dirdestino = ("localhost", 8000)
        self.nrosec = None

    @staticmethod
    #estructura de headers TCP debemos usar bytes directamente. notar forma en que dichos bytes codifican
    #esto es para que pueda pasar segmentos tcp a alguna estructura de datos más cómoda
    def parse_segment(pet_str):
        nueva_mascota = Mascota()
        pet_split = pet_str.split(" ")

        if len(pet_split) > 1:
            nueva_mascota.especie = pet_split[0]
            nueva_mascota.tamanno = pet_split[1]

        return nueva_mascota

    #crea segmentos a partir de dicha estructura de datos
    def create_segment(self, pet_str):
        nueva_mascota = self.parse_mascota(pet_str)
        self.especie = nueva_mascota.especie
        self.peso = nueva_mascota.peso
        self.tamanno = nueva_mascota.tamanno

    def set_peso(self, peso):
        self.peso = peso

    def set_mala_mascota(self):
        print("No, no hay mascotas malas, me niego")

    def is_buena_mascota(self):
        return self.buena_mascota

    def is_chonky(self):
        if self.especie == "gato":
            if self.tamanno == "smol":
                if self.peso > 5:
                    return "está chonky"
                else:
                    return "no está chonky"
            else:
                if self.peso > 7:
                    return "está chonky"
                else:
                    return "no está chonky"
        else:
            return "la verdad es que ni idea, esto es un ejemplo chiquito"

# usamos la clase que recién creamos
mi_gata = Mascota()
mi_gata.set_from_str("gato smol")
mi_gata.set_peso(6)
print(mi_gata.is_chonky())