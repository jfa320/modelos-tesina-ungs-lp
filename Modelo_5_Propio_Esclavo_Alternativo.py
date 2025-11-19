import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
from Objetos import Rebanada
from Objetos import Item

MODEL_NAME="Model5SlaveAlternative"
EPSILON = 1e-9
DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS = True  # Cambiar a True para desactivar el control de restricciones repetidas

def construirItems(variableNames, variableValues, altoItem, anchoItem):
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

def construirPosicionesOcupadas(variableNames, variableValues):
    posicionesOcupadas = []
   
    dictCompleto = dict(zip(variableNames, variableValues))
    for name, value in dictCompleto.items():
        if 'z' in name and value > 0.5: 
            xVal=int(name.split("_")[2])
            yVal=int(name.split("_")[3])
            posicionesOcupadas.append((xVal, yVal))
    print("posiciones ocupadas: ",posicionesOcupadas)
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

def createSlaveModel(maxTime, XY_x, XY_y, items, dualValues, anchoBin,altoItemSinRotar,anchoItemSinRotar):    
    print("--------------------------------------------------------------------------------------------------------------------")
    print("IN - Create Slave Model")
    I = items  # Lista de ítems disponibles
    A_i=dualValues
    h = altoItemSinRotar
    w = anchoItemSinRotar
    W= anchoBin
    H = (max(b for (_, b) in XY_x | XY_y) + 1) if (XY_x or XY_y) else 0 #busco la posicion más alta
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
        model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

        model.parameters.timelimit.set(maxTime)
        initialTime=model.get_time()
        added_constraints = set()
        

        # Función objetivo
        zVarsRotadas = []
        zVarsNoRotadas = []
        objCoeffs = []

        
        # # Variables z^x_(a,b) para posiciones no rotadas
        # for (a, b) in P_noRotado:
        #     varName = f"z_x_{a}_{b}"
        #     zVarsNoRotadas.append(varName)
        #     A_i_valor = A_i["pi"].get(f"({a},{b})", 0) 
        #     coeff = ALPHA if A_i_valor == 0 else A_i_valor
        #     objCoeffs.append(coeff)
            
        # addVariables(model,zVarsNoRotadas,objCoeffs,"B")
        
        # objCoeffs.clear()
        
        # # Variables z^y_(a,b) para posiciones rotadas
        # for (a, b) in P_rotado:
        #     varName = f"z_y_{a}_{b}"
        #     zVarsRotadas.append(varName)
        #     A_i_valor = A_i["pi"].get(f"({a},{b})", 0) 
        #     coeff = ALPHA if A_i_valor == 0 else A_i_valor
        #     objCoeffs.append(coeff)

        # Helper para sumar los duales de las celdas cubiertas por (a,b,t)
        def calcularSumaDual(a, b, t):
            celdasCubiertas = R[(a, b, t)]
            return sum(A_i["pi"].get(f"({x},{y})", 0.0) for (x, y) in celdasCubiertas)

        # Variables z^x_(a,b) → ítems no rotados
        for (a, b) in P_noRotado:
            varName = f"z_x_{a}_{b}"
            zVarsNoRotadas.append(varName)
            
            sumaDual = calcularSumaDual(a, b, 'x')
            coeff = 1.0 - sumaDual     # costo reducido: 1 - ∑π
            objCoeffs.append(coeff)

        addVariables(model, zVarsNoRotadas, objCoeffs, "B")

        objCoeffs.clear()

        # Variables z^y_(a,b) → ítems rotados
        for (a, b) in P_rotado:
            varName = f"z_y_{a}_{b}"
            zVarsRotadas.append(varName)
            
            sumaDual = calcularSumaDual(a, b, 'y')
            coeff = 1.0 - sumaDual    # costo reducido: 1 - ∑π
            objCoeffs.append(coeff)

        addVariables(model, zVarsRotadas, objCoeffs, "B")

        objCoeffs.clear()
         
        
        print("Coeficientes de la función objetivo: ", objCoeffs)    
            
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
        
        posicionesOcupadas=construirPosicionesOcupadas(variableNames, variableValues)
        alto= obtenerYMaximo(posicionesOcupadas,altoItem,anchoItem,items)
        print("Items de la rebanada encontrada:", items)
        print("Valor objetivo del esclavo", objectiveValue)
        
        
        if objectiveValue  <= EPSILON:
            print("El valor objetivo del esclavo es insignificante. Fin del proceso.")
            return None, objectiveValue
        else:
            rebanadaEncontrada=Rebanada(alto, anchoBin, items , posicionesOcupadas)
            print(f"Rebanada encontrada!!: {rebanadaEncontrada}")
            print("OUT - Solve Slave Model")
            return rebanadaEncontrada, objectiveValue
    except CplexSolverError as e:
        print("Error al resolver el modelo esclavo:", e)
        handleSolverError(e, queue,solverTime)