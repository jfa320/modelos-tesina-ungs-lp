import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
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
J = generate_positions2_without_rotation(W, H, w, h) #posiciones
P = [(x, y) for x in range(W) for y in range(H)]  #puntos
C = create_C_matrix(W, H, J,w,h,P)

# Conjunto de posiciones válidas por item 
T = J
Q = len(T)  # Cantidad total de posiciones válidas por item

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

        # Definir variables y objetivos
        nVars = []
        xVars = []
        # Añadir las variables n_i
        for i in I:
            varsNames = f"n_{i}"
            model.variables.add(names=[varsNames], types=[model.variables.type.binary])
            nVars.append(varsNames)
        # Añadir las variables x_j^i
        for i in I:
            xVarsI = []
            for j in T:
                varsNames = f"x_{j}^{i}"
                model.variables.add(names=[varsNames], types=[model.variables.type.binary])
                xVarsI.append(varsNames)
            xVars.append(xVarsI)
        # Función objetivo: maximizar la suma de n_i
        objective = [1.0] * len(I)
        model.objective.set_linear(list(zip(nVars, objective)))
        
        # Restricción 1: Cada punto del bin está ocupado por a lo sumo un item
        for indexP,_ in enumerate(P):
            indexes = []
            coefficients = []
            for i in I:
                for indexJ,j in enumerate(T):
                    if C[indexJ][indexP] == 1:
                        indexes.append(f"x_{j}^{i}")
                        coefficients.append(1.0)
            consRhs=1.0
            consSense="L"
            addConstraint(model,coefficients,indexes,consRhs,consSense)

        # Restricción 2: No exceder el área del bin
        indexes = []
        coefficients = []
        seenIndexes = set()  # Conjunto para verificar duplicados
        for i in I:
            for indexJ, j in enumerate(T):
                for indexP, _ in enumerate(P):
                    if C[indexJ][indexP] == 1:
                        varsNames = f"x_{j}^{i}"
                        if varsNames not in seenIndexes:  # Verificar si ya se ha agregado
                            indexes.append(varsNames)
                            coefficients.append(1.0)
                            seenIndexes.add(varsNames)  # Marcar como agregado
        consRhs=W * H
        consSense="L"
        addConstraint(model,coefficients,indexes,consRhs,consSense)
        # Restricción 3: n_i <= suma(x_j^i)
        for i in I:
            indexes = [f"x_{j}^{i}" for j in T]
            coefficients = [1.0] * len(T)
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

        # Desactivar la interrupción manual aquí
        manualInterruption.value = False

        # Resolver el modelo
        model.solve()

        objectiveValue = model.solution.get_objective_value()

        # Imprimir resultados
        print("Optimal value:", objectiveValue)

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

# if __name__ == '__main__':
#     executeWithTimeLimit(EXECUTION_TIME)
#     generator = TraceFileGenerator("output.trc")
#     generator.write_trace_record(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)