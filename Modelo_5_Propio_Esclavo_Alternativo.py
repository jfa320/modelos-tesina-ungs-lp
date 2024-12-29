import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
from Objetos import Rebanada
from Objetos import Item

MODEL_NAME="Model5SlaveAlternative"

# Constantes y conjuntos
# XY_x = []  # Conjunto de posiciones (x, y) para ítems "acostados"
# XY_y = []  # Conjunto de posiciones (x, y) para ítems "parados"
# I = []      # Conjunto de ítems
# w = 5        # Ancho del ítem
# h = 5        # Alto del ítem
# W = 10        # Ancho del bin
# H = 10        # Alto del bin
# P_star = [] # Soluciones duales, una lista con valores duales Y*_i


def construirItems(variableNames, variableValues, altoItem, anchoItem):
    items = []
    for name, value in zip(variableNames, variableValues):
        if value > 0.5:  # Considerar solo las variables activas (a veces toma el 0.999 como un 1)
            parts = name.split("_")
            tipo, i = parts[0], int(parts[1])  # Obtener tipo (`onX` o `onY`) y el índice del ítem
            
            if tipo == "onX":  # Ítem no rotado
                items.append(Item(alto=altoItem, ancho=anchoItem, rotado=False))
            elif tipo == "onY":  # Ítem rotado
                items.append(Item(alto=anchoItem, ancho=altoItem, rotado=True))
    return items

def construirPosicionesOcupadas(variableNames, variableValues):
    posicionesOcupadas = []
    for name, value in zip(variableNames, variableValues):
        if value > 0.5:  # Considerar solo variables activas
            parts = name.split("_")  # Dividir el nombre de la variable
            x, y = int(parts[2]), int(parts[3])  # Extraer x e y
            posicionesOcupadas.append((x, y))  # Agregar a la lista
    return posicionesOcupadas

def obtenerYMaximo(posicionesOcupadas):
    if not posicionesOcupadas:
        return None  # Manejar caso donde la lista esté vacía
    return max(y for _, y in posicionesOcupadas)

def createSlaveModel(maxTime, XY_x, XY_y, items, dualValues):
    XY = set(XY_x).union(set(XY_y)) 
    I = items  # Lista de ítems disponibles
    P_star=dualValues

    try:
        # Crear el modelo
        model = cplex.Cplex()

        model.set_problem_type(cplex.Cplex.problem_type.LP)

        model.parameters.timelimit.set(maxTime)
        initialTime=model.get_time()

        # Configurar como un problema de maximización
        model.objective.set_sense(model.objective.sense.maximize)

        # Función objetivo
        variablesNames = []
        objCoeffs = []        
        for i in I:
            for (x, y) in XY_x:
                var_name = f"onX_{i}_{x}_{y}"
                variablesNames.append(var_name)
                objCoeffs.append(P_star[i])
            for (x, y) in XY_y:
                var_name = f"onY_{i}_{x}_{y}"
                variablesNames.append(var_name)
                objCoeffs.append(P_star[i])

        addVariables(model,variablesNames,objCoeffs,"B")

        # Restricción 1: No solapamiento de ítems
        for (x, y) in XY:
            vars = []
            coefficients = []
            for i in I:
                if (x, y) in XY_x:
                    vars.append(f"onX_{i}_{x}_{y}")
                    coefficients.append(1)
                if (x, y) in XY_y:
                    vars.append(f"onY_{i}_{x}_{y}")
                    coefficients.append(1)
            addConstraint(model, coefficients, vars, 1,"L")

        # Restricción 2: Un ítem no puede estar acostado y parado al mismo tiempo
        for i in I:
            vars = []
            coefficients = []
            for (x, y) in XY_x:
                vars.append(f"onX_{i}_{x}_{y}")
                coefficients.append(1)
            for (x, y) in XY_y:
                vars.append(f"onY_{i}_{x}_{y}")
                coefficients.append(1)
            addConstraint(model, coefficients, vars,1,"L")
            
        return model
    except CplexSolverError as e:
        handleSolverError(e)


def solveSlaveModel(model, queue, manualInterruption, anchoBin, altoItem, anchoItem):
    
    #valores por default para enviar a paver
    modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1
    
    try:
        # Desactivar la interrupción manual aquí
        initialTime = model.get_time()
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
        variableNames = model.variables.get_names()
        variableValues = model.solution.get_values()
        items=construirItems(variableNames, variableValues, altoItem, anchoItem)
        posicionesOcupadas=construirPosicionesOcupadas(variableNames, variableValues)
        alto= obtenerYMaximo(posicionesOcupadas)
        return Rebanada(alto, anchoBin, items , posicionesOcupadas)
    except CplexSolverError as e:
        handleSolverError(e, queue,solverTime)



