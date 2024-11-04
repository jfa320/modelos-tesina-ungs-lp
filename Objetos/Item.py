class Item:
    def __init__(self, alto, posicion_y,rotado,ancho):
        self.set_alto(alto)
        self.set_posicion_y(posicion_y)
        self.set_rotado(rotado)
        self.set_ancho(ancho)

    def set_alto(self, alto):
        if isinstance(alto, (int, float)) and alto > 0:
            self.__alto = alto
        else:
            raise ValueError("El alto debe ser un número positivo.")

    def get_alto(self):
        return self.__alto
    
    def set_ancho(self, ancho):
        if isinstance(ancho, (int, float)) and ancho > 0:
            self.__alto = ancho
        else:
            raise ValueError("El ancho debe ser un número positivo.")

    def get_ancho(self):
        return self.__ancho

    def set_posicion_y(self, posicion_y):
        if isinstance(posicion_y, (int, float)):
            self.__posicion_y = posicion_y
        else:
            raise ValueError("La posición Y debe ser un número.")

    def get_posicion_y(self):
        return self.__posicion_y
    
    def set_rotado(self, rotado):
        if isinstance(rotado, bool):
            self.__rotado = rotado
        else:
            raise ValueError("Rotado debe ser un booleano.")

    def get_rotado(self):
        return self.__rotado
    
    def rotar(self):
        altoAux=self.get_alto()
        self.__alto = self.get_ancho()
        self.__ancho =altoAux
        self.__rotado=not self.get_rotado()

    def __repr__(self):
        return f"Item(id={self.get_id()}, alto={self.get_alto()}, posicion_y={self.get_posicion_y()})"