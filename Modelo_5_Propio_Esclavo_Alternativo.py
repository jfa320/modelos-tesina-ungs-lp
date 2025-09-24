import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
from Objetos import Rebanada
from Objetos import Item

MODEL_NAME="Model5SlaveAlternative"
EPSILON = 1e-5
DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS = True  # Cambiar a True para desactivar el control de restricciones repetidas
ALPHA = 0.01

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


def construirItems20072025ULTIMO(variableNames, variableValues, altoItem, anchoItem):
    items = []
    varsNameFiltered = [elemento for elemento in variableNames if elemento.startswith('z') or elemento.startswith('s')]
    valuesFiltered= variableValues[:len(varsNameFiltered)]
    
    z_dict = {}
    s_dict = {}

    for i, elemento in enumerate(varsNameFiltered):
        if elemento.startswith('z'):
            z_dict[elemento] = valuesFiltered[i]
        elif elemento.startswith('s'):
            s_dict[elemento] = valuesFiltered[i]
    
    for name, value in z_dict.items():
        if value > 0.5:  # Considerar solo las variables activas (a veces toma el 0.999 como un 1)
            parts = name.split("_")
            # Obtener coordenadas del item
            xValue = int(parts[1])  
            yValue = int(parts[2])  
            rotado = True if s_dict.get(f"s_{str(xValue)}_{str(yValue)}") > 0.5 else False
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

def construirPosicionesOcupadas20072025ULTIMO(variableNames, variableValues):
    posicionesOcupadas = []
   
    dictCompleto = dict(zip(variableNames, variableValues))
    
    for name, value in dictCompleto.items():
        if 'z' in name and value > 0.5: 
            xVal=int(name.split("_")[1])
            yVal=int(name.split("_")[2])
            posicionesOcupadas.append((xVal, yVal))
    print("posiciones ocupadas: ",posicionesOcupadas)
    return posicionesOcupadas
    

def obtenerYMaximo(posicionesOcupadas,altoItem,anchoItem,items):
    #TODO: Revisar si este metodo es necesario
    if not posicionesOcupadas:
        return None  # Manejar caso donde la lista esté vacía
    itemPosYMax = max(items, key=lambda item: item.getPosicionY())
    return itemPosYMax.getPosicionY() + itemPosYMax.getAlto()

def obtenerYMaximo080602025(posicionesOcupadas,altoItem,anchoItem):
    #TODO: Revisar si este metodo es necesario
    if not posicionesOcupadas:
        return None  # Manejar caso donde la lista esté vacía
    altoFinal=max(y for _, y in posicionesOcupadas) + max(altoItem,anchoItem)
    return altoFinal

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
    P = set(XY_x).union(XY_y)
    P_noRotado=XY_x
    P_rotado=XY_y
    P = list(P)  # Convertir a lista para iterar
    P.sort()  # Ordenar los pares (a, b) para consistencia
    
    O = []

    # Listas etiquetadas con tipo de rotación
    # ('x') para no rotado, ('y') para rotado
    posiciones_x = [((x, y), 'x') for (x, y) in P_noRotado]
    posiciones_y = [((x, y), 'y') for (x, y) in P_rotado]

    # Unificamos en una sola lista de posiciones posibles con tipo
    todasLasPosiciones = posiciones_x + posiciones_y

    # Construcción del conjunto O
    # Armamos todos los pares ordenados sin repeticiones
    for i in range(len(todasLasPosiciones)):
        (pos1, tipo1) = todasLasPosiciones[i]
        x1, y1 = pos1
        w1, h1 = (w, h) if tipo1 == 'x' else (h, w)

        for j in range(i + 1, len(todasLasPosiciones)):
            (pos2, tipo2) = todasLasPosiciones[j]
            x2, y2 = pos2
            w2, h2 = (w, h) if tipo2 == 'x' else (h, w)

            if rectsSolapan(x1, y1, w1, h1, x2, y2, w2, h2):
                # Guardamos el conflicto como tuplas ((x,y,tipo), (x',y',tipo'))
                O.append( ((x1, y1, tipo1), (x2, y2, tipo2)) )

    
    
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
        zVars  = []
        zVarsRotadas = []
        zVarsNoRotadas = []
        objCoeffs = []

        
        # Variables z^x_(a,b) para posiciones no rotadas
        for (a, b) in P_noRotado:
            varName = f"z_x_{a}_{b}"
            zVarsNoRotadas.append(varName)
            A_i_valor = A_i["pi"].get(f"({a},{b})", 0) 
            coeff = ALPHA if A_i_valor == 0 else A_i_valor
            objCoeffs.append(coeff)
            
        addVariables(model,zVarsNoRotadas,objCoeffs,"B")
        
        objCoeffs.clear()
        
        # Variables z^y_(a,b) para posiciones rotadas
        for (a, b) in P_rotado:
            varName = f"z_y_{a}_{b}"
            zVarsRotadas.append(varName)
            A_i_valor = A_i["pi"].get(f"({a},{b})", 0) 
            coeff = ALPHA if A_i_valor == 0 else A_i_valor
            objCoeffs.append(coeff)
         
        
        print("Coeficientes de la función objetivo: ", objCoeffs)    
            
        addVariables(model,zVarsRotadas,objCoeffs,"B")
        objCoeffs.clear()
               
        zVars= zVarsNoRotadas + zVarsRotadas
        # Restricciones
        varIndex = {name: i for i, name in enumerate(zVars)}

         # Restricciones de no solapamiento
        for ((a1, b1, i), (a2, b2, j)) in O:
            var1 = f"z_{i}_{a1}_{b1}"
            var2 = f"z_{j}_{a2}_{b2}"

            if var1 in varIndex and var2 in varIndex:
                indexes = [var1,var2]
                coeffs = [1,1]
                consRhs=1
                consSense="L"
                
                addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consNoOverlap_{var1}_{var2}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)
            
        print("OUT - Create Slave Model")    
        return model
    except CplexSolverError as e:
        handleSolverError(e)
        
