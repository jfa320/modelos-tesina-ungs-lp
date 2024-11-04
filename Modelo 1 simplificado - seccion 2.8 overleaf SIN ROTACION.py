import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
import multiprocessing
import time


#Basado en la simplificacion del modelo 1 (modelo base - Pisinger & Sigurd) - ver seccion 2.8 en Overleaf para modelo completo

# Caso sencillo que mejora con rotacion
MODEL_NAME="Model1"

modelStatus="1"
solverStatus="1"
objectiveValue=0
solverTime=1

# ITEMS_QUANTITY= 6 # constante n del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) # constante I del modelo
# BIN_WIDTH = 6 # W en el modelo
# BIN_HEIGHT = 4 # H en el modelo

# ITEM_WIDTH= 2 # w en el modelo
# ITEM_HEIGHT= 3 # h en el modelo

#prueba para validar el corte al minuto de la ejecucion
CASE_NAME="inst2"
ITEMS_QUANTITY= 15 # constante n del modelo
ITEMS = list(range(1, ITEMS_QUANTITY + 1)) # constante I del modelo
BIN_WIDTH = 6 # W en el modelo
BIN_HEIGHT = 4 # H en el modelo

ITEM_WIDTH= 2 # w en el modelo
ITEM_HEIGHT= 3 # h en el modelo

#caso con mas de 20 objetos

# ITEMS_QUANTITY= 20 # constante n del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) # constante I del modelo
# BIN_WIDTH = 10 # W en el modelo
# BIN_HEIGHT = 10 # H en el modelo

# ITEM_WIDTH= 2 # w en el modelo
# ITEM_HEIGHT= 3 # h en el modelo

EXECUTION_TIME=2 # in seconds

