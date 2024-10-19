class Rebanada:
    def __init__(self, id, alto, items):
        self.set_id(id)
        self.set_alto(alto)
        self.set_items(items)

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

    def set_items(self, items):
        if not isinstance(items, list):
            raise TypeError("Los items deben ser una lista.")
        self.__items = items

    def get_items(self):
        return self.__items

    def __repr__(self):
        return f"Rebanada(id={self.get_id()}, alto={self.get_alto()}, items={self.get_items()})"