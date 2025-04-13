import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
from Objetos import Rebanada
from Objetos import Item

MODEL_NAME="Model5SlaveAlternative"



def construirItems(variableNames, variableValues, altoItem, anchoItem):
    items = []
    print("CONSTRUIR ITEMS")
    print("variableNames: ",variableNames)
    print("variableValues: ",variableValues)
    for name, value in zip(variableNames, variableValues):
        if value > 0.5:  # Considerar solo las variables activas (a veces toma el 0.999 como un 1)
            parts = name.split("_")
            tipo, idValue = parts[0], int(parts[1])  # Obtener tipo (`onX` o `onY`) y el índice del ítem
            
            rotado = True if tipo == "onY" else False
            itemAgregar=Item(alto=altoItem, ancho=anchoItem, rotado=rotado,id=idValue)
            if(not itemAgregar in items):
                items.append(itemAgregar)
            
    return items

def construirPosicionesOcupadas(variableNames, variableValues):
    posicionesOcupadas = []
       
    for name, value in zip(variableNames, variableValues):
        if value > 0.5:  # Considerar solo variables activas
            parts = name.split("_")  # Dividir el nombre de la variable
            x, y = int(parts[2]), int(parts[3])  # Extraer x e y
            posicionesOcupadas.append((x, y))  # Agregar a la lista
    return posicionesOcupadas

def obtenerYMaximo(posicionesOcupadas,altoItem):
    if not posicionesOcupadas:
        return None  # Manejar caso donde la lista esté vacía
    
    print("alto: ",max(y for _, y in posicionesOcupadas))
    
    altoFinal=max(y for _, y in posicionesOcupadas) + altoItem
    return altoFinal

def createSlaveModelOLD(maxTime, XY_x, XY_y, items, dualValues):    
    print("--------------------------------------------------------------------------------------------------------------------")
    print("IN - Create Slave Model")
    XY = set(XY_x).union(set(XY_y)) 
    I = items  # Lista de ítems disponibles
    P_star=dualValues
    
    print("P_star: ",P_star)
    
    try:
        # Crear el modelo
        model = cplex.Cplex()

        model.set_problem_type(cplex.Cplex.problem_type.LP)

        model.parameters.timelimit.set(maxTime)
        initialTime=model.get_time()
        added_constraints = set()
        
        # Configurar como un problema de maximización
        model.objective.set_sense(model.objective.sense.maximize)

        # Función objetivo
        # variablesNames = []
        # objCoeffs = []
        # print("aca: "+str(P_star))
        # print("aca: "+str(I))      
        # for i in I:
        #     for (x, y) in XY_x:
        #         var_name = f"onX_{i}_{x}_{y}"
        #         variablesNames.append(var_name)
        #         objCoeffs.append(P_star[i.getId()-1])
        #     for (x, y) in XY_y:
        #         var_name = f"onY_{i}_{x}_{y}"
        #         variablesNames.append(var_name)
        #         objCoeffs.append(P_star[i.getId()-1])
        
        # Función objetivo
        variablesNames = []
        objCoeffs = []

        # Crear las variables para ítems acostados
        for i in I:
            for (x, y) in XY_x:
                var_name = f"onX_{i.getId()}_{x}_{y}"
                variablesNames.append(var_name)
                
                # Coeficiente de la variable en la función objetivo
                pi_i = P_star["pi"].get(i.getId(), 0)
                lambda_xy = P_star["lambda"].get((x, y), 0)
                coeff = pi_i - lambda_xy
                objCoeffs.append(coeff)

        # Crear las variables para ítems parados
        for i in I:
            for (x, y) in XY_y:
                var_name = f"onY_{i.getId()}_{x}_{y}"
                variablesNames.append(var_name)
                
                # Coeficiente de la variable en la función objetivo
                pi_i = P_star["pi"].get(i.getId(), 0)
                mu_xy = P_star["mu"].get((x, y), 0)
                coeff = pi_i - mu_xy
                objCoeffs.append(coeff)

        print("variablesNames: ",variablesNames)
        print("objCoeffs: ",objCoeffs)
        
        addVariables(model,variablesNames,objCoeffs,"B")

        # Restricción 1: No solapamiento de ítems
        for (x, y) in XY:
            coeficientes = {}  # Diccionario para consolidar coeficientes de las variables

            for i in I:
                if (x, y) in XY_x:  # Si la posición está en XY_x
                    var_name = f"onX_{i.getId()}_{x}_{y}"
                    coeficientes[var_name] = coeficientes.get(var_name, 0) + 1

                if (x, y) in XY_y:  # Si la posición está en XY_y
                    var_name = f"onY_{i.getId()}_{x}_{y}"
                    coeficientes[var_name] = coeficientes.get(var_name, 0) + 1

            # Crear listas de variables y coeficientes consolidados
            vars = list(coeficientes.keys())
            coefficients = list(coeficientes.values())
            # Agregar restricción al modelo
            addConstraintSet(model, coefficients, vars, rhs=1, sense="L", added_constraints=added_constraints)


        # Restricción 2: Un ítem no puede estar acostado y parado al mismo tiempo
        for i in I:
            coeficientes = {}  # Diccionario para consolidar coeficientes de las variables

            for (x, y) in XY_x:  # Posiciones en XY_x
                var_name = f"onX_{i.getId()}_{x}_{y}"
                coeficientes[var_name] = coeficientes.get(var_name, 0) + 1

            for (x, y) in XY_y:  # Posiciones en XY_y
                var_name = f"onY_{i.getId()}_{x}_{y}"
                coeficientes[var_name] = coeficientes.get(var_name, 0) + 1

            # Crear listas de variables y coeficientes consolidados
            vars = list(coeficientes.keys())
            coefficients = list(coeficientes.values())

            # Agregar restricción al modelo
            addConstraintSet(model, coefficients, vars, rhs=1, sense="L", added_constraints=added_constraints)

        print("OUT - Create Slave Model")    
        return model
    except CplexSolverError as e:
        handleSolverError(e)

