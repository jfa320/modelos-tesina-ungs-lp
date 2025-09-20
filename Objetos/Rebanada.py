from Objetos import Item

class Rebanada:
    _id_counter = 1

    def __init__(self, alto, ancho, items=None, puntosDeInicioItems=None):
        self.setId(Rebanada._id_counter)
        Rebanada._id_counter += 1
        self.set_alto(alto)
        self.set_ancho(ancho)
        self.setItems(items or [])
        self.setPuntosDeInicioItems(puntosDeInicioItems or [])

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

    def setItems(self, items):
        if not isinstance(items, list):
            raise TypeError("Los items deben ser una lista.")
        self.__items = items

    def getItems(self):
        return self.__items
    
    def getTotalItems(self):
        return len(self.__items)

    def contieneItem(self, item):
        if not isinstance(item, Item):
            raise TypeError("El parámetro debe ser un objeto de tipo Item.")
        return item in self.__items

    def setPuntosDeInicioItems(self, posiciones):
        if not isinstance(posiciones, list):
            raise TypeError("Las posiciones ocupadas deben ser una lista.")
        if not all(isinstance(pos, tuple) and len(pos) == 2 for pos in posiciones):
            raise ValueError("Cada posición debe ser una tupla (x, y).")
        self.__puntosDeInicioItems = posiciones

    def getPuntosDeInicioItems(self):
        return self.__puntosDeInicioItems

    def _appendItem(self, item, posicion=None):
        if not isinstance(item, Item):
            raise TypeError("El parámetro debe ser un objeto de tipo Item.")
        self.__items.append(item)
        self.appendPosicionInicioDeItem(posicion)
    
    def appendPosicionInicioDeItem(self, posicion):
        if not isinstance(posicion, tuple) or len(posicion) != 2:
            raise ValueError("La posición debe ser una tupla (x, y).")
        self.__puntosDeInicioItems.append(posicion)
        
    def colocarItem(self, nuevoItem, x, y):
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError("Las coordenadas deben ser números.")
        
        if (x, y) in self.__puntosDeInicioItems:
            raise ValueError("La posición ya está ocupada.")
        
        nuevoItem.setPosicionX(x)
        nuevoItem.setPosicionY(y)
        # Agregar a la lista de ítems y posiciones ocupadas
        self._appendItem(nuevoItem, (x, y))
            
    def __repr__(self):
        return (f"Rebanada(id={self.getId()}, alto={self.get_alto()}, ancho={self.get_ancho()}, "
            f"items={self.getItems()}, posicionesOcupadas={self.getPuntosDeInicioItems()})")