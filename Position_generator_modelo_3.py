import numpy as np
import itertools
import math

def generate_positions_without_rotation(W, H, wi, hi):
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

def generate_positions_without_rotation_marcelo(L,A,l,a):
    positions = {
        (i, j) 
        for i, j in itertools.product(range(math.floor(L / a) + 1), range(math.floor(A / a) + 1))
        if i * l + j * a <= L - a
    }
    return positions

def generate_positions_without_rotation_one_item_size(W, H, w, h):
    positions = []
    
    # Recorrer todas las posibles posiciones en el bin
    for j in range(W - w + 1):  # Rango de posiciones horizontales
        for l in range(H - h + 1):  # Rango de posiciones verticales
            positions.append((j, l))  # Generar la posición (j, l)
    
    return positions

def generate_positions2_without_rotation(W, H, w, h):
    positions = []
    
    # Bucle sobre posiciones horizontales donde el objeto puede empezar
    for j in range(W - w + 1):  # Desde 0 hasta W - w
        # Bucle sobre posiciones verticales donde el objeto puede empezar
        for k in range(H - h + 1):  # Desde 0 hasta H - h
            # Si el objeto cabe dentro del bin, guardamos la posición
            positions.append((j, k))
    
    return positions


def create_C_matrix(W, H, positions, w, h, points):
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

def generate_Ti(W, H, w_i, h_i, C, positions):
    T_i = []

    # Para cada posición generada, validar si es válida
    for idx, (x_start, y_start) in enumerate(positions):  # Solo usamos x_start y y_start
        valid = True
        for dx in range(w_i):
            for dy in range(h_i):
                x = x_start + dx
                y = y_start + dy
                if 0 <= x < W and 0 <= y < H:
                    p = x * H + y  # Calcula el índice del punto (x, y) en la matriz C
                    if C[idx, p] == 0:  # Si este punto no está ocupado en la posición, es válido
                        continue
                    else:
                        valid = False
                        break
            if not valid:
                break

        # Si la posición es válida, se agrega a T_i
        if valid:
            T_i.append(idx)

    return T_i