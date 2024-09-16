import cplex
from Position_generator import generate_positions

from cplex.exceptions import CplexSolverError
#Basado en la simplificacion del modelo 2 del overleaf (modelo discretizado en posiciones) - ver seccion 3.3 de ese documento para modelo completo

# Todos los casos siguientes mejoran con rotacion

# Caso 1:
# CANTIDAD_ITEMS=6 # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 6 # W en el modelo
# ALTO_BIN = 4 # H en el modelo

# ANCHO_OBJETO= 2 # w en el modelo
# ALTO_OBJETO= 3 # h en el modelo


#Caso 2: 

CANTIDAD_ITEMS=6 # constante N del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
ANCHO_BIN = 5 # W en el modelo
ALTO_BIN = 5 # H en el modelo

ANCHO_OBJETO= 3 # w en el modelo
ALTO_OBJETO= 2 # h en el modelo

#Caso 3: 

# CANTIDAD_ITEMS=8 # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 6 # W en el modelo
# ALTO_BIN = 6 # H en el modelo

# ANCHO_OBJETO= 4 # w en el modelo
# ALTO_OBJETO= 2 # h en el modelo

#Caso 4: 

# CANTIDAD_ITEMS=5 # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 7 # W en el modelo
# ALTO_BIN = 3 # H en el modelo

# ANCHO_OBJETO= 3 # w en el modelo
# ALTO_OBJETO= 2 # h en el modelo

#Caso 5: 

# CANTIDAD_ITEMS = 6  # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 6  # W en el modelo
# ALTO_BIN = 3  # H en el modelo

# ANCHO_OBJETO = 3  # w en el modelo
# ALTO_OBJETO = 2  # h en el modelo

#CONJUNTO_POS_X  constante X en el modelo
#CONJUNTO_POS_Y  constante Y en el modelo

#CONJUNTO_POS_X_I constante X_i en el modelo
#CONJUNTO_POS_Y_I constante Y_i en el modelo

CONJUNTO_POS_X, CONJUNTO_POS_Y, CONJUNTO_POS_X_I, CONJUNTO_POS_Y_I = generate_positions(ANCHO_BIN, ALTO_BIN, ANCHO_OBJETO, ALTO_OBJETO)

CANT_X_I=len(CONJUNTO_POS_X_I) #constante Q(X_i) del modelo
CANT_Y_I=len(CONJUNTO_POS_Y_I) #constante Q(Y_i) del modelo

