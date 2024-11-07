import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time
from Position_generator_modelo_3 import *
from Utils.Model_Functions import *
from Config import *

MODEL_NAME="Model3Pos2"

# Parámetros
W = BIN_WIDTH  # Ancho del bin
H = BIN_HEIGHT  # Alto del bin
w = ITEM_WIDTH # Ancho del item
h = ITEM_HEIGHT  # Alto del item

I = range(ITEMS_QUANTITY)  # Conjunto de items
J = generate_positions2_without_rotation(W, H, w, h)  # Posiciones sin rotación

J_rot = generate_positions2_without_rotation(W, H, h, w)  # Posiciones con rotación de 90 grados

P = [(x, y) for x in range(W) for y in range(H)]  # Puntos del bin
C = create_C_matrix(W, H, J, w, h, P)  # Matriz C para posiciones sin rotación
C_rot = create_C_matrix(W, H, J_rot, h, w, P)  # Matriz C para posiciones rotadas

# Conjunto de posiciones válidas por ítem
T = J
T_rot = J_rot
Q = len(T)  # Cantidad total de posiciones válidas por ítem
Q_rot = len(T_rot)  # Cantidad total de posiciones válidas rotadas por ítem

def createAndSolveModel(queue,manualInterruption,maxTime):
    #valores por default para enviar a paver
    modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1

    try:
        # Crear el modelo
        model = cplex.Cplex()
        model.set_results_stream(None) # deshabilito log de CPLEX de la info paso a paso
        model.objective.set_sense(model.objective.sense.maximize)
        model.parameters.timelimit.set(maxTime)
        
        initialTime=model.get_time()

        # Variables
        nVars = []
        xVars = []
        yVars = []

        # Añadir las variables n_i
        for i in I:
            varName = f"n_{i}"
            model.variables.add(names=[varName], types=[model.variables.type.binary])
            nVars.append(varName)

        # Añadir las variables x_j^i
        for i in I:
            xVarsI = []
            for j in T:
                varName = f"x_{j}^{i}"
                model.variables.add(names=[varName], types=[model.variables.type.binary])
                xVarsI.append(varName)
            xVars.append(xVarsI)

        # Añadir las variables y_j^i para las posiciones rotadas
        for i in I:
            yVarsI = []
            for j in T_rot:
                varName = f"y_{j}^{i}"
                model.variables.add(names=[varName], types=[model.variables.type.binary])
                yVarsI.append(varName)
            yVars.append(yVarsI)

        # Función objetivo: maximizar la suma de n_i
        objective = [1.0] * len(I)
        model.objective.set_linear(list(zip(nVars, objective)))

        # Restricción 1: Cada punto del bin está ocupado por a lo sumo un ítem (incluyendo rotaciones)
        for indexP, _ in enumerate(P):
            indexes = []
            coefficients = []
            for i in I:
                for indexJ, j in enumerate(T):
                    if C[indexJ][indexP] == 1:
                        indexes.append(f"x_{j}^{i}")
                        coefficients.append(1.0)
                for indexJ, j in enumerate(T_rot):
                    if C_rot[indexJ][indexP] == 1:
                        indexes.append(f"y_{j}^{i}")
                        coefficients.append(1.0)
            consRhs=1.0
            consSense="L"
            addConstraint(model,coefficients,indexes,consRhs,consSense)

        # Restricción 2: No exceder el área del bin
        indexes = []
        coefficients = []
        seenIndices = set()

        for i in I:
            for indexJ, j in enumerate(T):
                for indexP, _ in enumerate(P):
                    if C[indexJ][indexP] == 1:
                        varName = f"x_{j}^{i}"
                        if varName not in seenIndices:
                            indexes.append(varName)
                            coefficients.append(1.0)
                            seenIndices.add(varName)
            for indexJ, j in enumerate(T_rot):
                for indexP, _ in enumerate(P):
                    if C_rot[indexJ][indexP] == 1:
                        varName = f"y_{j}^{i}"
                        if varName not in seenIndices:
                            indexes.append(varName)
                            coefficients.append(1.0)
                            seenIndices.add(varName)
        consRhs=W * H
        consSense="L"
        addConstraint(model,coefficients,indexes,consRhs,consSense)

        # Restricción 3: n_i <= suma(x_j^i + y_j^i)
        for i in I:
            indexes = [f"x_{j}^{i}" for j in T] + [f"y_{j}^{i}" for j in T_rot]
            coefficients = [1.0] * (len(T) + len(T_rot))
            indexes.append(f"n_{i}")
            coefficients.append(-1.0)
            consRhs=0.0
            consSense="G"
            addConstraint(model,coefficients,indexes,consRhs,consSense)

        # Restricción 4: suma(x_j^i) <= Q(i) * n_i
        for i in I:
            indexes = [f"x_{j}^{i}" for j in T]
            coefficients = [1.0] * len(T)
            indexes.append(f"n_{i}")
            coefficients.append(-Q)
            consRhs=0.0
            consSense="L"
            addConstraint(model,coefficients,indexes,consRhs,consSense)

        # Restricción 5: suma(y_j^i) <= Q_rot(i) * n_i
        for i in I:
            indexes = [f"y_{j}^{i}" for j in T_rot]
            coefficients = [1.0] * len(T_rot)
            indexes.append(f"n_{i}")
            coefficients.append(-Q_rot)
            consRhs=0.0
            consSense="L"
            addConstraint(model,coefficients,indexes,consRhs,consSense)

        # Desactivar la interrupción manual aquí
        manualInterruption.value = False

        # Resolver el modelo
        model.solve()
        objectiveValue = model.solution.get_objective_value()

        # Imprimir resultados
        print("Optimal value:", objectiveValue)
        
        # #imprimo valor que toman las variables
        # for i, varName in enumerate(nVars):
        #     print(f"{varName} = {model.solution.get_values(varName)}")


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
