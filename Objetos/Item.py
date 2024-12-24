class Item:
    def __init__(self, alto, ancho,rotado):
        self.set_alto(alto)
        self.set_ancho(ancho)
        self.set_rotado(rotado)

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
        return f"Item(alto={self.get_alto()}, ancho={self.get_ancho}, rotado={self.get_rotado})"