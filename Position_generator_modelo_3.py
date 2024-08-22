import numpy as np

def generate_positions_without_rotation(W, H, w, h): #este lo saque del paper pero genera posiciones incorrectas
    positions = []
    
    for j in range(w, W + 1):  # Desde w hasta W (inclusive)
        for l in range(W):  # Desde 0 hasta W-1
            if (j + l) <= W:
                for i in range(h, H + 1):  # Desde h hasta H (inclusive)
                    for k in range(H):  # Desde 0 hasta H-1
                        if (k + i) <= H:
                            # Creación y etiquetado de una nueva posición para el item i
                            positions.append((j, l, i, k))
    
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