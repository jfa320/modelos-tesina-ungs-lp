from Objetos import Item

class Rebanada:
    _id_counter = 1

    def __init__(self, alto, ancho, items, posicionesOcupadas=None):
        self.setId(Rebanada._id_counter)
        Rebanada._id_counter += 1
        self.set_alto(alto)
        self.set_ancho(ancho)
        self.set_items(items)
        self.setPosicionesOcupadas(posicionesOcupadas or [])

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

    def set_items(self, items):
        if not isinstance(items, list):
            raise TypeError("Los items deben ser una lista.")
        self.__items = items

    def get_items(self):
        return self.__items
    
    def getTotalItems(self):
        return len(self.__items)

    def contieneItem(self, item):
        if not isinstance(item, Item):
            raise TypeError("El parámetro debe ser un objeto de tipo Item.")
        return item in self.__items

    def setPosicionesOcupadas(self, posiciones):
        if not isinstance(posiciones, list):
            raise TypeError("Las posiciones ocupadas deben ser una lista.")
        if not all(isinstance(pos, tuple) and len(pos) == 2 for pos in posiciones):
            raise ValueError("Cada posición debe ser una tupla (x, y).")
        self.__posicionesOcupadas = posiciones

    def getPosicionesOcupadas(self):
        return self.__posicionesOcupadas

    def agregarPosicionOcupada(self, posicion):
        if not isinstance(posicion, tuple) or len(posicion) != 2:
            raise ValueError("La posición debe ser una tupla (x, y).")
        if posicion not in self.__posicionesOcupadas:
            self.__posicionesOcupadas.append(posicion)

    def eliminarPosicionOcupada(self, posicion):
        if not isinstance(posicion, tuple) or len(posicion) != 2:
            raise ValueError("La posición debe ser una tupla (x, y).")
        if posicion in self.__posicionesOcupadas:
            self.__posicionesOcupadas.remove(posicion)

    def posicionEstaOcupada(self, posicion):
        if not isinstance(posicion, tuple) or len(posicion) != 2:
            raise ValueError("La posición debe ser una tupla (x, y).")
        return posicion in self.__posicionesOcupadas
    
    def appendItem(self, item, posicion=None):
        if not isinstance(item, Item):
            raise TypeError("El parámetro debe ser un objeto de tipo Item.")
        self.__items.append(item)
        self.appendPosicionOcupada(posicion)
    
    def appendPosicionOcupada(self, posicion):
        if not isinstance(posicion, tuple) or len(posicion) != 2:
            raise ValueError("La posición debe ser una tupla (x, y).")
        self.__posicionesOcupadas.append(posicion)
        
    def __repr__(self):
        return (f"Rebanada(id={self.getId()}, alto={self.get_alto()}, ancho={self.get_ancho()}, "
            f"items={self.get_items()}, posicionesOcupadas={self.getPosicionesOcupadas()})")