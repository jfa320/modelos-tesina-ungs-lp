from Position_generator_modelo_3 import *

L = 260  # Largo del contenedor
A = 240   # Altura del contenedor
l = 40   # Largo del producto
a = 35   # Altura del producto

# positions1=generate_positions_without_rotation_marcelo(L,A,l,a)
# positions2 = generate_positions_without_rotation(L, A, l, a) 
# print(positions1)
print("--------------------------------------------------------")
# print(positions2)


# Constantes
L, A, l, a = 3,3,2,3

# Conjunto Q
Q = {i * l + j * a for i in range(L // l + 1) for j in range(A // a + 1) if i * l + j * a <= L - a}
Q = sorted(Q)  # ordeno el conjunto


# Conjunto P
P = {x for x in range(0, L - a + 1) if x in Q}

XY_x = {(x, y) for x in P for y in P if x + l <= L and y + a <= A}

XY_y = {(x, y) for x in P for y in P if x + a <= L and y + l <= A}

# Print de los conjuntos para verificar
print("Q:", Q)
print("P:", P)
print("XY_x:", XY_x)
print("XY_y:", XY_y)

print("------------------")

print(generate_positions_without_rotation(L, A, l, a ))

