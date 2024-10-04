import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
import multiprocessing
import time


#Basado en la simplificacion del modelo 1 (modelo base - Pisinger & Sigurd) - ver seccion 2.8 en Overleaf para modelo completo

# Caso sencillo que mejora con rotacion
NOMBRE_MODELO="Model1"

modelStatus="1"
solverStatus="1"
objective_value=0
solverTime=1

# CANTIDAD_ITEMS= 6 # constante n del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo
# ANCHO_BIN = 6 # W en el modelo
# ALTO_BIN = 4 # H en el modelo

# ANCHO_OBJETO= 2 # w en el modelo
# ALTO_OBJETO= 3 # h en el modelo

#prueba para validar el corte al minuto de la ejecucion
NOMBRE_CASO="inst2"
CANTIDAD_ITEMS= 15 # constante n del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo
ANCHO_BIN = 6 # W en el modelo
ALTO_BIN = 4 # H en el modelo

ANCHO_OBJETO= 2 # w en el modelo
ALTO_OBJETO= 3 # h en el modelo

#caso con mas de 20 objetos

# CANTIDAD_ITEMS= 20 # constante n del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo
# ANCHO_BIN = 10 # W en el modelo
# ALTO_BIN = 10 # H en el modelo

# ANCHO_OBJETO= 2 # w en el modelo
# ALTO_OBJETO= 3 # h en el modelo

EXECUTION_TIME=2 # in seconds

def createAndSolveModel(queue,interrupcion_manual,tiempoMaximo):
    #valores por default para enviar a paver
    modelStatus="1"
    solverStatus="1"
    objective_value=0
    solverTime=1
    
    try:

        # Crear un modelo de CPLEX
        modelo= cplex.Cplex()

        tiempoInicial=modelo.get_time()

        # Definir el problema como uno de maximización
        modelo.set_problem_type(cplex.Cplex.problem_type.LP)
        modelo.objective.set_sense(modelo.objective.sense.maximize)

        # Definir el limite tiempo de la ejecución en un minuto
        modelo.parameters.timelimit.set(tiempoMaximo)
        
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

        nombreVariablesAdicionales= set()
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    nombreVariablesAdicionales.add(f"l_{i},{j}") # agrego variable l_{ij}
                    nombreVariablesAdicionales.add(f"l_{j},{i}") # agrego variable l_{ij}
                    nombreVariablesAdicionales.add(f"b_{i},{j}") # agrego variable b_{ij}
                    nombreVariablesAdicionales.add(f"b_{j},{i}") # agrego variable b_{ij}

        # Añadir las variables adicionales al problema con coeficientes 0 en la función objetivo
        # convertir el set a una lista
        nombreVariablesAdicionales = list(nombreVariablesAdicionales)
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

        # Desactivar la interrupción manual aquí
        interrupcion_manual.value = False
        # Resolver el modeloo
        modelo.solve()

        # Obtener y mostrar los resultados
        solution_values = modelo.solution.get_values()
        objective_value = modelo.solution.get_objective_value()
        print(f"Valor óptimo de la función objetivo: {objective_value}")
        for var_name, value in zip(nombreVariables, solution_values):
            print(f"{var_name} = {value}")
       
        status = modelo.solution.get_status()
        tiempoFinal = modelo.get_time()
        solverTime=tiempoFinal-tiempoInicial
        solverTime=round(solverTime, 2)
        
        if status == 105:  # CPLEX código 105 = Time limit exceeded
            print("El solver se detuvo porque alcanzó el límite de tiempo.")
            modelStatus="2" #valor en paver para marcar un optimo local

        # Enviar resultados a través de la cola
        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objective_value": objective_value,
            "solverTime": solverTime
        })
        
    except CplexSolverError as e:
        if e.args[2] == 1217:  # Codigo de error para "No solution exists"
            print("\nNo existen soluciones para el modelo dado.")
            modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solverStatus="4" #el solver finalizo la ejecucion del modelo
        else:
            print("CPLEX Solver Error:", e)
            modelStatus="12" #valor en paver para marcar un error desconocido
            solverStatus="10" #el solver tuvo un error en la ejecucion

        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objective_value": objective_value,
            "solverTime": solverTime
        })


def executeWithTimeLimit(tiempo_maximo):
    global modelStatus, solverStatus, objective_value, solverTime 
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

        if interrupcion_manual.value:
            # Si se excede el tiempo, terminamos el proceso
            if time.time() - tiempo_inicial > tiempo_maximo:
                print("Tiempo límite alcanzado. Abortando el proceso.")
                modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
                solverStatus="4" #el solver finalizo la ejecucion del modelo
                solverTime=tiempo_maximo
                proceso.terminate()
                proceso.join()
                break

        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            print(message)
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            objective_value = message["objective_value"]
            solverTime = message["solverTime"]



if __name__ == '__main__':
    # Ejecutar la función con un límite de tiempo de 10 segundos
    executeWithTimeLimit(EXECUTION_TIME)
    generator = TraceFileGenerator("output.trc")
    generator.write_trace_record(NOMBRE_CASO, NOMBRE_MODELO, modelStatus, solverStatus, objective_value, solverTime)