class Item:
    _id_counter = 1
    
    def __init__(self, alto, ancho,rotado=False,id=None):
        if(id==None):
            self.setId(Item._id_counter)
            Item._id_counter += 1
        else:
            self.setId(id)
        self.set_alto(alto)
        self.set_ancho(ancho)
        self.set_rotado(rotado)

    def setId(self, id):
        if isinstance(id, int) and id > 0:
            self.__id = id
        else:
            raise ValueError("El id debe ser un número entero positivo.")

    def getId(self):
        return self.__id
    
    def set_alto(self, alto):
        if isinstance(alto, (int, float)) and alto > 0:
            self.__alto = alto
        else:
            raise ValueError("El alto debe ser un número positivo.")

    def get_alto(self):
        return self.__alto
    
    def set_ancho(self, ancho):
        if isinstance(ancho, (int, float)) and ancho > 0:
            self.__ancho = ancho
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
        return f"Item(id={self.getId()},alto={self.get_alto()}, ancho={self.get_ancho()}, rotado={self.get_rotado()})"
    
    def __eq__(self, other):
        return self.getId() == other.getId()