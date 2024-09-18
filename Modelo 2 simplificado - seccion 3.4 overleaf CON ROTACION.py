import cplex
from Position_generator import generate_positions

from cplex.exceptions import CplexSolverError

# Constantes del problema

# Caso 5: 

CANTIDAD_ITEMS = 6  # constante N del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
ANCHO_BIN = 6  # W en el modelo
ALTO_BIN = 3  # H en el modelo

ANCHO_OBJETO = 3  # w en el modelo
ALTO_OBJETO = 2  # h en el modelo



# Generación de posiciones factibles para ítems y sus versiones rotadas
CONJUNTO_POS_X, CONJUNTO_POS_Y, CONJUNTO_POS_X_I, CONJUNTO_POS_Y_I = generate_positions(ANCHO_BIN, ALTO_BIN, ANCHO_OBJETO, ALTO_OBJETO)
CONJUNTO_POS_X_I_ROT = [x for x in range(ANCHO_BIN) if x <= ANCHO_BIN - ALTO_OBJETO]
CONJUNTO_POS_Y_I_ROT = [y for y in range(ALTO_BIN) if y <= ALTO_BIN - ANCHO_OBJETO]

CANT_X_I = len(CONJUNTO_POS_X_I)
CANT_Y_I = len(CONJUNTO_POS_Y_I)
CANT_X_I_ROT = len(CONJUNTO_POS_X_I_ROT)
CANT_Y_I_ROT = len(CONJUNTO_POS_Y_I_ROT)