def createSlaveModel20072025ULTIMO(maxTime, XY_x, XY_y, items, dualValues, altoRebanada, anchoBin,altoItemSinRotar,anchoItemSinRotar):    
    print("--------------------------------------------------------------------------------------------------------------------")
    print("IN - Create Slave Model")
    I = items  # Lista de ítems disponibles
    A_i=dualValues
    h = altoItemSinRotar
    w = anchoItemSinRotar
    H_r= altoRebanada
    W= anchoBin
    M= max(H_r, W) #maximo entre la altura de la rebanada y el ancho del bin
    P = set(XY_x).union(XY_y)
    P_noRotado=XY_x
    P_rotado=XY_y
    P = list(P)  # Convertir a lista para iterar
    P.sort()  # Ordenar los pares (a, b) para consistencia
    print(f"H_r: {H_r}, W: {W}, h: {h}, w: {w}, M: {M}")
    print("A_i: ",A_i)
    print("ITEMS: ",I)
    print("P: ", P)
    
    try:
        # Crear el modelo
        model = cplex.Cplex()
        model.parameters.preprocessing.presolve.set(0)
        model.set_problem_type(cplex.Cplex.problem_type.LP)

        model.parameters.timelimit.set(maxTime)
        initialTime=model.get_time()
        added_constraints = set()
        
        # Configurar como un problema de maximización
        model.objective.set_sense(model.objective.sense.maximize)

        # Función objetivo
        zVars  = []
        sVars  = []
        lVars, dVars = [], []
        
        objCoeffs = []

        # Crear las variables para indicar si incluyo item en la rebanada (z_a_b)
        for (a, b) in P:
            var_name = f"z_{a}_{b}" 
            zVars.append(var_name)
            # Coeficiente de la variable en la función objetivo
            A_i_valor = A_i["pi"].get(f"({a},{b})", 0) 
            # coeff = A_i_valor + ALPHA
            coeff = ALPHA if A_i_valor == 0 else A_i_valor
            objCoeffs.append(coeff)
            
        addVariables(model,zVars,objCoeffs,"B")
        
        objCoeffs.clear()
        # Crear variables para determinar si el item está rotado (s_a_b)
        for (a, b) in P:
            var_name = f"s_{a}_{b}"
            sVars.append(var_name)
            coeff = 0
            objCoeffs.append(coeff)
        addVariables(model,sVars,objCoeffs,"B")
            
        # creo variables para determinar si el item a esta a la izquierda de b (l_a,b) o si esta debajo (d_a,b)
        objCoeffs.clear()
        pairs = [(p1, p2) for idx1, p1 in enumerate(P) for idx2, p2 in enumerate(P) if idx1 < idx2]
        for (a, b), (a2, b2) in pairs:
            lName = f"l_{a}_{b}_{a2}_{b2}"
            dName = f"d_{a}_{b}_{a2}_{b2}"
            coeff = 0
            lVars.append(lName)
            dVars.append(dName)
     
        objCoeffs=[0] * len(lVars+dVars)  
        addVariables(model,lVars+dVars,objCoeffs,"B")
        
        objCoeffs.clear()
        
        
        # for (a,b) in P_rotado:
        #     sVar = f"s_{a}_{b}"
        #     zVar = f"z_{a}_{b}"
            
        #     # z_{a,b} ≤ s_{a,b} para a,b del conjunto "rotadas"
        #     indexes = [zVar,sVar]
        #     coeffs = [1,-1]
        #     consRhs=0
        #     consSense="L"
            
        #     addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consFixItemRotado_{a}_{b}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)
        
        # for (a,b) in P_noRotado:
        #     sVar = f"s_{a}_{b}"
        #     zVar = f"z_{a}_{b}"
            
        #     # z_{a,b} ≤ 1 - s_{a,b} para a,b del conjunto "rotadas"
        #     indexes = [zVar,sVar]
        #     coeffs = [1,1]
        #     consRhs=1
        #     consSense="L"
            
        #     addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consFixItemNoRotado_{a}_{b}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)

        
        # Restricciones
        for (a, b) in P:
            sVar = f"s_{a}_{b}"
            zVar = f"z_{a}_{b}"
            
            # Restricción 1: Relacion item y rotacion
            # s_{a,b} ≤ z_{a,b}
            
            indexes = [sVar,zVar]
            coeffs = [1,-1]
            consRhs=0
            consSense="L"
            
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consItemRotado_{a}_{b}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)

            # # Restricción 2: No exceder limite a lo ancho de la rebanada
            # a + w(1-s_{a,b}) + h s_{a,b} ≤ W + M(1 - z_{a,b})
            
            # Esto es un parche. Despues sacarlo, al solucionar el tema de incentivar mas las posiciones donde los duales son 0.
            # indexes = [sVar,zVar]
            # coeffs = [-w+h,M]
            # consRhs=W+M-a-w
            # consSense="L"
            # addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consLimiteAncho_{a}_{b}")
            
           
            
            # Restricción 3: No exceder limite a lo alto de la rebanada
            # b ≤ H_r + M(1 - z_{a,b})
            indexes = [zVar]
            coeffs = [M]
            consRhs=H_r+M-b
            consSense="L"
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consLimiteAlto_{a}_{b}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)
        
        for (a, b), (aPrime, bPrime) in pairs:
            zVar1, zVar2 = f"z_{a}_{b}", f"z_{aPrime}_{bPrime}"
            sVar1, sVar2 = f"s_{a}_{b}", f"s_{aPrime}_{bPrime}"
            lVar = f"l_{a}_{b}_{aPrime}_{bPrime}"
            dVar = f"d_{a}_{b}_{aPrime}_{bPrime}"

            # Restricción 4: No solape horizontal
            # a + w(1-s) + h s ≤ a2 + M(1 - l)
            
            indexes = [sVar1,lVar]
            coeffs = [-w+h,M]
            consRhs=aPrime+M-a-w
            consSense="L"
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consNoSolapamientoX_{a}_{b}_{aPrime}_{bPrime}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)

            # Restricción 5: No solape vertical
            # b + h(1-s) + w s ≤ b2 + M(1 - d)
            indexes = [sVar1, dVar]
            coeffs = [-h+w, M]
            consRhs = bPrime+M-b-h
            consSense="L"
            addConstraintSet(model, coeffs, indexes, consRhs, consSense, added_constraints, f"consNoSolapamientoY_{a}_{b}_{aPrime}_{bPrime}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)

            # Restricción 6: Disyunción
            # l + d ≥ z1 + z2 - 1
            indexes = [lVar, dVar, zVar1, zVar2]
            coeffs = [1, 1, -1, -1]
            consRhs = -1
            consSense="G"
            addConstraintSet(model, coeffs, indexes, consRhs, consSense, added_constraints, f"consDisyuncion_{a}_{b}_{aPrime}_{bPrime}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)
            
        
        
      
        
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
        
        print("Valor objetivo del esclavo", objectiveValue)
        
        
        if objectiveValue  <= EPSILON:
            print("El valor objetivo del esclavo es insignificante. Fin del proceso.")
            return None
        else:
            rebanadaEncontrada=Rebanada(alto, anchoBin, items , posicionesOcupadas)
            print(f"Rebanada encontrada!!: {rebanadaEncontrada}")
            print("OUT - Solve Slave Model")
            return rebanadaEncontrada
    except CplexSolverError as e:
        print("Error al resolver el modelo esclavo:", e)
        handleSolverError(e, queue,solverTime)

