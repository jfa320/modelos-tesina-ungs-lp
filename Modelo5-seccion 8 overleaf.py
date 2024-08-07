import cplex
from cplex.exceptions import CplexSolverError
#Basado en la simplificacion del modelo 5 del overleaf - ver seccion 8 de ese documento para modelo completo

CANTIDAD_ITEMS= 20 # constante n del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo
ANCHO_BIN = 5 # W en el modelo
ALTO_BIN = 2 # H en el modelo

ANCHO_OBJETO= 2 # w en el modelo
ALTO_OBJETO= 1 # h en el modelo

try:
    # Crear un modelo de CPLEX
    modelo= cplex.Cplex()

    # Definir el problema como uno de maximización
    modelo.set_problem_type(cplex.Cplex.problem_type.LP)
    modelo.objective.set_sense(modelo.objective.sense.maximize)

    # Generar nombres de variables dinámicamente
    # f_i: indica si el objeto i esta ubicado dentro del bin con f_i = 1 si esta ubicado en el bin y f_i = 0 de lo contrario

    nombreVariables = [f"f_{i}" for i in range(1, CANTIDAD_ITEMS + 1)]

    # Definir los coeficientes de la función objetivo (todos son 1)
    coeficientes = [1.0] * CANTIDAD_ITEMS  # Esto asigna 1 como coeficiente a cada variable

    # Definir que las variables sean binarias
    tiposVariables = "B" * CANTIDAD_ITEMS  # 'B' indica binaria

    # Añadir estas variables al problema
    modelo.variables.add(names=nombreVariables, obj=coeficientes, types="B" * CANTIDAD_ITEMS)

    nombreVariablesAdicionales=[f"x_{i}" for i in ITEMS]
    nombreVariablesAdicionales+=[f"y_{i}" for i in ITEMS]

    # Definir variables adicionales para todos los pares (i, j) con i != j

    coeficientesObjetivoAdicionales = [0.0] * len(nombreVariablesAdicionales)
    modelo.variables.add(names=nombreVariablesAdicionales, obj=coeficientesObjetivoAdicionales, types="I" * len(nombreVariablesAdicionales))

    nombreVariablesAdicionales= list()
    for i in ITEMS:
        for j in ITEMS:
            if i != j:
                nombreVariablesAdicionales.append(f"l_{i},{j}") # agrego variable l_{ij}
                nombreVariablesAdicionales.append(f"l_{j},{i}") # agrego variable l_{ij}
                nombreVariablesAdicionales.append(f"b_{i},{j}") # agrego variable b_{ij}
                nombreVariablesAdicionales.append(f"b_{j},{i}") # agrego variable b_{ij}
                #TODO: revisar estas variables ya que a veces se duplican e impiden resolver el modelo (se duplican con 20 items por ejemplo)

    # Añadir las variables adicionales al problema con coeficientes 0 en la función objetivo
    # convertir el set a una lista
    # nombreVariablesAdicionales = list(nombreVariablesAdicionales)
    print(nombreVariablesAdicionales)
    coeficientesObjetivoAdicionales = [0.0] * len(nombreVariablesAdicionales)
    modelo.variables.add(names=nombreVariablesAdicionales, obj=coeficientesObjetivoAdicionales, types="B" * len(nombreVariablesAdicionales))

    # Añadir las restricciones para cada par (i, j) con i < j
    for i in ITEMS:
        for j in ITEMS:
            if i < j: #Aca fue necesario reescribir la restriccion para que funcione con CPLEX
                coeficientes_restriccion = [1.0, 1.0, 1.0, 1.0, -1.0, -1.0]
                variables_restriccion = [f"l_{i},{j}", f"l_{j},{i}", f"b_{i},{j}", f"b_{j},{i}", f"f_{i}", f"f_{j}"] 
                rhs_restriccion = -1.0
                sentido_restriccion = "G"  # "G" indica >=

                # Añadir la restricción al problema
                modelo.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
                    senses=[sentido_restriccion],
                    rhs=[rhs_restriccion]
                )

    # Añadir las restricciones x_i - x_j + W l_{ij} <= W - w para cada i en I
    for i in ITEMS:
        for j in ITEMS:
            if i != j:
                coeficientes_restriccion = [1.0, -1.0, ANCHO_BIN]
                variables_restriccion = [f"x_{i}", f"x_{j}", f"l_{i},{j}"]
                rhs_restriccion = ANCHO_BIN - ANCHO_OBJETO
                sentido_restriccion = "L"  # "L" indica <=

                # Añadir la restricción al problema
                modelo.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
                    senses=[sentido_restriccion],
                    rhs=[rhs_restriccion]
                )

    # Añadir las restricciones y_i - y_j + H b_{ij} <= H - h para cada i en I
    for i in ITEMS:
        for j in ITEMS:
            if i != j:
                coeficientes_restriccion = [1.0, -1.0, ALTO_BIN]
                variables_restriccion = [f"y_{i}", f"y_{j}", f"b_{i},{j}"]
                rhs_restriccion = ALTO_BIN - ALTO_OBJETO
                sentido_restriccion = "L"  # "L" indica <=

                # Añadir la restricción al problema
                modelo.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
                    senses=[sentido_restriccion],
                    rhs=[rhs_restriccion]
                )

    # Añadir la restricción x_i + W f_i <= 2W - w  para cada i en I
    for i in ITEMS:
        coeficientes_restriccion = [1.0, ANCHO_BIN]  # Coeficientes para x_i y f_i
        variables_restriccion = [f"x_{i}", f"f_{i}"]  # Variables en la restricción
        rhs_restriccion = 2 * ANCHO_BIN - ANCHO_OBJETO  # Lado derecho de la restricción
        sentido_restriccion = "L"  # "L" indica <=

        # Añadir la restricción al problema
        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
            senses=[sentido_restriccion],
            rhs=[rhs_restriccion]
        )

    # Añadir la restricción y_i + H f_i <= 2H - h para cada i en I
    for i in ITEMS:
        coeficientes_restriccion = [1.0, ANCHO_BIN]  # Coeficientes para x_i y f_i
        variables_restriccion = [f"x_{i}", f"f_{i}"]  # Variables en la restricción
        rhs_restriccion = 2 * ANCHO_BIN - ANCHO_OBJETO  # Lado derecho de la restricción
        sentido_restriccion = "L"  # "L" indica <=

        # Añadir la restricción al problema
        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
            senses=[sentido_restriccion],
            rhs=[rhs_restriccion]
        )


    # Resolver el modeloo
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