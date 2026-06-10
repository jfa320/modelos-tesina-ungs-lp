import numpy as np
import itertools

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


def generatePositionsXYM(W, H, w, h):
    # Método de Marcelo mejorado

    Qx = {
        i * w + j * h
        for i in range(W // w + 1)
        for j in range((W - i * w) // h + 1)
    }

    Qy = {
        i * w + j * h
        for i in range(H // w + 1)
        for j in range((H - i * w) // h + 1)
    }

    Qx |= {0, max(0, W - w), max(0, W - h)}
    Qy |= {0, max(0, H - h), max(0, H - w)}

    xSinRotar = sorted(x for x in Qx if x + w <= W)
    ySinRotar = sorted(y for y in Qy if y + h <= H)

    XY_x = set(itertools.product(xSinRotar, ySinRotar))

    if w != h:
        xRotado = sorted(x for x in Qx if x + h <= W)
        yRotado = sorted(y for y in Qy if y + w <= H)

        XY_y = set(itertools.product(xRotado, yRotado))
    else:
        XY_y = set()

    return XY_x, XY_y

def generatePositionsXYM2(W, H, w, h):
    limit = W - h

    Q = {
        i * w + j * h
        for i in range(limit // w + 1)
        for j in range((limit - i * w) // h + 1)
    }

    # Ítem sin rotar: ancho w, alto h
    posicionesXNoRotado = [q for q in Q if q + w <= W]
    posicionesYNoRotado = [q for q in Q if q + h <= H]

    XY_x = set(itertools.product(posicionesXNoRotado, posicionesYNoRotado))

    # Ítem rotado: ancho h, alto w
    if w != h:
        posicionesXRotado = [q for q in Q if q + h <= W]
        posicionesYRotado = [q for q in Q if q + w <= H]

        XY_y = set(itertools.product(posicionesXRotado, posicionesYRotado))
    else:
        XY_y = set()

    return XY_x, XY_y