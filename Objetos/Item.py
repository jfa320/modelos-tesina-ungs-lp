class Item:
    _id_counter = 1
    
    def __init__(self, alto, ancho, rotado=False, id=None,posicionX=None, posicionY=None):
        if id is None:
            self.setId(Item._id_counter)
            Item._id_counter += 1
        else:
            self.setId(id)
        self.setAlto(alto)
        self.setAncho(ancho)
        self.setRotado(rotado)
        self.setPosicionX(posicionX)
        self.setPosicionY(posicionY)

    def setId(self, id):
        if isinstance(id, int) and id > 0:
            self.__id = id
        else:
            raise ValueError("El id debe ser un número entero positivo.")

    def getId(self):
        return self.__id
    
    def setAlto(self, alto):
        if isinstance(alto, (int, float)) and alto > 0:
            self.__alto = alto
        else:
            raise ValueError("El alto debe ser un número positivo.")

    def getAlto(self):
        return self.__alto
    
    def setAncho(self, ancho):
        if isinstance(ancho, (int, float)) and ancho > 0:
            self.__ancho = ancho
        else:
            raise ValueError("El ancho debe ser un número positivo.")

    def getAncho(self):
        return self.__ancho
    
    def setRotado(self, rotado):
        if isinstance(rotado, bool):
            self.__rotado = rotado
        else:
            raise ValueError("Rotado debe ser un booleano.")

    def getRotado(self):
        return self.__rotado
    
    def rotar(self):
        altoAux = self.getAlto()
        self.__alto = self.getAncho()
        self.__ancho = altoAux
        self.__rotado = not self.get_rotado()

    def setPosicionX(self, x):
        if isinstance(x, (int, float)) or x is None:
            self.__posX = x
        else:
            raise ValueError("La posición X debe ser un número o None.")

    def getPosicionX(self):
        return self.__posX

    def setPosicionY(self, y):
        if isinstance(y, (int, float)) or y is None:
            self.__posY = y
        else:
            raise ValueError("La posición Y debe ser un número o None.")

    def getPosicionY(self):
        return self.__posY
    
    def getPosicion(self):
        return (self.getPosicionX(), self.getPosicionY())
    
    def setPosicion(self, x, y):
        self.setPosicionX(x)
        self.setPosicionY(y)

    def __repr__(self):
        return (f"Item(id={self.getId()}, alto={self.getAlto()}, ancho={self.getAncho()}, "
                f"rotado={self.getRotado()}, x={self.getPosicionX()}, y={self.getPosicionY()})")
    
    def __eq__(self, other):
        return self.getId() == other.getId()
