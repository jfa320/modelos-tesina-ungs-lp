import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
from Objetos import Rebanada
from Objetos import Item

MODEL_NAME="Model5SlaveAlternative"

EPSILON = 1e-6

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
    print("IN - Create Slave Model")
    XY = set(XY_x).union(set(XY_y)) 
    I = items  # Lista de ítems disponibles
    P_star=dualValues
    print(f"P_star: {P_star}")
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
                objCoeffs.append(P_star[i.getId()-1])
            for (x, y) in XY_y:
                var_name = f"onY_{i}_{x}_{y}"
                variablesNames.append(var_name)
                objCoeffs.append(P_star[i.getId()-1])

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
        print("OUT - Create Slave Model")    
        return model
    except CplexSolverError as e:
        handleSolverError(e)


def solveSlaveModel(model, queue, manualInterruption, anchoBin, altoItem, anchoItem):
    print("IN - Solve Slave Model")
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
        
        if objectiveValue < EPSILON:
            print("El valor objetivo del esclavo es insignificante. Fin del proceso.")
            return None
        print("OUT - Solve Slave Model")
        return Rebanada(alto, anchoBin, items , posicionesOcupadas)
    except CplexSolverError as e:
        handleSolverError(e, queue,solverTime)

