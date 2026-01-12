import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
from Objetos import Rebanada
from Objetos import Item

MODEL_NAME="Model5SlaveAlternative"
DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS = True  # Cambiar a True para desactivar el control de restricciones repetidas

def construirItems1(variableNames, variableValues, altoItem, anchoItem):
    items = []
    varsNameFiltered = [elemento for elemento in variableNames if elemento.startswith('z') or elemento.startswith('s')]
    valuesFiltered= variableValues[:len(varsNameFiltered)]
    
    z_dict = {}
    s_dict = {}

    for i, elemento in enumerate(varsNameFiltered):
        z_dict[elemento] = valuesFiltered[i]
    
    for name, value in z_dict.items():
        if value > 0.5:  # Considerar solo las variables activas (a veces toma el 0.999 como un 1)
            parts = name.split("_")
            # Obtener coordenadas del item
            xValue = int(parts[2])  
            yValue = int(parts[3])  
            rotado = True if parts[1]=='y' else False
            itemAgregar=Item(alto=altoItem, ancho=anchoItem, rotado=rotado,posicionX=xValue, posicionY=yValue)
            if rotado:
                itemAgregar.setAlto(anchoItem)
                itemAgregar.setAncho(altoItem)
            if(not itemAgregar in items):
                items.append(itemAgregar)
    print("Items construidos: ", items)
    return items


def construirItems(variableNames, variableValues, altoItem, anchoItem):
    items = []

    for name, value in zip(variableNames, variableValues):
        if not name.startswith("z_") or value <= 0.5:
            continue

        parts = name.split("_")
        # z_<rot>_<x>_<y>
        rot = parts[1]
        xValue = int(parts[2])
        yValue = int(parts[3])

        rotado = (rot == "y")

        alto = anchoItem if rotado else altoItem
        ancho = altoItem if rotado else anchoItem

        item = Item(
            alto=alto,
            ancho=ancho,
            rotado=rotado,
            posicionX=xValue,
            posicionY=yValue
        )

        if item not in items:
            items.append(item)

    print("Items construidos:", items)
    return items


def construirPosicionesOcupadas(variableNames, variableValues, items):
    posicionesOcupadas = set()

    for it in items:
        x = it.getPosicionX()
        y = it.getPosicionY()
        w = it.getAncho()
        h = it.getAlto()

        for dx in range(w):
            for dy in range(h):
                posicionesOcupadas.add((x + dx, y + dy))

    return list(posicionesOcupadas)




def construirPosicionesOcupadas(variableNames, variableValues, altoItem, anchoItem):
    posicionesOcupadas = set()

    for name, value in zip(variableNames, variableValues):
        if not name.startswith("z_") or value <= 0.5:
            continue

        parts = name.split("_")
        rot = parts[1]
        x0 = int(parts[2])
        y0 = int(parts[3])

        rotado = (rot == "y")
        alto = anchoItem if rotado else altoItem
        ancho = altoItem if rotado else anchoItem

        for dx in range(ancho):
            for dy in range(alto):
                posicionesOcupadas.add((x0 + dx, y0 + dy))

    posicionesOcupadas = list(posicionesOcupadas)
    print("Posiciones ocupadas:", posicionesOcupadas)
    return posicionesOcupadas

    

def obtenerYMaximo(posicionesOcupadas,altoItem,anchoItem,items):
    #TODO: Revisar si este metodo es necesario
    if not posicionesOcupadas:
        return None  # Manejar caso donde la lista esté vacía
    itemPosYMax = max(items, key=lambda item: item.getPosicionY())
    return itemPosYMax.getPosicionY() + itemPosYMax.getAlto()

def rectsSolapan(x1, y1, w1, h1, x2, y2, w2, h2):
    return not (
        x1 + w1 <= x2 or x2 + w2 <= x1 or
        y1 + h1 <= y2 or y2 + h2 <= y1
    )