def createAndSolveModel(queue,manualInterruption,maxTime):
    #valores por default para enviar a paver
    modelStatus="1"
    solverStatus="1"
    objectiveValue=0
    solverTime=1
    
    try:

        # Crear un modelo de CPLEX
        model= cplex.Cplex()

        initialTime=model.get_time()

        # Definir el problema como uno de maximización
        model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

        # Definir el limite tiempo de la ejecución en un minuto
        model.parameters.timelimit.set(maxTime)
        
        # Generar nombres de variables dinámicamente
        # f_i: indica si el objeto i esta ubicado dentro del bin con f_i = 1 si esta ubicado en el bin y f_i = 0 de lo contrario

        varsNames = [f"f_{i}" for i in range(1, ITEMS_QUANTITY + 1)]

        # Definir los coeficientes de la función objetivo (todos son 1)
        coeffs = [1.0] * ITEMS_QUANTITY  # Esto asigna 1 como coeficiente a cada variable

        # Añadir estas variables al problema
        model.variables.add(names=varsNames, obj=coeffs, types="B" * ITEMS_QUANTITY)

        additionalVarsNames=[f"x_{i}" for i in ITEMS]
        additionalVarsNames+=[f"y_{i}" for i in ITEMS]

        # Definir variables adicionales para todos los pares (i, j) con i != j

        additionalCoeffObj = [0.0] * len(additionalVarsNames)
        model.variables.add(names=additionalVarsNames, obj=additionalCoeffObj, types="I" * len(additionalVarsNames))

        additionalVarsNames= set()
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    additionalVarsNames.add(f"l_{i},{j}") # agrego variable l_{ij}
                    additionalVarsNames.add(f"l_{j},{i}") # agrego variable l_{ij}
                    additionalVarsNames.add(f"b_{i},{j}") # agrego variable b_{ij}
                    additionalVarsNames.add(f"b_{j},{i}") # agrego variable b_{ij}

        # Añadir las variables adicionales al problema con coeficientes 0 en la función objetivo
        # convertir el set a una lista
        additionalVarsNames = list(additionalVarsNames)
        additionalCoeffObj = [0.0] * len(additionalVarsNames)
        model.variables.add(names=additionalVarsNames, obj=additionalCoeffObj, types="B" * len(additionalVarsNames))

        # Añadir las restricciones para cada par (i, j) con i < j
        for i in ITEMS:
            for j in ITEMS:
                if i < j: #Aca fue necesario reescribir la restriccion para que funcione con CPLEX
                    consCoeff = [1.0, 1.0, 1.0, 1.0, -1.0, -1.0]
                    consVars = [f"l_{i},{j}", f"l_{j},{i}", f"b_{i},{j}", f"b_{j},{i}", f"f_{i}", f"f_{j}"] 
                    consRhs = -1.0
                    consSense = "G"  # "G" indica >=

                    # Añadir la restricción al problema
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                        senses=[consSense],
                        rhs=[consRhs]
                    )

        # Añadir las restricciones x_i - x_j + W l_{ij} <= W - w para cada i en I
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    consCoeff = [1.0, -1.0, BIN_WIDTH]
                    consVars = [f"x_{i}", f"x_{j}", f"l_{i},{j}"]
                    consRhs = BIN_WIDTH - ITEM_WIDTH
                    consSense = "L"  # "L" indica <=

                    # Añadir la restricción al problema
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                        senses=[consSense],
                        rhs=[consRhs]
                    )

        # Añadir las restricciones y_i - y_j + H b_{ij} <= H - h para cada i en I
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    consCoeff = [1.0, -1.0, BIN_HEIGHT]
                    consVars = [f"y_{i}", f"y_{j}", f"b_{i},{j}"]
                    consRhs = BIN_HEIGHT - ITEM_HEIGHT
                    consSense = "L"  # "L" indica <=

                    # Añadir la restricción al problema
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                        senses=[consSense],
                        rhs=[consRhs]
                    )

        # Añadir la restricción x_i + W f_i <= 2W - w  para cada i en I
        for i in ITEMS:
            consCoeff = [1.0, BIN_WIDTH]  # Coeficientes para x_i y f_i
            consVars = [f"x_{i}", f"f_{i}"]  # Variables en la restricción
            consRhs = 2 * BIN_WIDTH - ITEM_WIDTH  # Lado derecho de la restricción
            consSense = "L"  # "L" indica <=

            # Añadir la restricción al problema
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                senses=[consSense],
                rhs=[consRhs]
            )

        # Añadir la restricción y_i + H f_i <= 2H - h para cada i en I
        for i in ITEMS:
            consCoeff = [1.0, BIN_WIDTH]  # Coeficientes para x_i y f_i
            consVars = [f"x_{i}", f"f_{i}"]  # Variables en la restricción
            consRhs = 2 * BIN_WIDTH - ITEM_WIDTH  # Lado derecho de la restricción
            consSense = "L"  # "L" indica <=

            # Añadir la restricción al problema
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                senses=[consSense],
                rhs=[consRhs]
            )

        # Desactivar la interrupción manual aquí
        manualInterruption.value = False
        # Resolver el modelo
        model.solve()

        # Obtener y mostrar los resultados
        solutionValues = model.solution.get_values()
        objectiveValue = model.solution.get_objectiveValue()
        print(f"Optimal value: {objectiveValue}")
        for var_name, value in zip(varsNames, solutionValues):
            print(f"{var_name} = {value}")
       
        status = model.solution.get_status()
        finalTime = model.get_time()
        solverTime=finalTime-initialTime
        solverTime=round(solverTime, 2)
        
        if status == 105:  # CPLEX código 105 = Time limit exceeded
            print("The solver stopped because it reached the time limit.")
            modelStatus="2" #valor en paver para marcar un optimo local

        # Enviar resultados a través de la cola
        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objectiveValue": objectiveValue,
            "solverTime": solverTime
        })
        
    except CplexSolverError as e:
        if e.args[2] == 1217:  # Codigo de error para "No solution exists"
            print("\nNo solutions for the given model.")
            modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solverStatus="4" #el solver finalizo la ejecucion del modelo
        else:
            print("CPLEX Solver Error:", e)
            modelStatus="12" #valor en paver para marcar un error desconocido
            solverStatus="10" #el solver tuvo un error en la ejecucion

        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objectiveValue": objectiveValue,
            "solverTime": solverTime
        })


def executeWithTimeLimit(maxTime):
    global modelStatus, solverStatus, objectiveValue, solverTime 
    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    manualInterruption = multiprocessing.Value('b', True)

    # Crear el subproceso que correrá la función
    process = multiprocessing.Process(target=createAndSolveModel, args=(queue,manualInterruption,maxTime))

    # Iniciar el subproceso
    process.start()

    initialTime = time.time()

    # Monitorear la cola mientras el proceso está en ejecución
    while process.is_alive():

        if manualInterruption.value:
            # Si se excede el tiempo, terminamos el process
            if time.time() - initialTime > maxTime:
                print("Limit time reached. Aborting process.")
                modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
                solverStatus="4" #el solver finalizo la ejecucion del modelo
                solverTime=maxTime
                process.terminate()
                process.join()
                break

        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            print(message)
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            objectiveValue = message["objectiveValue"]
            solverTime = message["solverTime"]



if __name__ == '__main__':
    # Ejecutar la función con un límite de tiempo de 10 segundos
    executeWithTimeLimit(EXECUTION_TIME)
    generator = TraceFileGenerator("output.trc")
    generator.write_trace_record(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)