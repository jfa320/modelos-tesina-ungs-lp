import numpy as np
import math

def generatePositionsCastro(W, H, w, h):
    # Generar el conjunto de posiciones en el eje x (X)
    X = [x for x in range(W)]

    # Generar el conjunto de posiciones en el eje y (Y)
    Y = [y for y in range(H)]

    # Generar el conjunto de posiciones válidas en el eje x (X_i)
    X_i = [x for x in X if x <= W - w]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    Y_i = [y for y in Y if y <= H - h]

    return X, Y, X_i, Y_i

def generate_positions_no_height_limit(W, H, w, h): #TODO: evaluar si hay que borrarlo porque es del esclavo viejo
    # Generar el conjunto de posiciones en el eje x (X)
    X = [x for x in range(W)]

    # Generar el conjunto de posiciones en el eje y (Y)
    Y = [y for y in range(H)]

    # Generar el conjunto de posiciones válidas en el eje x (X_i)
    X_i = [x for x in X if x <= W - w]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    Y_i = [y for y in Y if y <= H]

    return X, Y, X_i, Y_i

def generate_positions_modelo_maestro(H):#TODO: evaluar si hay que borrarlo porque es del maestro viejo
  
    Y = [y for y in range(H)]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    Y_i = [y for y in Y if y <= H]

    return Y_i

#---------------------------------------------------------
def generatePositionsCidGarcia(W, H, wi, hi):
    positions = []

    # Ciclo externo en 'j' desde el ancho del ítem hasta el ancho del bin
    for j in range(wi, W + 1):
        # Ciclo en 'l' para iterar sobre posibles desplazamientos horizontales
        for l in range(W):
            if (j + l) <= W:  # Validación para asegurar que no se exceda el ancho del bin
                # Ciclo en 'i' desde la altura del ítem hasta la altura del bin
                for i in range(hi, H + 1):
                    # Ciclo en 'k' para iterar sobre posibles desplazamientos verticales
                    for k in range(H):
                        if (k + i) <= H:  # Validación para asegurar que no se exceda la altura del bin
                            # Creación y etiquetado de una nueva posición (j - wi, i - hi) válida para el ítem
                            positions.append((j - wi, i - hi))

    # Eliminamos duplicados en caso de ser necesario
    return list(set(positions))

def createCMatrix(W, H, positions, w, h, points): #usado en los modelos
    num_positions = len(positions)
    num_points = W * H  # Total de puntos en la cuadrícula del bin
    C = np.zeros((num_positions, num_points), dtype=int)
   
    # Enumerar los puntos del bin como coordenadas (x, y)
    points = points
    
    for j, (x_start, y_start) in enumerate(positions):  # Solo usamos x_start y y_start
        for dx in range(w):  # Ancho del item
            for dy in range(h):  # Alto del item
                # Calcular el punto que ocupa la posición (x_start + dx, y_start + dy)
                x = x_start + dx
                y = y_start + dy
                if 0 <= x < W and 0 <= y < H:
                    # Encuentra el índice del punto (x, y) en la lista de puntos
                    p = points.index((x, y))
                    # Marca el punto p en la fila j de la matriz C
                    C[j, p] = 1

    return C

#-------------------------------------------------------------------

def generatePositionsXY(W, H, w, h):
    def axisPositions(binSize, sizes):
        positions = {0} # incluyo siempre la posicion 0
        for s in sizes: # tomo los posibles tamaños que entrarian de los items (en este caso w y h o al reves)
            positions.update(range(0, binSize, s)) # guardo las posiciones en base a los multiplos de cada valor hasta el tamaño del bin
            positions.add(binSize - s)  # incluyo la posicion limite empezando desde atras
        return sorted(p for p in positions if p >= 0 and p < binSize) # ordeno de menor a mayor con p >= 0 y p < binSize
    
    Px = axisPositions(W, [w, h]) # armo las posibles posiciones en el eje x
    Py = axisPositions(H, [h, w]) # armo las posibles posiciones en el eje y 

    XY_x = {(x, y) for x in Px for y in Py if x + w <= W and y + h <= H} # armo los puntos (posiciones finales) para items SIN ROTAR 
                                                                        # usando los Px y Py siempre y cuando entren en el bin
    XY_y = {(x, y) for x in Px for y in Py if x + h <= W and y + w <= H} # armo los puntos (posiciones finales) para items ROTADOS 
                                                                        # usando los Px y Py siempre y cuando entren en el bin

    return XY_x, XY_y

def generatePositionsXYM(W, H, w, h): #metodo Marcelo - parece que anda bien
    # Conjunto Q
    Q = {i * w + j * h for i in range(W // w + 1) for j in range(W // w + 1) if i * w + j * h <= W - h}
    Q = sorted(Q)  # ordeno el conjunto

    # Conjunto P
    P = {x for x in range(0, W - h + 1) if x in Q}

    # Puntos XY para ítems sin rotar (lado largo)
    XY_x = {(x, y) for x in P for y in P if x + w <= W and y + h <= H}

    # Puntos XY para ítems rotados (lado corto)
    XY_y = {(x, y) for x in P for y in P if x + h <= W and y + w <= H}

    return XY_x, XY_y

# def generatePositionsXY1(W, H, w, h):
#     # Qx: posiciones alcanzables en el eje horizontal
#     Qx = {i * w + j * h for i in range(W // w + 1) for j in range(W // h + 1)
#           if i * w + j * h <= W - min(w, h)}
#     Px = sorted(Qx)

#     # Qy: posiciones alcanzables en el eje vertical
#     Qy = {i * h + j * w for i in range(H // h + 1) for j in range(H // w + 1)
#           if i * h + j * w <= H - min(w, h)}
#     Py = sorted(Qy)

#     # Conjuntos de posiciones válidas
#     XY_x = {(x, y) for x in Px for y in Py if x + w <= W and y + h <= H}  # ítem no rotado
#     XY_y = {(x, y) for x in Px for y in Py if x + h <= W and y + w <= H}  # ítem rotado

#     return XY_x, XY_y


# def generatePositionsXYOriginal(anchoBin, altoBin, anchoItem, altoItem):
#     # Constantes
#     W, H, w, h = anchoBin,altoBin,anchoItem,altoItem

#     # Conjunto Q (puntos posibles)
#     Q = {i * w + j * h for i in range(W // w + 1) for j in range(H // h + 1) if i * w + j * h <= W - h}
#     Q = sorted(Q)  # ordeno el conjunto


#     # Conjunto P (pares de posiciones)
#     P = {x for x in range(0, W - h + 1) if x in Q}

#     # Conjuntos que filtran P para que cumplan las condiciones de ancho y alto
#     XY_x = {(x, y) for x in P for y in P if x + w <= W and y + h <= H}

#     XY_y = {(x, y) for x in P for y in P if x + h <= W and y + w <= H}
    
#     return XY_x, XY_y

# def generatePositionsXY1(anchoBin, altoBin, anchoItem, altoItem): #chat
#     W, H = anchoBin, altoBin
#     w, h = anchoItem, altoItem

#     # Ítems NO rotados: ubicarlos de izquierda a derecha, fila por fila
#     XY_x = {(0, y) for y in range(0, H - h + 1)}

#     # Ítems ROTADOS: ubicarlos de arriba hacia abajo, columna por columna
#     XY_y = {(x, 0) for x in range(0, W - h + 1)}

#     return XY_x, XY_y