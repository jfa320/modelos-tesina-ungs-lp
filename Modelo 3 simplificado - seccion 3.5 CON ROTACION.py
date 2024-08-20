import cplex

# Crear el modelo
model = cplex.Cplex()

# Parámetros
W = 6  # Ancho del bin
H = 4  # Alto del bin
w = 2  # Ancho del item
h = 3  # Alto del item

I = range(6)  # Conjunto de items
P = generate_positions(W, H, w, h)
# J = range(10)  # Ejemplo de posiciones posibles para los items
C = create_C_matrix(W, H, positions)

# Conjunto de posiciones válidas por item T(i)
T_i = generate_Ti(W, H, w, h, C)
Q = {i: len(T[i]) for i in I}  # Cantidad total de posiciones válidas por item

# Variables
n_vars = []
x_vars = []

# Añadir las variables n_i
for i in I:
    var_name = f"n_{i}"
    model.variables.add(names=[var_name], types=[model.variables.type.binary])
    n_vars.append(var_name)

# Añadir las variables x_j^i
for i in I:
    x_vars_i = []
    for j in T[i]:
        var_name = f"x_{j}^{i}"
        model.variables.add(names=[var_name], types=[model.variables.type.binary])
        x_vars_i.append(var_name)
    x_vars.append(x_vars_i)

# Función objetivo: maximizar la suma de n_i
objective = [1.0] * len(I)
model.objective.set_sense(model.objective.sense.maximize)
model.objective.set_linear(list(zip(n_vars, objective)))

# Restricción 1: Cada punto del bin está ocupado por a lo sumo un item
for p in P:
    indices = []
    coefficients = []
    for i in I:
        for j in T[i]:
            if C[j][p] == 1:
                indices.append(f"x_{j}^{i}")
                coefficients.append(1.0)
    model.linear_constraints.add(
        lin_expr=[[indices, coefficients]],
        senses=["L"],
        rhs=[1.0]
    )

# Restricción 2: No exceder el área del bin
indices = []
coefficients = []
for i in I:
    for j in T[i]:
        for p in P:
            if C[j][p] == 1:
                indices.append(f"x_{j}^{i}")
                coefficients.append(1.0)
model.linear_constraints.add(
    lin_expr=[[indices, coefficients]],
    senses=["L"],
    rhs=[W * H]
)

# Restricción 3: n_i <= suma(x_j^i)
for i in I:
    indices = [f"x_{j}^{i}" for j in T[i]]
    coefficients = [1.0] * len(T[i])
    indices.append(f"n_{i}")
    coefficients.append(-1.0)
    model.linear_constraints.add(
        lin_expr=[[indices, coefficients]],
        senses=["G"],
        rhs=[0.0]
    )

# Restricción 4: suma(x_j^i) <= Q(i) * n_i
for i in I:
    indices = [f"x_{j}^{i}" for j in T[i]]
    coefficients = [1.0] * len(T[i])
    indices.append(f"n_{i}")
    coefficients.append(-Q[i])
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
for i, var_group in enumerate(x_vars):
    for j, var_name in enumerate(var_group):
        print(f"{var_name} = {model.solution.get_values(var_name)}")
