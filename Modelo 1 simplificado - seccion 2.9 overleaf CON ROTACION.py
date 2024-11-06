import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
import multiprocessing
import time


MODEL_NAME="Model1"

modelStatus="1"
solverStatus="1"
objectiveValue=0
solverTime=1

# Caso 1:
# ITEMS_QUANTITY=6 # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 6 # W en el modelo
# BIN_HEIGHT = 4 # H en el modelo

# ITEM_WIDTH= 2 # w en el modelo
# ITEM_HEIGHT= 3 # h en el modelo


#Caso 2: 

# ITEMS_QUANTITY=6 # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 5 # W en el modelo
# BIN_HEIGHT = 5 # H en el modelo

# ITEM_WIDTH= 3 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

#Caso 3: 

# ITEMS_QUANTITY=8 # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 6 # W en el modelo
# BIN_HEIGHT = 6 # H en el modelo

# ITEM_WIDTH= 4 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

#Caso 4: 

# ITEMS_QUANTITY=5 # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 7 # W en el modelo
# BIN_HEIGHT = 3 # H en el modelo

# ITEM_WIDTH= 3 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

# Caso 5: 

# ITEMS_QUANTITY = 6  # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 6  # W en el modelo
# BIN_HEIGHT = 3  # H en el modelo

# ITEM_WIDTH = 3  # w en el modelo
# ITEM_HEIGHT = 2  # h en el modelo

#prueba para validar el corte al minuto de la ejecucion

CASE_NAME="inst2"

ITEMS_QUANTITY= 10 # constante n del modelo
ITEMS = list(range(1, ITEMS_QUANTITY + 1)) # constante I del modelo
BIN_WIDTH = 6 # W en el modelo
BIN_HEIGHT = 4 # H en el modelo

ITEM_WIDTH= 2 # w en el modelo
ITEM_HEIGHT= 3 # h en el modelo

EXECUTION_TIME=2 # in seconds

def createAndSolveModel(queue,manualInterruption,maxTime):
    #valores por default para enviar a paver
    modelStatus="1"
    solverStatus="1"
    objectiveValue=0
    solverTime=1
    
    try:
        # Crear un modelo de CPLEX
        model = cplex.Cplex()
        
        model.set_results_stream(None) # deshabilito log de CPLEX de la info paso a paso
        
        initialTime=model.get_time()

        # Definir el problema como uno de maximización
        model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

        # Definir el limite tiempo de la ejecución en un minuto
        model.parameters.timelimit.set(maxTime)

        # Variables f_i: indica si el objeto i está ubicado dentro del bin
        varsNames = [f"f_{i}" for i in ITEMS]

        # Definir los coeficientes de la función objetivo (todos son 1)
        coeffs = [1.0] * ITEMS_QUANTITY  # Esto asigna 1 como coeficiente a cada variable

        # Definir que las variables sean binarias
        model.variables.add(names=varsNames, obj=coeffs, types="B" * ITEMS_QUANTITY)

        # Variables adicionales: x_i, y_i y r_i (indica si el objeto está rotado)
        additionalVarsNames = [f"x_{i}" for i in ITEMS]
        additionalVarsNames += [f"y_{i}" for i in ITEMS]
        additionalVarsNames += [f"r_{i}" for i in ITEMS]  # Variable de rotación

        additionalCoeffObj = [0.0] * len(additionalVarsNames)
        model.variables.add(names=additionalVarsNames, obj=additionalCoeffObj, types="I" * (2 * ITEMS_QUANTITY) + "B" * ITEMS_QUANTITY)

        # Variables l_{ij}, b_{ij}
        additionalVarsNames = []
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    additionalVarsNames.append(f"l_{i},{j}")  # Variable l_{ij}
                    additionalVarsNames.append(f"b_{i},{j}")  # Variable b_{ij}

        # Añadir variables adicionales con coeficiente 0
        additionalCoeffObj = [0.0] * len(additionalVarsNames)
        model.variables.add(names=additionalVarsNames, obj=additionalCoeffObj, types="B" * len(additionalVarsNames))

        # Restricciones de no solapamiento
        for i in ITEMS:
            for j in ITEMS:
                if i < j:
                    consCoeff = [1.0, 1.0, 1.0, 1.0, -1.0, -1.0]
                    consVars = [f"l_{i},{j}", f"l_{j},{i}", f"b_{i},{j}", f"b_{j},{i}", f"f_{i}", f"f_{j}"]
                    consRhs = -1.0
                    consSense = "G"

                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                        senses=[consSense],
                        rhs=[consRhs]
                    )

        # Restricciones x_i - x_j + W l_{ij} <= W - w (1 - r_i) - h r_i
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    consCoeff = [1.0, -1.0, BIN_WIDTH, -ITEM_WIDTH + ITEM_HEIGHT ]
                    consVars = [f"x_{i}", f"x_{j}", f"l_{i},{j}", f"r_{i}"]
                    consRhs = BIN_WIDTH - ITEM_WIDTH
                    consSense = "L"

                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                        senses=[consSense],
                        rhs=[consRhs]
                    )

        # Restricciones y_i - y_j + H  b_{ij} <= H - h  (1 - r_i) - w r_i
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    consCoeff = [1.0, -1.0, BIN_HEIGHT, -ITEM_HEIGHT+ITEM_WIDTH]
                    consVars = [f"y_{i}", f"y_{j}", f"b_{i},{j}", f"r_{i}"]
                    consRhs = BIN_HEIGHT - ITEM_HEIGHT
                    consSense = "L"

                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                        senses=[consSense],
                        rhs=[consRhs]
                    )

        # Restricciones para asegurar que los objetos estén dentro del bin (considerando rotación)
        for i in ITEMS:
            consXCoeff = [1.0, BIN_WIDTH, -ITEM_WIDTH + ITEM_HEIGHT]  # Coeficientes para x_i, f_i, r_i
            consXVars = [f"x_{i}", f"f_{i}", f"r_{i}"]
            consXRhs = 2 * BIN_WIDTH - ITEM_WIDTH
            consXSense = "L"

            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consXVars, consXCoeff)],
                senses=[consXSense],
                rhs=[consXRhs]
            )

            consYCoeff = [1.0, BIN_HEIGHT, -ITEM_HEIGHT + ITEM_WIDTH]  # Coeficientes para y_i, f_i, r_i
            consYVars = [f"y_{i}", f"f_{i}", f"r_{i}"]
            consYRhs = 2 * BIN_HEIGHT - ITEM_HEIGHT
            consYSense = "L"

            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consYVars, consYCoeff)],
                senses=[consYSense],
                rhs=[consYRhs]
            )

        # Desactivar la interrupción manual aquí
        manualInterruption.value = False

        # Resolver el modelo
        model.solve()

        # Obtener y mostrar los resultados
        solutionValues = model.solution.get_values()
        objectiveValue = model.solution.get_objective_value()

        print(f"Optimal value: {objectiveValue}")
        
        # print("Variables values:")
        # for var_name, value in zip(varsNames, solutionValues):
        #     print(f"{var_name} = {value}")
        
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
            # Si se excede el tiempo, terminamos el proceso
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

