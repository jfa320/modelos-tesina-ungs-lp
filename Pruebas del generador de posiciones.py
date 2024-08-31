from Position_generator_modelo_3 import *

L = 10  # Largo del contenedor
A = 8   # Altura del contenedor
l = 2   # Largo del producto
a = 2   # Altura del producto

positions1=generate_positions_without_rotation_marcelo(L,A,l,a)
positions2 = generate_positions_without_rotation_one_item_size(L, A, l, a) 
print(positions1)
print("--------------------------------------------------------")
print(positions2)