def createSlaveModel(maxTime, XY_x, XY_y, items, dualValues, anchoBin,altoItemSinRotar,anchoItemSinRotar,altoBin):    
    print("--------------------------------------------------------------------------------------------------------------------")
    print("IN - Create Slave Model")
    I = items  # Lista de ítems disponibles
    A_i=dualValues
    h = altoItemSinRotar
    w = anchoItemSinRotar

    # -------------------------
    # EPSILON adaptativo (global)
    # -------------------------
    lambdaEps = 0.04     # fijo global
    epsMin = 1e-4        # fijo global

    piValues = list(A_i["pi"].values()) if "pi" in A_i and A_i["pi"] else []
    absPiValues = [abs(v) for v in piValues if v is not None]

    avgAbsPi = (sum(absPiValues) / len(absPiValues)) if absPiValues else 0.0
    itemArea = w * h

    EPSILON = max(epsMin, lambdaEps * avgAbsPi * itemArea)

    print(f"EPSILON adaptativo = {EPSILON} (avgAbsPi={avgAbsPi}, itemArea={itemArea}, lambda={lambdaEps}, epsMin={epsMin})")


    W= anchoBin
    H = altoBin
    P = set(XY_x).union(XY_y)
    P_noRotado=XY_x
    P_rotado=XY_y
    P = list(P)  # Convertir a lista para iterar
    P.sort()  # Ordenar los pares (a, b) para consistencia
    

    # Listas etiquetadas con tipo de rotación
    # ('x') para no rotado, ('y') para rotado
    posiciones_x = [((x, y), 'x') for (x, y) in P_noRotado]
    posiciones_y = [((x, y), 'y') for (x, y) in P_rotado]

    # Unificamos en una sola lista de posiciones posibles con tipo
    todasLasPosiciones = posiciones_x + posiciones_y


    # R[(a,b,t)] = lista de posiciones (x,y) cubiertas por el ítem que inicia en (a,b,t)
    R = {}
    for (pos, t) in todasLasPosiciones:
        a, b = pos
        ancho, alto = (w, h) if t == 'x' else (h, w)
        R[(a, b, t)] = [(x, y)
                        for x in range(a, a + ancho)
                        for y in range(b, b + alto)
                        if 0 <= x < W and 0 <= y < H]
    
    try:
        # Crear el modelo
        model = cplex.Cplex()
        model.parameters.preprocessing.presolve.set(0)
        # model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

        model.parameters.mip.pool.intensity.set(4)   # buscar soluciones alternativas
        model.parameters.mip.pool.capacity.set(8)    # hasta 8 soluciones
        model.parameters.mip.pool.replace.set(2)     # diversidad


        model.parameters.timelimit.set(maxTime)
        initialTime=model.get_time()
        added_constraints = set()
        

        # Función objetivo
        zVarsRotadas = []
        zVarsNoRotadas = []
        objCoeffs = []

        # Helper para sumar los duales de las celdas cubiertas por (a,b,t)
        def calcularSumaDual(a, b, t):
            celdasCubiertas = R[(a, b, t)]
            return sum(A_i["pi"].get(f"({x+1},{y+1})", 0.0) for (x, y) in celdasCubiertas)


        # Variables z^x_(a,b) → ítems no rotados
        for (a, b) in P_noRotado:
            varName = f"z_x_{a}_{b}"
            zVarsNoRotadas.append(varName)
            
            sumaDual = calcularSumaDual(a, b, 'x')
            coeff = sumaDual + EPSILON
            objCoeffs.append(coeff)

        addVariables(model, zVarsNoRotadas, objCoeffs, "B")

        objCoeffs.clear()

        # Variables z^y_(a,b) → ítems rotados
        for (a, b) in P_rotado:
            varName = f"z_y_{a}_{b}"
            zVarsRotadas.append(varName)
            
            sumaDual = calcularSumaDual(a, b, 'y')
            coeff = sumaDual + EPSILON
            objCoeffs.append(coeff)

        addVariables(model, zVarsRotadas, objCoeffs, "B")
        print("Coeficientes de la función objetivo: ", objCoeffs)    
        objCoeffs.clear()
         
        # Restricciones
        # Restricciones de no solapamiento
        coverMap = {}
        consRhs=1

        for (a, b, t), celdas in R.items():
            varName = f"z_{t}_{a}_{b}"
            for (x, y) in celdas:
                coverMap.setdefault((x, y), set()).add(varName)
                

        for (x, y), varsQueCubren in coverMap.items():
            coeffs = [1.0] * len(varsQueCubren)
            addConstraintSet(
                model,
                coeffs,
                varsQueCubren,
                consRhs,
                "L",
                added_constraints,
                f"consNoOverlap_{x}_{y}",
                DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
            )
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
        if(manualInterruption is not None):
            manualInterruption.value = False
        print("Voy a resolver el esclavo")
        # Resolver el modelo
        model.solve()
        objectiveValue = model.solution.get_objective_value()

        # Imprimir resultados
        print("Optimal value:", objectiveValue)
        #imprimo valor que toman las variables
        for _, varName in enumerate(model.variables.get_names()):
            print(f"{varName} = {model.solution.get_values(varName)}")
            
        # Obtener la función objetivo y sus coeficientes
        obj_coefs = model.objective.get_linear()  # Obtiene los coeficientes
        var_names = model.variables.get_names()   # Obtiene los nombres de las variables

        # Imprimir la función objetivo en formato legible -- ENTIENDO QUE LO AGREGUE PARA DEBUGEAR, LO DEJO COMENTADO
        # objetivo_str = " + ".join([f"{coef}*{var}" for coef, var in zip(obj_coefs, var_names)])
        # print(f"Función Objetivo: {objetivo_str}")

        status = model.solution.get_status()
        finalTime = model.get_time()
        solverTime=finalTime-initialTime
        solverTime=round(solverTime, 2)
                        
        if status == 105:  # CPLEX código 105 = Time limit exceeded
            print("The solver stopped because it reached the time limit.")
            modelStatus="2" #valor en paver para marcar un optimo local

        
        variableNames = model.variables.get_names()
        variableValues = model.solution.get_values()
        items=construirItems(variableNames, variableValues, altoItem, anchoItem)
        
        posicionesOcupadas=construirPosicionesOcupadas(variableNames, variableValues, altoItem, anchoItem)
        alto= obtenerYMaximo(posicionesOcupadas,altoItem,anchoItem,items)
        print("Items de la rebanada encontrada:", items)
        print("Valor objetivo del esclavo", objectiveValue)
        
        
        rebanadaEncontrada = Rebanada(alto, anchoBin, items, posicionesOcupadas)

        print(f"Rebanada encontrada!!: {rebanadaEncontrada}")
        print("OUT - Solve Slave Model")

        return rebanadaEncontrada, objectiveValue
    
    except CplexSolverError as e:
        print("Error al resolver el modelo esclavo:", e)
        handleSolverError(e, queue,solverTime)