try:
    # Crear un modelo de CPLEX
    modelo= cplex.Cplex()

    # Definir el problema como uno de maximización
    modelo.set_problem_type(cplex.Cplex.problem_type.LP)
    modelo.objective.set_sense(modelo.objective.sense.maximize)

    # Generar nombres de variables dinámicamente
    # f_i: indica si el objeto i esta ubicado dentro del bin con f_i = 1 si esta ubicado en el bin y f_i = 0 de lo contrario

    nombreVariables = [f"m_{i}" for i in range(1, CANTIDAD_ITEMS + 1)]

    # Definir los coeficientes de la función objetivo (todos son 1)
    coeficientes = [1.0] * CANTIDAD_ITEMS  # Esto asigna 1 como coeficiente a cada variable

    # Definir que las variables sean binarias
    tiposVariables = "B" * CANTIDAD_ITEMS  # 'B' indica binaria

    # Añadir estas variables al problema
    modelo.variables.add(names=nombreVariables, obj=coeficientes, types="B" * CANTIDAD_ITEMS)

    # Definir variables adicionales 


    nombreVariablesAdicionales = []
    for x in CONJUNTO_POS_X_I:
        for y in CONJUNTO_POS_Y_I:
                for i in ITEMS:
                    nombreVariablesAdicionales.append(f"n_{i},{x},{y}") # agrego variable n_{i,x,y}

    for x in CONJUNTO_POS_X:
        for y in CONJUNTO_POS_Y:            
            nombreVariablesAdicionales.append(f"r_{x},{y}") # agrego variable r_{x,y}

    # Añadir las variables adicionales al problema con coeficientes 0 en la función objetivo
    coeficientesObjetivoAdicionales = [0.0] * len(nombreVariablesAdicionales)
    modelo.variables.add(names=nombreVariablesAdicionales, obj=coeficientesObjetivoAdicionales, types="B" * len(nombreVariablesAdicionales))

    # Añadir la restricción r_{x,y} = sum_{i in N} sum_{x' in X_i, x-w+1 <= x' <= x} sum_{y' in Y_i, y-h+1 <= y' <= y} n_{i,x',y'} para cada (x, y) en X x Y
    for x in CONJUNTO_POS_X:
        for y in CONJUNTO_POS_Y:
            coeficientes_restriccion = [1.0]  # Coeficiente para r_{x,y}
            variables_restriccion = [f"r_{x},{y}"]  # Variable r_{x,y}

            # Añadir los coeficientes y variables de sum_{i in N} sum_{x' in X_i, x-w+1 <= x' <= x} sum_{y' in Y_i, y-h+1 <= y' <= y} n_{i,x',y'}
            for i in ITEMS:
                for x_prima in CONJUNTO_POS_X_I:
                    if x - ANCHO_OBJETO + 1 <= x_prima <= x:
                        for y_prima in CONJUNTO_POS_Y_I:
                            if y - ALTO_OBJETO + 1 <= y_prima <= y:
                                coeficientes_restriccion.append(-1.0)
                                variables_restriccion.append(f"n_{i},{x_prima},{y_prima}")

            rhs_restriccion = 0.0  # Lado derecho de la restricción
            sentido_restriccion = "E"  # "E" indica ==

            # Añadir la restricción al problema
            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
                senses=[sentido_restriccion],
                rhs=[rhs_restriccion]
            )

    # Añadir la restricción m_i <= sum_{x in X_i} sum_{y in Y_i} n_{i,x,y} para cada i en items - restriccion 2 del modelo
    for i in ITEMS:
        coeficientes_restriccion = [1.0]  # Coeficiente para m_i
        variables_restriccion = [f"m_{i}"]  # Variable m_i

        # Añadir los coeficientes y variables de sum_{x in X_i} sum_{y in Y_i} n_{i,x,y}
        for x in CONJUNTO_POS_X_I:
            for y in CONJUNTO_POS_Y_I:
                coeficientes_restriccion.append(-1.0)
                variables_restriccion.append(f"n_{i},{x},{y}")

        rhs_restriccion = 0.0  # Lado derecho de la restricción
        sentido_restriccion = "L"  # "L" indica <=

        # Añadir la restricción al problema
        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
            senses=[sentido_restriccion],
            rhs=[rhs_restriccion]
        )

    # Añadir la restricción sum_{x in X_i} sum_{y in Y_i} n_{i,x,y} <= Q(X_i) Q(Y_i) m_i para cada i en items
    for i in ITEMS:
        coeficientes_restriccion = [-1.0]  # Coeficiente para m_i
        variables_restriccion = [f"m_{i}"]  # Variable m_i

        # Añadir los coeficientes y variables de sum_{x in X_i} sum_{y in Y_i} n_{i,x,y}
        for x in CONJUNTO_POS_X_I:
            for y in CONJUNTO_POS_Y_I:
                coeficientes_restriccion.append(1.0)
                variables_restriccion.append(f"n_{i},{x},{y}")

        rhs_restriccion = 0.0  # Lado derecho de la restricción
        sentido_restriccion = "L"  # "L" indica <=

        # Añadir la restricción al problema
        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
            senses=[sentido_restriccion],
            rhs=[CANT_X_I * CANT_Y_I]  # Right Hand Side (RHS) es Q(X_i) * Q(Y_i)
        )

    

    # Resolver el modelo
    modelo.solve()

    # Obtener y mostrar los resultados
    solution_values = modelo.solution.get_values()
    objective_value = modelo.solution.get_objective_value()

    print("Valor óptimo de la función objetivo:", objective_value)
    print("Valores de las variables:")
    for var_name, value in zip(nombreVariables, solution_values):
        print(f"{var_name} = {value}")

except CplexSolverError as e:
    if e.args[2] == 1217:  # Codigo de error para "No solution exists"
        print("\nNo existen soluciones para el modelo dado.")
    else:
        print("CPLEX Solver Error:", e)