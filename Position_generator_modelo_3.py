import numpy as np

def generate_positions(W, H, w, h):
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


def create_C_matrix(W, H, positions):
    num_positions = len(positions)
    num_points = W * H  # Total de puntos en la cuadrícula del bin
    C = np.zeros((num_positions, num_points), dtype=int)

    # Enumerar los puntos del bin como coordenadas (x, y)
    points = [(x, y) for x in range(W) for y in range(H)]

    for j, (x_start, _, y_start, _) in enumerate(positions):
        for dx in range(w):  # Ancho del item
            for dy in range(h):  # Alto del item
                # Calcular el punto que ocupa la posición (x_start + dx, y_start + dy)
                x = x_start + dx
                y = y_start + dy
                if 0 <= x < W and 0 <= y < H:
                    p = points.index((x, y))  # Índice del punto en la matriz C
                    C[j, p] = 1

    return C

def generate_Ti(W, H, w_i, h_i, C):
    positions = generate_positions(W, H, w_i, h_i)
    T_i = []

    # Para cada posición generada, validar si es válida
    for idx, (x_start, _, y_start, _) in enumerate(positions):
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