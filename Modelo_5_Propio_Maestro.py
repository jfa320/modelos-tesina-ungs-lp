import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time
from Utils.Model_Functions import *
from Config import *

MODEL_NAME="Model5Master"

#TODO: Refactor y ajustar estas constantes (moverlas a archivo?)

# Constantes del problema
H = 10  # Alto del bin (ejemplo)
W = 10  # Ancho del bin (ejemplo)
I = []  # Lista de ítems disponibles
R = []  # Lista de rebanadas disponibles
I_r = {}  # Diccionario con ítems en cada rebanada
C_r = {}  # Cantidad de ítems en cada rebanada
H_r = {}  # Alto de cada rebanada
H_ab= {} # subconjunto de posiciones que inician en (a, b) para items en orientacion horizontal
V_ab= {} # subconjunto de posiciones que inician en (a, b) para items en orientacion vertical
R_r_xy={} # indica si la rebanada r con r ∈ R posee un item en la coordenada (x, y)

def createAndSolveModel(queue,manualInterruption,maxTime):
    #valores por default para enviar a paver
    modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1

    try:
        # Crear instancia del problema
        model = cplex.Cplex()
        model.set_problem_type(cplex.Cplex.problem_type.LP) 

        model.parameters.timelimit.set(maxTime)
        initialTime=model.get_time()

        # Variables
        # Variables p_r (binarias)
        p_r_names = [f"p_{r}" for r in R]
        model.variables.add(names=p_r_names, types=[model.variables.type.binary] * len(R))

        # Variables y_r (enteras)
        y_r_names = [f"y_{r}" for r in R]
        model.variables.add(names=y_r_names, types=[model.variables.type.integer] * len(R))


        # Función objetivo
        coef_obj = [C_r[r] for r in R]  # Coeficientes de p_r en la función objetivo
        model.objective.set_sense(model.objective.sense.maximize)
        model.objective.set_linear(list(zip(p_r_names, coef_obj)))


        # Restricción 1: Un ítem no puede estar en más de una rebanada activa
        for i in I:
            indexes = [p_r_names[r] for r in R if i in I_r[r]]
            coefs = [1] * len(indexes)
            consRhs=1.0
            consSense="L"
            addConstraint(model,coefs,indexes,consRhs,consSense)

        # Ejemplos de conjuntos:
        # H_(0,0)={(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)}
        # V_(5,1)​={(5,1),(6,1)}
        # R_r_xy[1] = [(0, 0), (1, 0), (0, 1), (1, 1)] Coordenadas ocupadas en la rebanada 1

        # (2), (3), (4): No solapamiento
        for r in R:
            for (a, b) in R_r_xy[r]:
                # Obtener posiciones horizontales y verticales
                H_ab_positions = H_ab.get((a, b), [])
                V_ab_positions = V_ab.get((a, b), [])
                
                # Restricción (2): No solapamiento horizontal
                if H_ab_positions:
                    coeff = [1 if (x, y) in R_r_xy[r] else 0 for (x, y) in H_ab_positions]
                    vars = [f"p_{r}"] * len(H_ab_positions)
                    addConstraint(model, coeff, vars, rhs=1, sense="L")
                
                # Restricción (3): No solapamiento vertical
                if V_ab_positions:
                    coeff = [1 if (x, y) in R_r_xy[r] else 0 for (x, y) in V_ab_positions]
                    vars = [f"p_{r}"] * len(V_ab_positions)
                    addConstraint(model, coeff, vars, rhs=1, sense="L")
                
                # Restricción (4): No solapamiento en intersección
                overlap_positions = set(H_ab_positions) & set(V_ab_positions)
                if overlap_positions:
                    coeff = [1 if (x, y) in R_r_xy[r] else 0 for (x, y) in overlap_positions]
                    vars = [f"p_{r}"] * len(overlap_positions)
                    addConstraint(model, coeff, vars, rhs=1, sense="L")

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