def createSlaveModel(maxTime, XY_x, XY_y, items, dualValues, altoRebanada, anchoBin,altoItemSinRotar,anchoItemSinRotar):    
    print("--------------------------------------------------------------------------------------------------------------------")
    print("IN - Create Slave Model")
    I = items  # Lista de ítems disponibles
    A_i=dualValues
    h = altoItemSinRotar
    w = anchoItemSinRotar
    H_r= altoRebanada
    W= anchoBin
    M= max(H_r, W) #maximo entre la altura de la rebanada y el ancho del bin
    
    
    try:
        # Crear el modelo
        model = cplex.Cplex()

        model.set_problem_type(cplex.Cplex.problem_type.LP)

        model.parameters.timelimit.set(maxTime)
        initialTime=model.get_time()
        added_constraints = set()
        
        # Configurar como un problema de maximización
        model.objective.set_sense(model.objective.sense.maximize)

        # Función objetivo
        z_i_names = []
        s_i_names = []
        l_ij_names=[]
        d_ij_names=[]
        objCoeffs = []
        x_i_names = []
        y_i_names = []

        # Crear las variables para indicar si incluyo item en la rebanada (z_i)
        for i in I:
            var_name = f"z_{i.getId()}"
            z_i_names.append(var_name)
            # Coeficiente de la variable en la función objetivo
            A_i_valor = A_i["pi"].get(i.getId(), 0)
            coeff = A_i_valor
            objCoeffs.append(coeff)
            
        addVariables(model,z_i_names,objCoeffs,"B")
        
        # Crear variables para determinar si el item está rotado (s_i)
        for i in I:
            var_name = f"s_{i.getId()}"
            s_i_names.append(var_name)
            coeff = 0
            objCoeffs.append(coeff)
        addVariables(model,s_i_names,objCoeffs,"B")
            
        # Crear variables para determinar si el item i está a la izquierda de j (l_ij)
        for i in I:
            for j in I:
                if i != j:
                    var_name = f"l_{i.getId()}_{j.getId()}"
                    l_ij_names.append(var_name)
                    coeff = 0
                    objCoeffs.append(coeff)
        addVariables(model,l_ij_names,objCoeffs,"B")
        
        # Crear variables para determinar si el item i está debajo de j (d_ij)
        for i in I:
            for j in I:
                if i != j:
                    var_name = f"d_{i.getId()}_{j.getId()}"
                    d_ij_names.append(var_name)
                    coeff = 0
                    objCoeffs.append(coeff)            
        
        addVariables(model,d_ij_names,objCoeffs,"B")
          
        # Crear las variables para posicion sobre eje x del item i (x_i)
        for i in I:
            var_name = f"x_{i.getId()}"
            x_i_names.append(var_name)
            # Coeficiente de la variable en la función objetivo
            coeff = 0
            objCoeffs.append(coeff)
            
        addVariables(model,x_i_names,objCoeffs,"I")
        
        # Crear las variables para posicion sobre eje Y del item i (Y_i)
        for i in I:
            var_name = f"y_{i.getId()}"
            y_i_names.append(var_name)
            # Coeficiente de la variable en la función objetivo
            coeff = 0
            objCoeffs.append(coeff)

        addVariables(model,y_i_names,objCoeffs,"I")
        

        # Restricción 1: Relacion item y rotacion
        for i in I:
            indexes = [s_i_names[i.getId()-1],z_i_names[i.getId()-1]]
            coeffs = [1,-1]
            consRhs=0.0
            consSense="L"
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consItemRotado_{i.getId()}")
        
        # Restricción 2: No exceder limite a lo ancho de la rebanada
        for i in I:
            indexes = [x_i_names[i.getId()-1],s_i_names[i.getId()-1]]
            coeffs = [1,h-w]
            consRhs=W-w
            consSense="L"
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consLimiteAncho_{i.getId()}")
        
        # Restricción 3: No exceder limite a lo alto de la rebanada
        for i in I:
            indexes = [y_i_names[i.getId()-1],s_i_names[i.getId()-1]]
            coeffs = [1,w-h]
            consRhs=H_r-h
            consSense="L"
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consLimiteAlto_{i.getId()}")
        
        # Restricciones (4-5-6) para evitar superposicion entre items
        for i in I:
            for j in I:
                if i < j:
                    # x_i + w(1 - s_i) + h s_i <= x_j + M(1 - l_ij)
                    indexes = [x_i_names[i.getId()-1],s_i_names[i.getId()-1],x_i_names[j.getId(-1)],f"l_{i.getId()-1}_{j.getId()-1}"]
                    coeffs = [1,h-w,-1,M]
                    consRhs=M-w
                    consSense="L"
                    addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consSuperposicionX_{i.getId()}")

                    # y_i + h(1 - s_i) + w s_i <= y_j + M(1 - d_ij)
                    indexes = [y_i_names[i.getId()-1],s_i_names[i.getId()-1],y_i_names[j.getId()-1],f"d_{i.getId()-1}_{j.getId()-1}"]
                    coeffs = [1,w-h,-1,M]
                    consRhs=M-h
                    consSense="L"
                    addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consSuperposicionY_{i.getId()}")

                    # l_ij + d_ij >= z_i + z_j - 1
                    indexes = [f"l_{i.getId()-1}_{j.getId()-1}",f"d_{i.getId()-1}_{j.getId()-1}", z_i_names[i.getId()-1],z_i_names[j.getId()-1]]
                    coeffs = [1,1,-1,-1]
                    consRhs=-1
                    consSense="L"
                    addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consDisyuncion_{i.getId()}")
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
        
        # Obtener la función objetivo y sus coeficientes
        obj_coefs = model.objective.get_linear()  # Obtiene los coeficientes
        var_names = model.variables.get_names()   # Obtiene los nombres de las variables

        # Imprimir la función objetivo en formato legible
        objetivo_str = " + ".join([f"{coef}*{var}" for coef, var in zip(obj_coefs, var_names)])
        print(f"Función Objetivo: {objetivo_str}")
        
        

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
        alto= obtenerYMaximo(posicionesOcupadas,altoItem)
        
        print("Valor objetivo del esclavo", objectiveValue)
        if objectiveValue <= 0:
            print("El valor objetivo del esclavo es insignificante. Fin del proceso.")
            return None
        print("OUT - Solve Slave Model")
        
        rebanadaEncontrada=Rebanada(alto, anchoBin, items , posicionesOcupadas)
        print("Rebanada encontrada en ESCLAVO:", rebanadaEncontrada)
        return rebanadaEncontrada
    except CplexSolverError as e:
        handleSolverError(e, queue,solverTime)

