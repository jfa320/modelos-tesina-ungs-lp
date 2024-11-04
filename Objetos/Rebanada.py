class Rebanada:
    def __init__(self, alto, items):
        self.set_alto(alto)
        self.set_items(items)

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