try:
    # Crear el modelo CPLEX
    modelo = cplex.Cplex()
    modelo.set_problem_type(cplex.Cplex.problem_type.LP)
    modelo.objective.set_sense(modelo.objective.sense.maximize)

    # Variables para indicar si el ítem o su versión rotada están en el bin
    nombreVariables = [f"m_{i}" for i in ITEMS] + [f"m_rot_{i}" for i in ITEMS]
    coeficientes = [1.0] * CANTIDAD_ITEMS * 2
    modelo.variables.add(names=nombreVariables, obj=coeficientes, types="B" * len(nombreVariables))

    # Variables de posición para la versión original y rotada de los ítems
    nombreVariablesPosiciones = []
    for i in ITEMS:
        for x in CONJUNTO_POS_X_I:
            for y in CONJUNTO_POS_Y_I:
                nombreVariablesPosiciones.append(f"n_{i},{x},{y}")
        for x_rot in CONJUNTO_POS_X_I_ROT:
            for y_rot in CONJUNTO_POS_Y_I_ROT:
                nombreVariablesPosiciones.append(f"n_rot_{i},{x_rot},{y_rot}")

    coeficientesPos = [0.0] * len(nombreVariablesPosiciones)
    modelo.variables.add(names=nombreVariablesPosiciones, obj=coeficientesPos, types="B" * len(nombreVariablesPosiciones))

    # Variables para las posiciones libres (r_x,y)
    nombreVariablesR = [f"r_{x},{y}" for x in CONJUNTO_POS_X for y in CONJUNTO_POS_Y]
    modelo.variables.add(names=nombreVariablesR, obj=[0.0] * len(nombreVariablesR), types="B" * len(nombreVariablesR))

    # Restricción 1: Evita solapamiento de ítems en una posición (x,y)
    for x in CONJUNTO_POS_X:
        for y in CONJUNTO_POS_Y:
            coef_restriccion = [1.0]  # Coeficiente de r_{x,y}
            var_restriccion = [f"r_{x},{y}"]

            for i in ITEMS:
                for x_prima in CONJUNTO_POS_X_I:
                    if x - ANCHO_OBJETO + 1 <= x_prima <= x:
                        for y_prima in CONJUNTO_POS_Y_I:
                            if y - ALTO_OBJETO + 1 <= y_prima <= y:
                                coef_restriccion.append(-1.0)
                                var_restriccion.append(f"n_{i},{x_prima},{y_prima}")

                for x_prima_rot in CONJUNTO_POS_X_I_ROT:
                    if x - ALTO_OBJETO + 1 <= x_prima_rot <= x:
                        for y_prima_rot in CONJUNTO_POS_Y_I_ROT:
                            if y - ANCHO_OBJETO + 1 <= y_prima_rot <= y:
                                coef_restriccion.append(-1.0)
                                var_restriccion.append(f"n_rot_{i},{x_prima_rot},{y_prima_rot}")

            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(var_restriccion, coef_restriccion)],
                senses=["E"], rhs=[0.0]
            )

    # Restricción 2: m_i + m_rot_i <= suma de posiciones donde el ítem está
    # for i in ITEMS:
    #     coef_restriccion = [1.0, 1.0]  # Coeficientes para m_i y m_rot_i
    #     var_restriccion = [f"m_{i}", f"m_rot_{i}"]

    #     for x in CONJUNTO_POS_X_I:
    #         for y in CONJUNTO_POS_Y_I:
    #             coef_restriccion.append(-1.0)
    #             var_restriccion.append(f"n_{i},{x},{y}")

    #     for x_rot in CONJUNTO_POS_X_I_ROT:
    #         for y_rot in CONJUNTO_POS_Y_I_ROT:
    #             coef_restriccion.append(-1.0)
    #             var_restriccion.append(f"n_rot_{i},{x_rot},{y_rot}")

    #     modelo.linear_constraints.add(
    #         lin_expr=[cplex.SparsePair(var_restriccion, coef_restriccion)],
    #         senses=["L"], rhs=[0.0]
    #     )
    # Restricción para ítems no rotados: m_i = suma de las posiciones no rotadas donde está el ítem i
    for i in ITEMS:
        coef_restriccion = [-1.0]  # Coeficiente para m_i
        var_restriccion = [f"m_{i}"]  # Variable m_i que indica si el ítem no rotado está en el bin

        # Sumamos todas las posiciones no rotadas posibles donde el ítem puede estar
        for x in CONJUNTO_POS_X_I:
            for y in CONJUNTO_POS_Y_I:
                coef_restriccion.append(1.0)
                var_restriccion.append(f"n_{i},{x},{y}")

        # La restricción asegura que m_i sea igual a la suma de posiciones ocupadas
        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(var_restriccion, coef_restriccion)],
            senses=["E"], rhs=[0.0]
        )

    # Restricción para ítems rotados: m_rot_i = suma de las posiciones rotadas donde está el ítem i
    for i in ITEMS:
        coef_restriccion_rot = [-1.0]  # Coeficiente para m_rot_i
        var_restriccion_rot = [f"m_rot_{i}"]  # Variable m_rot_i que indica si el ítem rotado está en el bin

        # Sumamos todas las posiciones rotadas posibles donde el ítem puede estar
        for x_rot in CONJUNTO_POS_X_I_ROT:
            for y_rot in CONJUNTO_POS_Y_I_ROT:
                coef_restriccion_rot.append(1.0)
                var_restriccion_rot.append(f"n_rot_{i},{x_rot},{y_rot}")

        # La restricción asegura que m_rot_i sea igual a la suma de posiciones ocupadas
        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(var_restriccion_rot, coef_restriccion_rot)],
            senses=["E"], rhs=[0.0]
        )

    # Restricción 3: suma de posiciones <= Q(X_i)*Q(Y_i) * m_i
    for i in ITEMS:
        coef_restriccion = [-1.0]  # Coeficiente para m_i
        var_restriccion = [f"m_{i}"]

        for x in CONJUNTO_POS_X_I:
            for y in CONJUNTO_POS_Y_I:
                coef_restriccion.append(1.0)
                var_restriccion.append(f"n_{i},{x},{y}")

        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(var_restriccion, coef_restriccion)],
            senses=["L"], rhs=[CANT_X_I * CANT_Y_I]
        )

        coef_restriccion_rot = [-1.0]  # Coeficiente para m_rot_i
        var_restriccion_rot = [f"m_rot_{i}"]

        for x_rot in CONJUNTO_POS_X_I_ROT:
            for y_rot in CONJUNTO_POS_Y_I_ROT:
                coef_restriccion_rot.append(1.0)
                var_restriccion_rot.append(f"n_rot_{i},{x_rot},{y_rot}")

        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(var_restriccion_rot, coef_restriccion_rot)],
            senses=["L"], rhs=[CANT_X_I_ROT * CANT_Y_I_ROT]
        )

    # Restricción 4: m_i + m_rot_i <= 1
    for i in ITEMS:
        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair([f"m_{i}", f"m_rot_{i}"], [1.0, 1.0])],
            senses=["L"], rhs=[1.0]
        )

    # Resolver el modelo
    modelo.solve()

    # Obtener resultados
    solution_values = modelo.solution.get_values()
    objective_value = modelo.solution.get_objective_value()
    sol_values_posiciones = modelo.solution.get_values(nombreVariablesPosiciones)

    print("Valor óptimo de la función objetivo:", objective_value)
    for var_name, value in zip(nombreVariables, solution_values):
        print(f"{var_name} = {value}")
    
    print("\nPosiciones ocupadas por ítems no rotados:")
    for var_name, value in zip(nombreVariablesPosiciones, sol_values_posiciones):
        if value == 1.0 and "n_" in var_name and "rot" not in var_name:
            print(f"{var_name} = {value}")

    # Imprimir las posiciones ocupadas por ítems rotados
    print("\nPosiciones ocupadas por ítems rotados:")
    for var_name, value in zip(nombreVariablesPosiciones, sol_values_posiciones):
        if value == 1.0 and "n_rot" in var_name:
            print(f"{var_name} = {value}")

except CplexSolverError as e:
    if e.args[2] == 1217:
        print("\nNo existen soluciones para el modelo dado.")
    else:
        print("CPLEX Solver Error:", e)
