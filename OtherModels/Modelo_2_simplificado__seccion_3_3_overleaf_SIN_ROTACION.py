import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time
from Position_generator import generatePositionsCastro
from Utils.Model_Functions import *
from Config import *

#Basado en la simplificacion del modelo 2 del overleaf (modelo discretizado en posiciones) - ver seccion 3.3 de ese documento para modelo completo

MODEL_NAME="Model2Pos1"

#SET_POS_X  constante X en el modelo
#SET_POS_Y  constante Y en el modelo

#SET_POS_X_I constante X_i en el modelo
#SET_POS_Y_I constante Y_i en el modelo

SET_POS_X, SET_POS_Y, SET_POS_X_I, SET_POS_Y_I = generatePositionsCastro(BIN_WIDTH, BIN_HEIGHT, ITEM_WIDTH, ITEM_HEIGHT)

QUANTITY_X_I=len(SET_POS_X_I) #constante Q(X_i) del modelo
QUANTITY_Y_I=len(SET_POS_Y_I) #constante Q(Y_i) del modelo

def createAndSolveModel(queue,manualInterruption,maxTime):
    #valores por default para enviar a paver
    modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1

    try:
        # Crear un modelo de CPLEX
        model= cplex.Cplex()
        model.set_results_stream(None) # deshabilito log de CPLEX de la info paso a paso
        model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)
        model.parameters.timelimit.set(maxTime)

        initialTime=model.get_time()

        # Definir variables y objetivos
        varsNames = [f"m_{i}" for i in range(1, ITEMS_QUANTITY + 1)]
        coeffs = [1.0] * ITEMS_QUANTITY  
        addVariables(model, varsNames, coeffs, "B")

        additionalVarsNames = []
        for x in SET_POS_X_I:
            for y in SET_POS_Y_I:
                    for i in ITEMS:
                        additionalVarsNames.append(f"n_{i},{x},{y}") 

        for x in SET_POS_X:
            for y in SET_POS_Y:            
                additionalVarsNames.append(f"r_{x},{y}") 
        additionalCoeffObj = [0.0] * len(additionalVarsNames)
        addVariables(model, additionalVarsNames, additionalCoeffObj, "B")

        # Añadir la restricción r_{x,y} = sum_{i in N} sum_{x' in X_i, x-w+1 <= x' <= x} sum_{y' in Y_i, y-h+1 <= y' <= y} n_{i,x',y'} para cada (x, y) en X x Y
        for x in SET_POS_X:
            for y in SET_POS_Y:
                consCoeff = [1.0] 
                consVars = [f"r_{x},{y}"]  
                for i in ITEMS:
                    for xPrime in SET_POS_X_I:
                        if x - ITEM_WIDTH + 1 <= xPrime <= x:
                            for yPrime in SET_POS_Y_I:
                                if y - ITEM_HEIGHT + 1 <= yPrime <= y:
                                    consCoeff.append(-1.0)
                                    consVars.append(f"n_{i},{xPrime},{yPrime}")
                consRhs = 0.0  
                consSense = "E"  
                addConstraint(model,consCoeff,consVars,consRhs,consSense)

        # Añadir la restricción m_i <= sum_{x in X_i} sum_{y in Y_i} n_{i,x,y} para cada i en items - restriccion 2 del modelo
        for i in ITEMS:
            consCoeff = [1.0]  # Coeficiente para m_i
            consVars = [f"m_{i}"]  # Variable m_i
            # Añadir los coeficientes y variables de sum_{x in X_i} sum_{y in Y_i} n_{i,x,y}
            for x in SET_POS_X_I:
                for y in SET_POS_Y_I:
                    consCoeff.append(-1.0)
                    consVars.append(f"n_{i},{x},{y}")
            consRhs = 0.0  # Lado derecho de la restricción
            consSense = "L"  # "L" indica <=
            addConstraint(model,consCoeff,consVars,consRhs,consSense)

        # Añadir la restricción sum_{x in X_i} sum_{y in Y_i} n_{i,x,y} <= Q(X_i) Q(Y_i) m_i para cada i en items
        for i in ITEMS:
            consCoeff = [-1.0]  # Coeficiente para m_i
            consVars = [f"m_{i}"]  # Variable m_i

            # Añadir los coeficientes y variables de sum_{x in X_i} sum_{y in Y_i} n_{i,x,y}
            for x in SET_POS_X_I:
                for y in SET_POS_Y_I:
                    consCoeff.append(1.0)
                    consVars.append(f"n_{i},{x},{y}")
            consRhs = 0.0  # Lado derecho de la restricción
            consSense = "L"  # "L" indica <=
            addConstraint(model,consCoeff,consVars,consRhs,consSense)

        # Desactivar la interrupción manual aquí
        manualInterruption.value = False

        # Resolver el modelo
        model.solve()

        # Obtener y mostrar los resultados
        objectiveValue = model.solution.get_objective_value()

        print("Optimal value:", objectiveValue)
        
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
        handleSolverError(e, queue,solverTime)

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
        if manualInterruption.value and time.time() - initialTime > maxTime:
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
    return CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime

