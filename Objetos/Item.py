class Item:
    _id_counter = 1
    
    def __init__(self, alto, ancho, rotado=False, id=None, posicion_x=None, posicion_y=None):
        if id is None:
            self.set_id(Item._id_counter)
            Item._id_counter += 1
        else:
            self.set_id(id)
        self.set_alto(alto)
        self.set_ancho(ancho)
        self.set_rotado(rotado)
        self.set_posicion_x(posicion_x)
        self.set_posicion_y(posicion_y)

    def set_id(self, id):
        if isinstance(id, int) and id > 0:
            self.__id = id
        else:
            raise ValueError("El id debe ser un número entero positivo.")

    def get_id(self):
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
        alto_aux = self.get_alto()
        self.__alto = self.get_ancho()
        self.__ancho = alto_aux
        self.__rotado = not self.get_rotado()

    def set_posicion_x(self, x):
        if isinstance(x, (int, float)) or x is None:
            self.__posX = x
        else:
            raise ValueError("La posición X debe ser un número o None.")

    def get_posicion_x(self):
        return self.__posX

    def set_posicion_y(self, y):
        if isinstance(y, (int, float)) or y is None:
            self.__posY = y
        else:
            raise ValueError("La posición Y debe ser un número o None.")

    def get_posicion_y(self):
        return self.__posY
    
    def get_posicion(self):
        return (self.get_posicion_x(), self.get_posicion_y())
    
    def set_posicion(self, x, y):
        self.set_posicion_x(x)
        self.set_posicion_y(y)

    def __repr__(self):
        return (f"Item(id={self.get_id()}, alto={self.get_alto()}, ancho={self.get_ancho()}, "
                f"rotado={self.get_rotado()}, x={self.get_posicion_x()}, y={self.get_posicion_y()})")
    
    def __eq__(self, other):
        return self.get_id() == other.get_id()
