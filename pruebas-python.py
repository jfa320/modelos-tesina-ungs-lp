tiposVariables = ["B"] * 12  # 'B' indica binaria
print(tiposVariables)

# Definir el ancho y la altura del bin
W = 10  # Ancho del bin
H = 10  # Altura del bin

# Definir el ancho y la altura de los ítems
w = 2  # Ancho de los ítems
h = 2  # Altura de los ítems

# Generar todas las posiciones posibles para los ítems en el bin
X = list(range(0, W, w))  # Posiciones posibles en el eje x
Y = list(range(0, H, h))  # Posiciones posibles en el eje y

# Filtrar posiciones para asegurar que el ítem no exceda el tamaño del bin
X = [x for x in X if x + w <= W]
Y = [y for y in Y if y + h <= H]

# Mostrar los conjuntos
print("Conjunto X:", X)
print("Conjunto Y:", Y)


# Calcular las posiciones posibles para cada ítem (sin superposición)
positions = [(x, y) for x in X for y in Y]

# Mostrar las posiciones posibles para cada ítem
print("Posiciones posibles para cada ítem:")
for pos in positions:
    print(pos)
