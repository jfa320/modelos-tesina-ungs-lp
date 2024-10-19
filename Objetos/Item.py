class Item:
    def __init__(self, id, alto, posicion_y,rotado):
        self.set_id(id)
        self.set_alto(alto)
        self.set_posicion_y(posicion_y)
        self.set_rotado(rotado)

    def set_id(self, id):
        if isinstance(id, int) and id > 0:
            self.__id = id
        else:
            raise ValueError("El ID debe ser un número entero positivo.")

    def get_id(self):
        return self.__id

    def set_alto(self, alto):
        if isinstance(alto, (int, float)) and alto > 0:
            self.__alto = alto
        else:
            raise ValueError("El alto debe ser un número positivo.")

    def get_alto(self):
        return self.__alto

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
    
    

    def __repr__(self):
        return f"Item(id={self.get_id()}, alto={self.get_alto()}, posicion_y={self.get_posicion_y()})"