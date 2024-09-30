import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time

# Caso 1:
# CANTIDAD_ITEMS=6 # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 6 # W en el modelo
# ALTO_BIN = 4 # H en el modelo

# ANCHO_OBJETO= 2 # w en el modelo
# ALTO_OBJETO= 3 # h en el modelo


#Caso 2: 

# CANTIDAD_ITEMS=6 # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 5 # W en el modelo
# ALTO_BIN = 5 # H en el modelo

# ANCHO_OBJETO= 3 # w en el modelo
# ALTO_OBJETO= 2 # h en el modelo

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

# Caso 5: 

# CANTIDAD_ITEMS = 6  # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 6  # W en el modelo
# ALTO_BIN = 3  # H en el modelo

# ANCHO_OBJETO = 3  # w en el modelo
# ALTO_OBJETO = 2  # h en el modelo

#prueba para validar el corte al minuto de la ejecucion
CANTIDAD_ITEMS= 100 # constante n del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo
ANCHO_BIN = 16 # W en el modelo
ALTO_BIN = 14 # H en el modelo

ANCHO_OBJETO= 2 # w en el modelo
ALTO_OBJETO= 3 # h en el modelo

EXECUTION_TIME=60 # in seconds

def createAndSolveModel(queue,interrupcion_manual,tiempoMaximo):
    try:
        # Crear un modelo de CPLEX
        modelo = cplex.Cplex()

        # Definir el problema como uno de maximización
        modelo.set_problem_type(cplex.Cplex.problem_type.LP)
        modelo.objective.set_sense(modelo.objective.sense.maximize)

        # Definir el limite tiempo de la ejecución en un minuto
        modelo.parameters.timelimit.set(tiempoMaximo)

        # Variables f_i: indica si el objeto i está ubicado dentro del bin
        nombreVariables = [f"f_{i}" for i in ITEMS]

        # Definir los coeficientes de la función objetivo (todos son 1)
        coeficientes = [1.0] * CANTIDAD_ITEMS  # Esto asigna 1 como coeficiente a cada variable

        # Definir que las variables sean binarias
        modelo.variables.add(names=nombreVariables, obj=coeficientes, types="B" * CANTIDAD_ITEMS)

        # Variables adicionales: x_i, y_i y r_i (indica si el objeto está rotado)
        nombreVariablesAdicionales = [f"x_{i}" for i in ITEMS]
        nombreVariablesAdicionales += [f"y_{i}" for i in ITEMS]
        nombreVariablesAdicionales += [f"r_{i}" for i in ITEMS]  # Variable de rotación

        coeficientesObjetivoAdicionales = [0.0] * len(nombreVariablesAdicionales)
        modelo.variables.add(names=nombreVariablesAdicionales, obj=coeficientesObjetivoAdicionales, types="I" * (2 * CANTIDAD_ITEMS) + "B" * CANTIDAD_ITEMS)

        # Variables l_{ij}, b_{ij}
        nombreVariablesAdicionales = []
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    nombreVariablesAdicionales.append(f"l_{i},{j}")  # Variable l_{ij}
                    nombreVariablesAdicionales.append(f"b_{i},{j}")  # Variable b_{ij}

        # Añadir variables adicionales con coeficiente 0
        coeficientesObjetivoAdicionales = [0.0] * len(nombreVariablesAdicionales)
        modelo.variables.add(names=nombreVariablesAdicionales, obj=coeficientesObjetivoAdicionales, types="B" * len(nombreVariablesAdicionales))

        # Restricciones de no solapamiento
        for i in ITEMS:
            for j in ITEMS:
                if i < j:
                    coeficientes_restriccion = [1.0, 1.0, 1.0, 1.0, -1.0, -1.0]
                    variables_restriccion = [f"l_{i},{j}", f"l_{j},{i}", f"b_{i},{j}", f"b_{j},{i}", f"f_{i}", f"f_{j}"]
                    rhs_restriccion = -1.0
                    sentido_restriccion = "G"

                    modelo.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
                        senses=[sentido_restriccion],
                        rhs=[rhs_restriccion]
                    )

        # Restricciones x_i - x_j + W l_{ij} <= W - w (1 - r_i) - h r_i
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    coeficientes_restriccion = [1.0, -1.0, ANCHO_BIN, -ANCHO_OBJETO + ALTO_OBJETO ]
                    variables_restriccion = [f"x_{i}", f"x_{j}", f"l_{i},{j}", f"r_{i}"]
                    rhs_restriccion = ANCHO_BIN - ANCHO_OBJETO
                    sentido_restriccion = "L"

                    modelo.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
                        senses=[sentido_restriccion],
                        rhs=[rhs_restriccion]
                    )

        # Restricciones y_i - y_j + H  b_{ij} <= H - h  (1 - r_i) - w r_i
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    coeficientes_restriccion = [1.0, -1.0, ALTO_BIN, -ALTO_OBJETO+ANCHO_OBJETO]
                    variables_restriccion = [f"y_{i}", f"y_{j}", f"b_{i},{j}", f"r_{i}"]
                    rhs_restriccion = ALTO_BIN - ALTO_OBJETO
                    sentido_restriccion = "L"

                    modelo.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(variables_restriccion, coeficientes_restriccion)],
                        senses=[sentido_restriccion],
                        rhs=[rhs_restriccion]
                    )

        # Restricciones para asegurar que los objetos estén dentro del bin (considerando rotación)
        for i in ITEMS:
            coeficientes_restriccion_x = [1.0, ANCHO_BIN, -ANCHO_OBJETO + ALTO_OBJETO]  # Coeficientes para x_i, f_i, r_i
            variables_restriccion_x = [f"x_{i}", f"f_{i}", f"r_{i}"]
            rhs_restriccion_x = 2 * ANCHO_BIN - ANCHO_OBJETO
            sentido_restriccion_x = "L"

            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(variables_restriccion_x, coeficientes_restriccion_x)],
                senses=[sentido_restriccion_x],
                rhs=[rhs_restriccion_x]
            )

            coeficientes_restriccion_y = [1.0, ALTO_BIN, -ALTO_OBJETO + ANCHO_OBJETO]  # Coeficientes para y_i, f_i, r_i
            variables_restriccion_y = [f"y_{i}", f"f_{i}", f"r_{i}"]
            rhs_restriccion_y = 2 * ALTO_BIN - ALTO_OBJETO
            sentido_restriccion_y = "L"

            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(variables_restriccion_y, coeficientes_restriccion_y)],
                senses=[sentido_restriccion_y],
                rhs=[rhs_restriccion_y]
            )

        # Desactivar la interrupción manual aquí
        interrupcion_manual.value = False

        # Resolver el modelo
        modelo.solve()

        # Obtener y mostrar los resultados
        solution_values = modelo.solution.get_values()
        objective_value = modelo.solution.get_objective_value()

        queue.put(f"Valor óptimo de la función objetivo: {objective_value}")
        queue.put("Valores de las variables:")
        for var_name, value in zip(nombreVariables, solution_values):
            queue.put(f"{var_name} = {value}")

    except CplexSolverError as e:
        if e.args[2] == 1217:  # Código de error para "No solution exists"
            queue.put("\nNo existen soluciones para el modelo dado.")
        else:
            queue.put("CPLEX Solver Error:", e)

def executeWithTimeLimit(tiempo_maximo):
    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    interrupcion_manual = multiprocessing.Value('b', True)

    # Crear el subproceso que correrá la función
    proceso = multiprocessing.Process(target=createAndSolveModel, args=(queue,interrupcion_manual,tiempo_maximo))

    # Iniciar el subproceso
    proceso.start()

    tiempo_inicial = time.time()

    # Monitorear la cola mientras el proceso está en ejecución
    while proceso.is_alive():
        # Verificar si hay mensajes en la cola y mostrarlos
        while not queue.empty():
            print(queue.get())

        if interrupcion_manual.value:
            # Si se excede el tiempo, terminamos el proceso
            if time.time() - tiempo_inicial > tiempo_maximo:
                print("Tiempo límite alcanzado. Abortando el proceso.")
                proceso.terminate()
                proceso.join()
                break

        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Asegurarse de imprimir los mensajes restantes si el proceso terminó por sí mismo
    while not queue.empty():
        print(queue.get())


if __name__ == '__main__':
    # Ejecutar la función con un límite de tiempo de 10 segundos
    executeWithTimeLimit(EXECUTION_TIME)


