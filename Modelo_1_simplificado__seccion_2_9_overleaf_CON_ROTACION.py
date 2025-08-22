import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time
from Utils.Model_Functions import *
from Config import *

MODEL_NAME="Model1"

def createAndSolveModel(queue,manualInterruption,maxTime):
    #valores por default para enviar a paver
    modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1
    try:
        # Crear un modelo de CPLEX
        model = cplex.Cplex()
        model.set_results_stream(None) # deshabilito log de CPLEX de la info paso a paso
        model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)
        model.parameters.timelimit.set(maxTime)
        
        initialTime=model.get_time()
        initialTimeT = time.time()

        # Definir variables y objetivos
        varsNames = [f"f_{i}" for i in ITEMS]
        coeffs = [1.0] * ITEMS_QUANTITY  # Esto asigna 1 como coeficiente a cada variable
        addVariables(model, varsNames, coeffs, "B")

        additionalVarsNames = [f"x_{i}" for i in ITEMS] + [f"y_{i}" for i in ITEMS] + [f"r_{i}" for i in ITEMS] 
        additionalCoeffObj = [0.0] * len(additionalVarsNames)
        model.variables.add(names=additionalVarsNames, obj=additionalCoeffObj, types="I" * (2 * ITEMS_QUANTITY) + "B" * ITEMS_QUANTITY)

        additionalVarsNames = []
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    additionalVarsNames.append(f"l_{i},{j}")  # Variable l_{ij}
                    additionalVarsNames.append(f"b_{i},{j}")  # Variable b_{ij}

        additionalCoeffObj = [0.0] * len(additionalVarsNames)
        addVariables(model, additionalVarsNames, additionalCoeffObj, "B")

        # Restricciones de no solapamiento
        for i in ITEMS:
            for j in ITEMS:
                if i < j:
                    consCoeff = [1.0, 1.0, 1.0, 1.0, -1.0, -1.0]
                    consVars = [f"l_{i},{j}", f"l_{j},{i}", f"b_{i},{j}", f"b_{j},{i}", f"f_{i}", f"f_{j}"]
                    consRhs = -1.0
                    consSense = "G"
                    addConstraint(model,consCoeff,consVars,consRhs,consSense)

        # Restricciones x_i - x_j + W l_{ij} <= W - w (1 - r_i) - h r_i
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    consCoeff = [1.0, -1.0, BIN_WIDTH, -ITEM_WIDTH + ITEM_HEIGHT ]
                    consVars = [f"x_{i}", f"x_{j}", f"l_{i},{j}", f"r_{i}"]
                    consRhs = BIN_WIDTH - ITEM_WIDTH
                    consSense = "L"
                    addConstraint(model,consCoeff,consVars,consRhs,consSense)

        # Restricciones y_i - y_j + H  b_{ij} <= H - h  (1 - r_i) - w r_i
        for i in ITEMS:
            for j in ITEMS:
                if i != j:
                    consCoeff = [1.0, -1.0, BIN_HEIGHT, -ITEM_HEIGHT+ITEM_WIDTH]
                    consVars = [f"y_{i}", f"y_{j}", f"b_{i},{j}", f"r_{i}"]
                    consRhs = BIN_HEIGHT - ITEM_HEIGHT
                    consSense = "L"
                    addConstraint(model,consCoeff,consVars,consRhs,consSense)

        # Restricciones para asegurar que los objetos estén dentro del bin (considerando rotación)
        for i in ITEMS:
            consXCoeff = [1.0, BIN_WIDTH, -ITEM_WIDTH + ITEM_HEIGHT]  # Coeficientes para x_i, f_i, r_i
            consXVars = [f"x_{i}", f"f_{i}", f"r_{i}"]
            consXRhs = 2 * BIN_WIDTH - ITEM_WIDTH
            consXSense = "L"
            addConstraint(model,consXCoeff,consXVars,consXRhs,consXSense)

            consYCoeff = [1.0, BIN_HEIGHT, -ITEM_HEIGHT + ITEM_WIDTH]  # Coeficientes para y_i, f_i, r_i
            consYVars = [f"y_{i}", f"f_{i}", f"r_{i}"]
            consYRhs = 2 * BIN_HEIGHT - ITEM_HEIGHT
            consYSense = "L"
            addConstraint(model,consYCoeff,consYVars,consYRhs,consYSense)

        # Desactivar la interrupción manual aquí
        manualInterruption.value = False

        # Resolver el modelo
        model.solve()

        # Obtener y mostrar los resultados
        objectiveValue = model.solution.get_objective_value()
        
        
        print("-------------------------------------------")
        print("Modelo 1 - Con Rotacion")
        print(f"Optimal value: {objectiveValue}")
        
        # solutionValues=model.solution.get_values
        # print("Variables values:")
        # for var_name, value in zip(varsNames, solutionValues):
        #     print(f"{var_name} = {value}")
        
        status = model.solution.get_status()
        # finalTime = model.get_time()
        # solverTime=finalTime-initialTime
        # solverTime=round(solverTime, 2)
        
        finalTimeT = time.time()
        solverTimeT = finalTimeT - initialTimeT
        solverTimeT = round(solverTimeT, 2)
        
        if status == 105:  # CPLEX código 105 = Time limit exceeded
            print("The solver stopped because it reached the time limit.")
            modelStatus="2" #valor en paver para marcar un optimo local

        # Enviar resultados a través de la cola
        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objectiveValue": objectiveValue,
            "solverTime": solverTimeT
        })

    except CplexSolverError as e:
        handleSolverError(e, queue,solverTime)


def executeWithTimeLimit(maxTime):
    global modelStatus, solverStatus, objectiveValue, solverTime 
    global excedingLimitTime
    excedingLimitTime=False

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
        if manualInterruption.value and time.time() - initialTime > maxTime:
            print("Limit time reached. Aborting process.")
            modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solverStatus="4" #el solver finalizo la ejecucion del modelo
            solverTime=maxTime
            excedingLimitTime=True
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
    
    if(excedingLimitTime):
        print("El modelo excedió el tiempo límite de ejecución.")
        objectiveValue = "n/a"
        modelStatus = "14"
        
    return CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime
