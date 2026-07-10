import numpy as np
import itertools

def generate_positions_castro(bin_width, bin_height, item_width, item_height):
    # Generar el conjunto de posiciones en el eje x (X)
    x_positions = [x for x in range(bin_width)]

    # Generar el conjunto de posiciones en el eje y (Y)
    y_positions = [y for y in range(bin_height)]

    # Generar el conjunto de posiciones válidas en el eje x (X_i)
    valid_x_positions = [x for x in x_positions if x <= bin_width - item_width]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    valid_y_positions = [y for y in y_positions if y <= bin_height - item_height]

    return x_positions, y_positions, valid_x_positions, valid_y_positions

def generate_positions_no_height_limit(bin_width, bin_height, item_width, item_height): #TODO: evaluar si hay que borrarlo porque es del esclavo viejo
    # Generar el conjunto de posiciones en el eje x (X)
    x_positions = [x for x in range(bin_width)]

    # Generar el conjunto de posiciones en el eje y (Y)
    y_positions = [y for y in range(bin_height)]

    # Generar el conjunto de posiciones válidas en el eje x (X_i)
    valid_x_positions = [x for x in x_positions if x <= bin_width - item_width]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    valid_y_positions = [y for y in y_positions if y <= bin_height]

    return x_positions, y_positions, valid_x_positions, valid_y_positions

def generate_positions_modelo_maestro(bin_height):#TODO: evaluar si hay que borrarlo porque es del maestro viejo
  
    y_positions = [y for y in range(bin_height)]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    valid_y_positions = [y for y in y_positions if y <= bin_height]

    return valid_y_positions

#---------------------------------------------------------
def generate_positions_cid_garcia(bin_width, bin_height, item_width, item_height):
    positions = []

    # Ciclo externo en 'j' desde el ancho del ítem hasta el ancho del bin
    for j in range(item_width, bin_width + 1):
        # Ciclo en 'l' para iterar sobre posibles desplazamientos horizontales
        for l in range(bin_width):
            if (j + l) <= bin_width:  # Validación para asegurar que no se exceda el ancho del bin
                # Ciclo en 'i' desde la altura del ítem hasta la altura del bin
                for i in range(item_height, bin_height + 1):
                    # Ciclo en 'k' para iterar sobre posibles desplazamientos verticales
                    for k in range(bin_height):
                        if (k + i) <= bin_height:  # Validación para asegurar que no se exceda la altura del bin
                            # Creación y etiquetado de una nueva posición (j - wi, i - hi) válida para el ítem
                            positions.append((j - item_width, i - item_height))

    # Eliminamos duplicados en caso de ser necesario
    return list(set(positions))

def create_c_matrix(bin_width, bin_height, positions, item_width, item_height, points): #usado en los modelos
    num_positions = len(positions)
    num_points = bin_width * bin_height  # Total de puntos en la cuadrícula del bin
    c_matrix = np.zeros((num_positions, num_points), dtype=int)
   
    # Enumerar los puntos del bin como coordenadas (x, y)
    points = points
    
    for j, (x_start, y_start) in enumerate(positions):  # Solo usamos x_start y y_start
        for dx in range(item_width):  # Ancho del item
            for dy in range(item_height):  # Alto del item
                # Calcular el punto que ocupa la posición (x_start + dx, y_start + dy)
                x = x_start + dx
                y = y_start + dy
                if 0 <= x < bin_width and 0 <= y < bin_height:
                    # Encuentra el índice del punto (x, y) en la lista de puntos
                    p = points.index((x, y))
                    # Marca el punto p en la fila j de la matriz C
                    c_matrix[j, p] = 1

    return c_matrix

#-------------------------------------------------------------------


def generate_positions_xym(bin_width, bin_height, item_width, item_height):
    # Método de Marcelo mejorado

    q_x = {
        i * item_width + j * item_height
        for i in range(bin_width // item_width + 1)
        for j in range((bin_width - i * item_width) // item_height + 1)
    }

    q_y = {
        i * item_width + j * item_height
        for i in range(bin_height // item_width + 1)
        for j in range((bin_height - i * item_width) // item_height + 1)
    }

    q_x |= {0, max(0, bin_width - item_width), max(0, bin_width - item_height)}
    q_y |= {0, max(0, bin_height - item_height), max(0, bin_height - item_width)}

    x_sin_rotar = sorted(x for x in q_x if x + item_width <= bin_width)
    y_sin_rotar = sorted(y for y in q_y if y + item_height <= bin_height)

    xy_x = set(itertools.product(x_sin_rotar, y_sin_rotar))

    if item_width != item_height:
        x_rotado = sorted(x for x in q_x if x + item_height <= bin_width)
        y_rotado = sorted(y for y in q_y if y + item_width <= bin_height)

        xy_y = set(itertools.product(x_rotado, y_rotado))
    else:
        xy_y = set()

    return xy_x, xy_y

def generate_positions_xym2(bin_width, bin_height, item_width, item_height):
    # Precondicion del metodo: dimensiones normalizadas con bin_width >= bin_height e item_width >= item_height.
    # El orquestador normaliza la instancia antes de llamar a esta funcion.
    limit = bin_width - item_height

    q = {
        i * item_width + j * item_height
        for i in range(limit // item_width + 1)
        for j in range((limit - i * item_width) // item_height + 1)
    }

    # Ítem sin rotar: ancho w, alto h
    posiciones_x_no_rotado = [q_value for q_value in q if q_value + item_width <= bin_width]
    posiciones_y_no_rotado = [q_value for q_value in q if q_value + item_height <= bin_height]

    xy_x = set(itertools.product(posiciones_x_no_rotado, posiciones_y_no_rotado))

    # Ítem rotado: ancho h, alto w
    if item_width != item_height:
        posiciones_x_rotado = [q_value for q_value in q if q_value + item_height <= bin_width]
        posiciones_y_rotado = [q_value for q_value in q if q_value + item_width <= bin_height]

        xy_y = set(itertools.product(posiciones_x_rotado, posiciones_y_rotado))
    else:
        xy_y = set()

    return xy_x, xy_y
