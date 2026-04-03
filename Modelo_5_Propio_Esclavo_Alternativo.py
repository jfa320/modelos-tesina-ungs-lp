import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
from Objetos import Rebanada
from Objetos import Item

MODEL_NAME="Model5SlaveAlternative"
DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS = True  # Cambiar a True para desactivar el control de restricciones repetidas

EPS = 1e-9  # tolerancia numérica

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

    return items

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
    I = items  
    A_i=dualValues
    h = altoItemSinRotar
    w = anchoItemSinRotar
    W= anchoBin
    H = altoBin
    P = set(XY_x).union(XY_y)
    P_noRotado=XY_x
    P_rotado=XY_y
    P = list(P)  # Convertir a lista para iterar
    P.sort()  # Ordenar los pares (a, b) para consistencia
    
        
    posiciones_x_validas = []
    for (a, b) in P_noRotado:
        if a + w <= W and b + h <= H:
            posiciones_x_validas.append((a, b))

    posiciones_y_validas = []
    for (a, b) in P_rotado:
        if a + h <= W and b + w <= H:
            posiciones_y_validas.append((a, b))

    # R[(a,b,t)] = celdas cubiertas por un item que inicia en (a,b,t)
    R = {}

    for (a, b) in posiciones_x_validas:
        R[(a, b, 'x')] = [
            (x, y)
            for x in range(a, a + w)
            for y in range(b, b + h)
        ]

    for (a, b) in posiciones_y_validas:
        R[(a, b, 'y')] = [
            (x, y)
            for x in range(a, a + h)
            for y in range(b, b + w)
        ]
    
    
    try:
        # Crear el modelo
        model = cplex.Cplex()
        model.parameters.preprocessing.presolve.set(0)
        # model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

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
            return sum(A_i["pi"].get(f"({x},{y})", 0.0) for (x, y) in celdasCubiertas)
         
        # Variables no rotadas
        # ---------------------------------------------------------------------
        for (a, b) in posiciones_x_validas:
            varName = f"z_x_{a}_{b}"
            zVarsNoRotadas.append(varName)

            sumaDual = calcularSumaDual(a, b, 'x')
            coeff = 1.0 - sumaDual
            objCoeffs.append(coeff)

        addVariables(model, zVarsNoRotadas, objCoeffs, "B")
        objCoeffs.clear()

        # ---------------------------------------------------------------------
        # Variables rotadas
        # ---------------------------------------------------------------------
        for (a, b) in posiciones_y_validas:
            varName = f"z_y_{a}_{b}"
            zVarsRotadas.append(varName)

            sumaDual = calcularSumaDual(a, b, 'y')
            coeff = 1.0 - sumaDual
            objCoeffs.append(coeff)

        addVariables(model, zVarsRotadas, objCoeffs, "B")
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
    except CplexSolverError:
        raise
        

from Objetos import Item, Rebanada

def solveSlaveModel(model, queue, manualInterruption, binWidth, itemHeight, itemWidth):
    print("IN - Solve Slave Model")

    model.solve()

    statusString = model.solution.get_status_string()
    if "optimal" not in statusString.lower() and "feasible" not in statusString.lower():
        print("No hay solución factible en el esclavo")
        print("OUT - Solve Slave Model")
        return None, None, []

    objectiveValue = model.solution.get_objective_value()
    print(f"FO esclavo: {objectiveValue}")

    nombres = model.variables.get_names()
    valores = model.solution.get_values()

    itemsConstruidos = []

    for nombre, valor in zip(nombres, valores):
        if valor <= 0.5:
            continue

        parts = nombre.split("_")
        if len(parts) != 4:
            continue

        _, tipo, a, b = parts
        a = int(a)
        b = int(b)

        if tipo == "x":
            item = Item(
                alto=itemHeight,
                ancho=itemWidth,
                rotado=False
            )
        else:
            item = Item(
                alto=itemWidth,   # rotado
                ancho=itemHeight,
                rotado=True
            )

        item.setPosicionX(a)
        item.setPosicionY(b)
    

        itemsConstruidos.append(item)

    print(f"Items reconstruidos: {len(itemsConstruidos)}")

    if not itemsConstruidos:
        print("No se reconstruyó ningún item")
        print("OUT - Solve Slave Model")
        return None, objectiveValue, []

    height = obtenerYMaximo(construirPosicionesOcupadas(nombres, valores, itemHeight, itemWidth), itemHeight, itemWidth, itemsConstruidos)

    rebanada = Rebanada(
        alto=height,
        ancho=binWidth,
        items=itemsConstruidos
    )

    print("OUT - Solve Slave Model")

    variablesActivas = []

    nombres = model.variables.get_names()
    valores = model.solution.get_values()

    for nombre, valor in zip(nombres, valores):
        if valor > 0.5 and (nombre.startswith("z_x_") or nombre.startswith("z_y_")):
            variablesActivas.append(nombre)


    return rebanada, objectiveValue, variablesActivas

