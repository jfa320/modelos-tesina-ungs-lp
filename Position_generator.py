def generate_positions(W, H, w, h):
    # Generar el conjunto de posiciones en el eje x (X)
    X = [x for x in range(W)]

    # Generar el conjunto de posiciones en el eje y (Y)
    Y = [y for y in range(H)]

    # Generar el conjunto de posiciones válidas en el eje x (X_i)
    X_i = [x for x in X if x <= W - w]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    Y_i = [y for y in Y if y <= H - h]

    return X, Y, X_i, Y_i

def generate_positions_no_height_limit(W, H, w, h):
    # Generar el conjunto de posiciones en el eje x (X)
    X = [x for x in range(W)]

    # Generar el conjunto de posiciones en el eje y (Y)
    Y = [y for y in range(H)]

    # Generar el conjunto de posiciones válidas en el eje x (X_i)
    X_i = [x for x in X if x <= W - w]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    Y_i = [y for y in Y if y <= H]

    return X, Y, X_i, Y_i

def generate_positions_modelo_maestro(H, altoRebanada):
  
    Y = [y for y in range(H)]

    # Generar el conjunto de posiciones válidas en el eje y (Y_i)
    Y_i = [y for y in Y if y <= H - altoRebanada]

    return Y_i