# TODO: borrar esto previo a las pruebas

# def createAndSolveSlaveModel(queue, manualInterruption, maxTime, XY_x, XY_y, items, dualValues):
#     XY = set(XY_x).union(set(XY_y)) 
#     I = items  # Lista de ítems disponibles
#     P_star=dualValues
#     #valores por default para enviar a paver
#     modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1
    
#     try:
#         # Crear el modelo
#         model = cplex.Cplex()

#         model.set_problem_type(cplex.Cplex.problem_type.LP)

#         model.parameters.timelimit.set(maxTime)
#         initialTime=model.get_time()

#         # Configurar como un problema de maximización
#         model.objective.set_sense(model.objective.sense.maximize)

#         # Función objetivo
#         variablesNames = []
#         objCoeffs = []        
#         for i in I:
#             for (x, y) in XY_x:
#                 var_name = f"onX_{i}_{x}_{y}"
#                 variablesNames.append(var_name)
#                 objCoeffs.append(P_star[i])
#             for (x, y) in XY_y:
#                 var_name = f"onY_{i}_{x}_{y}"
#                 variablesNames.append(var_name)
#                 objCoeffs.append(P_star[i])

#         addVariables(model,variablesNames,objCoeffs,"B")

#         # Restricción 1: No solapamiento de ítems
#         for (x, y) in XY:
#             vars = []
#             coefficients = []
#             for i in I:
#                 if (x, y) in XY_x:
#                     vars.append(f"onX_{i}_{x}_{y}")
#                     coefficients.append(1)
#                 if (x, y) in XY_y:
#                     vars.append(f"onY_{i}_{x}_{y}")
#                     coefficients.append(1)
#             addConstraint(model, coefficients, vars, 1,"L")

#         # Restricción 2: Un ítem no puede estar acostado y parado al mismo tiempo
#         for i in I:
#             vars = []
#             coefficients = []
#             for (x, y) in XY_x:
#                 vars.append(f"onX_{i}_{x}_{y}")
#                 coefficients.append(1)
#             for (x, y) in XY_y:
#                 vars.append(f"onY_{i}_{x}_{y}")
#                 coefficients.append(1)
#             addConstraint(model, coefficients, vars,1,"L")

#         # Desactivar la interrupción manual aquí
#         manualInterruption.value = False
        
#         # Resolver el modelo
#         model.solve()
#         objectiveValue = model.solution.get_objective_value()

#         # Imprimir resultados
#         print("Optimal value:", objectiveValue)

#         status = model.solution.get_status()
#         finalTime = model.get_time()
#         solverTime=finalTime-initialTime
#         solverTime=round(solverTime, 2)
                        
#         if status == 105:  # CPLEX código 105 = Time limit exceeded
#             print("The solver stopped because it reached the time limit.")
#             modelStatus="2" #valor en paver para marcar un optimo local

#         # Enviar resultados a través de la cola
#         queue.put({
#             "modelStatus": modelStatus,
#             "solverStatus": solverStatus,
#             "objectiveValue": objectiveValue,
#             "solverTime": solverTime
#         })
#     except CplexSolverError as e:
#         handleSolverError(e, queue,solverTime)


# def executeWithTimeLimit(maxTime):
#     global modelStatus, solverStatus, objectiveValue, solverTime 
#     # Crear una cola para recibir los resultados del subproceso
#     queue = multiprocessing.Queue()

#     # Crear una variable compartida para manejar la interrupción manual
#     manualInterruption = multiprocessing.Value('b', True)

#     # Crear el subproceso que correrá la función
#     process = multiprocessing.Process(target=createAndSolveSlaveModel, args=(queue,manualInterruption,maxTime))

#     # Iniciar el subproceso
#     process.start()

#     initialTime = time.time()

#     # Monitorear la cola mientras el proceso está en ejecución
#     while process.is_alive():
#         if manualInterruption.value and time.time() - initialTime > maxTime:
#             print("Limit time reached. Aborting process.")
#             modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
#             solverStatus="4" #el solver finalizo la ejecucion del modelo
#             solverTime=maxTime
#             process.terminate()
#             process.join()
#             break
#         time.sleep(0.1)  # Evitar consumir demasiados recursos

#     # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
#     while not queue.empty():
#         message = queue.get()
#         if isinstance(message, dict):
#             print(message)
#             modelStatus = message["modelStatus"]
#             solverStatus = message["solverStatus"]
#             objectiveValue = message["objectiveValue"]
#             solverTime = message["solverTime"]
#     return CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime