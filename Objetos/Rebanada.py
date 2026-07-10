from Objetos import Item

class Rebanada:
    _id_counter = 1

    @classmethod
    def reset_id_counter(cls):
        cls._id_counter = 1

    def __init__(self, alto, ancho, items=None, puntos_de_inicio_items=None):
        self.set_id(Rebanada._id_counter)
        Rebanada._id_counter += 1
        self.set_alto(alto)
        self.set_ancho(ancho)
        self.set_items(items or [])
        self.set_puntos_de_inicio_items(puntos_de_inicio_items or [])
        if self.get_puntos_de_inicio_items() is None or self.get_puntos_de_inicio_items() == []:
            self.colocar_puntos_inicio_items()


    def colocar_puntos_inicio_items(self):
        for item in self.get_items():
            x = item.get_posicion_x()
            y = item.get_posicion_y()
            self.__puntosDeInicioItems.append((x, y))

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

    def set_items(self, items):
        if not isinstance(items, list):
            raise TypeError("Los items deben ser una lista.")
        self.__items = items

    def get_items(self):
        return self.__items
    
    def get_total_items(self):
        return len(self.__items)

    def contiene_item(self, item):
        if not isinstance(item, Item):
            raise TypeError("El parámetro debe ser un objeto de tipo Item.")
        return item in self.__items

    def set_puntos_de_inicio_items(self, posiciones):
        if not isinstance(posiciones, list):
            raise TypeError("Las posiciones ocupadas deben ser una lista.")
        if not all(isinstance(pos, tuple) and len(pos) == 2 for pos in posiciones):
            raise ValueError("Cada posición debe ser una tupla (x, y).")
        self.__puntosDeInicioItems = posiciones

    def get_puntos_de_inicio_items(self):
        return self.__puntosDeInicioItems

    def _append_item(self, item, posicion=None):
        if not isinstance(item, Item):
            raise TypeError("El parámetro debe ser un objeto de tipo Item.")
        self.__items.append(item)
        self.append_posicion_inicio_de_item(posicion)
    
    def append_posicion_inicio_de_item(self, posicion):
        if not isinstance(posicion, tuple) or len(posicion) != 2:
            raise ValueError("La posición debe ser una tupla (x, y).")
        self.__puntosDeInicioItems.append(posicion)
        
    def colocar_item(self, nuevo_item, x, y):
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError("Las coordenadas deben ser números.")
        
        if (x, y) in self.__puntosDeInicioItems:
            raise ValueError("La posición ya está ocupada.")
        
        nuevo_item.set_posicion_x(x)
        nuevo_item.set_posicion_y(y)
        # Agregar a la lista de ítems y posiciones ocupadas
        self._append_item(nuevo_item, (x, y))
            
    def __repr__(self):
        return (f"Rebanada(id={self.get_id()}, alto={self.get_alto()}, ancho={self.get_ancho()}, "
            f"items={self.get_items()}, puntos_de_inicio_items={self.get_puntos_de_inicio_items()})")
