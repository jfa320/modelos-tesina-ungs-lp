import cplex
from Position_generator_modelo_3 import *

# Crear el modelo
model = cplex.Cplex()

#Caso 1: 

CANTIDAD_ITEMS=6 # constante N del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
ANCHO_BIN = 6 # W en el modelo
ALTO_BIN = 4 # H en el modelo

ANCHO_OBJETO= 2 # w en el modelo
ALTO_OBJETO= 3 # h en el modelo

# Parámetros
W = ANCHO_BIN  # Ancho del bin
H = ALTO_BIN  # Alto del bin
w = ANCHO_OBJETO # Ancho del item
h = ALTO_OBJETO  # Alto del item

I = range(CANTIDAD_ITEMS)  # Conjunto de items
J = generate_positions2_without_rotation(W, H, w, h)  # Posiciones sin rotación
print("sin rotacion")
print(J)
J_rot = generate_positions2_without_rotation(W, H, h, w)  # Posiciones con rotación de 90 grados
print("con rotacion")
print(J_rot)
P = [(x, y) for x in range(W) for y in range(H)]  # Puntos del bin
C = create_C_matrix(W, H, J, w, h, P)  # Matriz C para posiciones sin rotación
C_rot = create_C_matrix(W, H, J_rot, h, w, P)  # Matriz C para posiciones rotadas

# Conjunto de posiciones válidas por ítem
T = J
T_rot = J_rot
Q = len(T)  # Cantidad total de posiciones válidas por ítem
Q_rot = len(T_rot)  # Cantidad total de posiciones válidas rotadas por ítem

# Variables
n_vars = []
x_vars = []
y_vars = []

# Añadir las variables n_i
for i in I:
    var_name = f"n_{i}"
    model.variables.add(names=[var_name], types=[model.variables.type.binary])
    n_vars.append(var_name)

# Añadir las variables x_j^i
for i in I:
    x_vars_i = []
    for j in T:
        var_name = f"x_{j}^{i}"
        model.variables.add(names=[var_name], types=[model.variables.type.binary])
        x_vars_i.append(var_name)
    x_vars.append(x_vars_i)

# Añadir las variables y_j^i para las posiciones rotadas
for i in I:
    y_vars_i = []
    for j in T_rot:
        var_name = f"y_{j}^{i}"
        model.variables.add(names=[var_name], types=[model.variables.type.binary])
        y_vars_i.append(var_name)
    y_vars.append(y_vars_i)

# Función objetivo: maximizar la suma de n_i
objective = [1.0] * len(I)
model.objective.set_sense(model.objective.sense.maximize)
model.objective.set_linear(list(zip(n_vars, objective)))

# Restricción 1: Cada punto del bin está ocupado por a lo sumo un ítem (incluyendo rotaciones)
for index_p, _ in enumerate(P):
    indices = []
    coefficients = []
    for i in I:
        for index_j, j in enumerate(T):
            if C[index_j][index_p] == 1:
                indices.append(f"x_{j}^{i}")
                coefficients.append(1.0)
        for index_j, j in enumerate(T_rot):
            if C_rot[index_j][index_p] == 1:
                indices.append(f"y_{j}^{i}")
                coefficients.append(1.0)
    model.linear_constraints.add(
        lin_expr=[[indices, coefficients]],
        senses=["L"],
        rhs=[1.0]
    )

# Restricción 2: No exceder el área del bin
indices = []
coefficients = []
seen_indices = set()

for i in I:
    for index_j, j in enumerate(T):
        for index_p, _ in enumerate(P):
            if C[index_j][index_p] == 1:
                var_name = f"x_{j}^{i}"
                if var_name not in seen_indices:
                    indices.append(var_name)
                    coefficients.append(1.0)
                    seen_indices.add(var_name)
    for index_j, j in enumerate(T_rot):
        for index_p, _ in enumerate(P):
            if C_rot[index_j][index_p] == 1:
                var_name = f"y_{j}^{i}"
                if var_name not in seen_indices:
                    indices.append(var_name)
                    coefficients.append(1.0)
                    seen_indices.add(var_name)

model.linear_constraints.add(
    lin_expr=[[indices, coefficients]],
    senses=["L"],
    rhs=[W * H]
)

# Restricción 3: n_i <= suma(x_j^i + y_j^i)
for i in I:
    indices = [f"x_{j}^{i}" for j in T] + [f"y_{j}^{i}" for j in T_rot]
    coefficients = [1.0] * (len(T) + len(T_rot))
    indices.append(f"n_{i}")
    coefficients.append(-1.0)
    model.linear_constraints.add(
        lin_expr=[[indices, coefficients]],
        senses=["G"],
        rhs=[0.0]
    )

# Restricción 4: suma(x_j^i) <= Q(i) * n_i
for i in I:
    indices = [f"x_{j}^{i}" for j in T]
    coefficients = [1.0] * len(T)
    indices.append(f"n_{i}")
    coefficients.append(-Q)
    model.linear_constraints.add(
        lin_expr=[[indices, coefficients]],
        senses=["L"],
        rhs=[0.0]
    )

# Restricción 5: suma(y_j^i) <= Q_rot(i) * n_i
for i in I:
    indices = [f"y_{j}^{i}" for j in T_rot]
    coefficients = [1.0] * len(T_rot)
    indices.append(f"n_{i}")
    coefficients.append(-Q_rot)
    model.linear_constraints.add(
        lin_expr=[[indices, coefficients]],
        senses=["L"],
        rhs=[0.0]
    )

# Resolver el modelo
model.solve()

# Imprimir resultados
print("Estado de la solución:", model.solution.get_status_string())
print("Valor de la función objetivo:", model.solution.get_objective_value())
for i, var_name in enumerate(n_vars):
    print(f"{var_name} = {model.solution.get_values(var_name)}")


# Imprimir los valores de las variables x_j^i
print("\nValores de las variables x_j^i:")
for i in range(len(I)):
    for j in range(len(T)):
        var_name = x_vars[i][j]
        value = model.solution.get_values(var_name)
        if value > 0:  # Mostrar solo las variables que están activas
            print(f"{var_name} = {value}")

# Imprimir los valores de las variables y_j^i
print("\nValores de las variables y_j^i:")
for i in range(len(I)):
    for j in range(len(T_rot)):
        var_name = y_vars[i][j]
        value = model.solution.get_values(var_name)
        if value > 0:  # Mostrar solo las variables que están activas
            print(f"{var_name} = {value}")