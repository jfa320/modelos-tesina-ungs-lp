import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *

MODEL_NAME="Model5Master"



def createMasterModelOLD(maxTime,rebanadas,altoBin,anchoBin,altoItem,anchoItem,items,posXY_x,posXY_y):
    print("IN - Create Master Model")
    H = altoBin  # Alto del bin 
    W = anchoBin  # Ancho del bin
    I = items  # Lista de ítems disponibles
    R = rebanadas  # Lista de rebanadas disponibles
    H_ab= {} # subconjunto de posiciones que inician en (a, b) para items en orientacion horizontal.
    for a, b in posXY_x:
        H_ab[(a, b)] = [(x, y) for x in range(a, a + anchoItem) for y in range(b, b + altoItem)]
        
    V_ab= {} # subconjunto de posiciones que inician en (a, b) para items en orientacion vertical.
    for a, b in posXY_y:
        V_ab[(a, b)] = [(x, y) for x in range(a, a + altoItem) for y in range(b, b + anchoItem)]
        
    R_r_xy={} # indica si la rebanada r con r ∈ R posee un item en la coordenada (x, y)
    
    # Recorrer cada rebanada en R y llenar R_r_xy
    for r_idx, rebanada in enumerate(R, start=0): 
        R_r_xy[r_idx] = rebanada.getPosicionesOcupadas()

    
    try:
        # Crear instancia del problema
        model = cplex.Cplex()
        model.set_problem_type(cplex.Cplex.problem_type.MILP) 

        model.parameters.timelimit.set(maxTime)

        # Variables
        # Variables p_r (binarias)
        p_r_names = [f"p_{r.getId()-1}" for r in R]
        model.variables.add(names=p_r_names, types=[model.variables.type.binary] * len(R))

        # Variables y_r (enteras)
        y_r_names = [f"y_{r.getId()}" for r in R]
        model.variables.add(names=y_r_names, types=[model.variables.type.integer] * len(R))

        # Función objetivo
        coef_obj = [r.getTotalItems() for r in R]  # Coeficientes de p_r en la función objetivo
    
        model.objective.set_sense(model.objective.sense.maximize)
        model.objective.set_linear(list(zip(p_r_names, coef_obj)))

        added_constraints = set()
        # Restricción 1: Un ítem no puede estar en más de una rebanada activa
        for i in I:
            print("Rebanadas: ",R)
            indexes = [p_r_names[r.getId()-1] for r in R if r.contieneItem(i)]
            coeffs = [1] * len(indexes)
            consRhs=1.0
            consSense="L"
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consItem_{i.getId()}")
        
        
        # Esta restriccion es vieja
        # Ejemplos de conjuntos:
        # H_(0,0)={(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)}
        # V_(5,1)​={(5,1),(6,1)}
        # R_r_xy[1] = [(0, 0), (1, 0), (0, 1), (1, 1)] Coordenadas ocupadas en la rebanada 1
        # (2), (3), (4): No solapamiento
        for r in R:
            for (a, b) in R_r_xy[r.getId()-1]:
                # Obtener posiciones horizontales y verticales
                H_ab_positions = H_ab.get((a, b), [])
                V_ab_positions = V_ab.get((a, b), [])
                
                # Restricción (2): No solapamiento horizontal
                if H_ab_positions:
                    coeff = [1 if (x, y) in R_r_xy[r.getId()-1] else 0 for (x, y) in H_ab_positions]
                    vars = [f"p_{r.getId()}"] * len(H_ab_positions)
                    print("COEFFS Y VARS")
                    print(coeff)
                    print(vars) 
                    addConstraintSet(model, coeff, vars, rhs=1, sense="L",added_constraints=added_constraints, constraintName=f"consH_{a}_{b}")
                
                # Restricción (3): No solapamiento vertical
                if V_ab_positions:
                    coeff = [1 if (x, y) in R_r_xy[r.getId()-1] else 0 for (x, y) in V_ab_positions]
                    vars = [f"p_{r.getId()}"] * len(V_ab_positions)
                    print("COEFFS Y VARS")
                    print(coeff)
                    print(vars) 
                    addConstraintSet(model, coeff, vars, rhs=1, sense="L",added_constraints=added_constraints, constraintName=f"consV_{a}_{b}")
                
                # Restricción (4): No solapamiento en intersección
                overlap_positions = set(H_ab_positions) & set(V_ab_positions)
                if overlap_positions:
                    coeff = [1 if (x, y) in R_r_xy[r.getId()-1] else 0 for (x, y) in overlap_positions]
                    vars = [f"p_{r.getId()}"] * len(overlap_positions)
                    addConstraintSet(model, coeff, vars, rhs=1, sense="L",added_constraints=added_constraints, constraintName=f"consHV_{a}_{b}")
       
        
        # Generación del conjunto de posiciones válidas
        posicionesValidas = set()  # Usamos un conjunto para evitar duplicados

        # Unimos todas las posiciones de H_a,b y V_a,b para cada (a, b)
        for (a, b) in H_ab.keys():  # Iteramos sobre todas las claves de H_a,b
            posicionesValidas.update(H_ab[(a, b)])  # Agregamos las posiciones horizontales
        for (a, b) in V_ab.keys():  # Iteramos sobre todas las claves de V_a,b
            posicionesValidas.update(V_ab[(a, b)])  # Agregamos las posiciones verticales

        # Convertimos el conjunto a una lista si se necesita orden específico
        posicionesValidas = list(posicionesValidas)
        
        # Generación de la restricción en CPLEX
        # for (a, b) in posicionesValidas:  # Iteramos sobre las posiciones válidas
        #     coeficientes = {}  # Diccionario para consolidar coeficientes de cada p_r

        #     for r in R:  # Iteramos sobre cada rebanada
        #         # Verificamos posiciones en H_{a,b}
        #         for (x, y) in H_ab.get((a, b), []):  # Posiciones horizontales asociadas a (a, b)
        #             if (x, y) in R_r_xy[r.getId() - 1]:  # Si (x, y) está ocupado por la rebanada r
        #                 var_name = p_r_names[r.getId() - 1]  # Nombre de la variable p_r[r]
        #                 coeficientes[var_name] = coeficientes.get(var_name, 0) + 1  # Sumar contribución

        #         # Verificamos posiciones en V_{a,b}
        #         for (x, y) in V_ab.get((a, b), []):  # Posiciones verticales asociadas a (a, b)
        #             if (x, y) in R_r_xy[r.getId() - 1]:  # Si (x, y) está ocupado por la rebanada r
        #                 var_name = p_r_names[r.getId() - 1]  # Nombre de la variable p_r[r]
        #                 coeficientes[var_name] = coeficientes.get(var_name, 0) + 1  # Sumar contribución

        #     # Crear SparsePair consolidado
        #     restriccion = cplex.SparsePair()
        #     restriccion.ind = list(coeficientes.keys())  # Variables involucradas
        #     restriccion.val = list(coeficientes.values())  # Coeficientes consolidados
            
        #     addConstraintSet(model,  restriccion.val, restriccion.ind , rhs=1, sense="L",added_constraints=added_constraints, constraintName=f"consColisionRebanadas_{a}_{b}")
        
        # Restricción para evitar colisiones de ítems entre distintas rebanadas
        for (a, b) in posicionesValidas:
            # Construir la suma de términos en la restricción
            terms = []
            coefs = []

            for r in R:
                for (x, y) in H_ab.get((a, b), []):  # Asegurar que H_a_b[(a,b)] existe
                    if (x, y) in R_r_xy[r.getId()-1]:
                        terms.append(f"p_{r.getId()-1}")
                        coefs.append(1)

                for (x, y) in V_ab.get((a, b), []):  # Asegurar que V_a_b[(a,b)] existe
                    if (r, x, y) in R_r_xy:
                        terms.append(f"p_{r.getId()-1}")
                        coefs.append(1)
            # Agregar la restricción al modelo: suma de términos ≤ 1
            if terms:
                addConstraintSet(model,  coefs, terms , rhs=1, sense="L",added_constraints=added_constraints, constraintName=f"consNoSolapamiento_{a}_{b}")
        
        print("OUT - Create Master Model")
        return model
    
    except CplexSolverError as e:
        handleSolverError(e)


def createMasterModelDeprecated(maxTime,rebanadas,altoBin,anchoBin,altoItem,anchoItem,items,posXY_x,posXY_y):
    print("IN - Create Master Model")
    H = altoBin  # Alto del bin 
    R = rebanadas  # Lista de rebanadas disponibles
    #C_r= se puede modelar usando el metodo rebanada.getTotalItems() - Cantidad de items en rebanadas
    I = items  # Lista de ítems disponibles
    #A_ir = no es necesario crear un conjunto de posiciones ocupadas por rebanada, se puede modelar usando el metodo rebanada.contieneItem(item)
    #H_r = no es necesario crear un conjunto de alturas ocupadas por rebanada, se puede modelar usando el metodo rebanada.get_alto()
    
    try:
        # Crear instancia del problema
        model = cplex.Cplex()
        model.set_problem_type(cplex.Cplex.problem_type.MILP) 

        model.parameters.timelimit.set(maxTime)

        # Variables
        # Variables p_r (binarias)
        p_r_names = [f"p_{r.getId()}" for r in R]
        model.variables.add(names=p_r_names, types=[model.variables.type.binary] * len(R))

        # Variables y_r (enteras)
        y_r_names = [f"y_{r.getId()}" for r in R]
        model.variables.add(names=y_r_names, types=[model.variables.type.integer] * len(R))
        
        # Variables z_{rr'} 
        z_rr_names = []
        z_rr_indices = {}
        for r1 in R:
            for r2 in R:
                if r1.getId() != r2.getId():
                    name = f"z_{r1.getId()}_{r2.getId()}"
                    z_rr_names.append(name)
                    z_rr_indices[(r1.getId(), r2.getId())] = name
        model.variables.add(names=z_rr_names, types=[model.variables.type.binary] * len(z_rr_names))

        print("TOTAL ITEMS POR REBANADA")
        for r in R:
            print(r.getTotalItems() )

        # Función objetivo
        coef_obj = [r.getTotalItems() for r in R]  # Coeficientes de p_r en la función objetivo
    
        model.objective.set_sense(model.objective.sense.maximize)
        model.objective.set_linear(list(zip(p_r_names, coef_obj)))

        added_constraints = set()
        
        # Restricción 1: Un ítem no puede estar en más de una rebanada activa
        for i in I:
            indexes = [p_r_names[r.getId()-1] for r in R if r.contieneItem(i)]
            coeffs = [1] * len(indexes)
            consRhs=1.0
            consSense="L"
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consItem_{i.getId()}")
        
        # Restricción 2: no colision de rebanada r con r'
        for r in R:
            for r_prime in R:
                if r.getId() != r_prime.getId():
                    y_r = f"y_{r.getId()}"
                    y_r_prime = f"y_{r_prime.getId()}"
                    z_rr_prime = z_rr_indices[(r.getId(), r_prime.getId())]
                    coef = [1, -1 , H]
                    rhs= H - r.get_alto()
                    vars=[y_r, y_r_prime, z_rr_prime]
                    addConstraintSet(model, coef, vars, rhs=rhs, sense="L", added_constraints=added_constraints,
                                     constraintName=f"consColisionUp_{r.getId()}_{r_prime.getId()}")
                
        # Restricción 3: no colision de rebanada r' con r
        for r in R:
            for r_prime in R:
                if r.getId() != r_prime.getId():
                    y_r = f"y_{r.getId()}"
                    y_r_prime = f"y_{r_prime.getId()}"
                    z_rr_prime = z_rr_indices[(r.getId(), r_prime.getId())]
                    coef = [1, -1 , -H]
                    rhs= -r_prime.get_alto()
                    vars=[y_r_prime, y_r, z_rr_prime]
                    addConstraintSet(model, coef, vars, rhs=rhs, sense="L", added_constraints=added_constraints,
                                     constraintName=f"consColisionDown_{r.getId()}_{r_prime.getId()}")
                
        print("OUT - Create Master Model")
        return model
    
    except CplexSolverError as e:
        handleSolverError(e)


def createMasterModel2(altoBin, anchoBin, items, rebanadas, S):
    try:
        problem = cplex.Cplex()
        problem.set_problem_type(cplex.Cplex.problem_type.LP)
        problem.objective.set_sense(problem.objective.sense.maximize)
        
        # Variables binaria p_r
        pNames = [f"p_{r.getId()}" for r in rebanadas]
        problem.variables.add(names=pNames, types=[problem.variables.type.binary] * len(rebanadas))
        
        # Variables enteras y_r
        yNames = [f"y_{r.getId()}" for r in rebanadas]
        problem.variables.add(names=yNames, types=[problem.variables.type.integer] * len(rebanadas), lb=[0] * len(rebanadas))
        
        # Restricción (1): Cada ítem solo puede estar en una rebanada
        for i in items:
            indices = [pNames[r.getId()-1] for r in rebanadas if i in r.get_items()]
            problem.linear_constraints.add(
                lin_expr=[[indices, [1] * len(indices)]],
                senses=["L"],
                rhs=[1],
                names=[f"consItem_{i.getId()}"]
            )
        
        # Restricción (2): Cada punto (a,b) solo puede estar en una rebanada
        for (a, b) in S:
            indices = [pNames[r.getId()-1] for r in rebanadas if (a, b) in r.getPosicionesOcupadas()]
            problem.linear_constraints.add(
                lin_expr=[[indices, [1] * len(indices)]],
                senses=["L"],
                rhs=[1],
                names=[f"consPoint_{a}_{b}"]
            )
        
        # Restricción (3): Suma de alturas de rebanadas no supera altoBin
        problem.linear_constraints.add(
            lin_expr=[[pNames, [r.get_alto() for r in rebanadas]]],
            senses=["L"],
            rhs=[altoBin],
            names=["consH_Bin"]
        )
        
        # Restricción (4): Posición en y más altura no supera altoBin
        for r in rebanadas:
            problem.linear_constraints.add(
                lin_expr=[[ [yNames[r.getId()-1], pNames[r.getId()-1]], [1, r.get_alto()] ]],
                senses=["L"],
                rhs=[altoBin],
                names=[f"consH_{r.getId()-1}"]
            )
        
        # Restricción (5): No solapamiento vertical entre rebanadas
        for r in rebanadas:
            for r2 in rebanadas:
                if r != r2:
                    problem.linear_constraints.add(
                        lin_expr=[[ [yNames[r.getId()-1], pNames[r.getId()-1], yNames[r2.getId()-1], pNames[r2.getId()-1]], [1, altoBin, -1, altoBin] ]],
                        senses=["L"],
                        rhs=[2*altoBin-r.get_alto()],
                        names=[f"consV_{r.getId()-1}_{r2.getId()-1}"]
                    )
        
        # Función objetivo: maximizar la cantidad de ítems en rebanadas seleccionadas
        problem.objective.set_linear([(pNames[r.getId()-1], r.getTotalItems()) for r in rebanadas])
        
        return problem
    
    except CplexSolverError as exc:
        print(exc)




def solveMasterModel(model, queue, manualInterruption, relajarModelo, items, posXY_x, posXY_y):
    print("IN - Solve Master Model")
    # valores por default para enviar a paver
    modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1
    
    try:    
        # Desactivar la interrupción manual aquí
        initialTime = model.get_time()
        manualInterruption.value = False
        
        
        if(relajarModelo):
            print("Relajando modelo...")
            model.set_problem_type(cplex.Cplex.problem_type.LP)
        else:
            print("NO RELAJO MODELO - QUEDA COMO MILP")
            model.set_problem_type(cplex.Cplex.problem_type.MILP)
        
        # Resolver el modelo
        model.solve()
            
        objectiveValue = model.solution.get_objective_value()
        # Imprimir resultados
        print("Optimal value:", objectiveValue)
        dualValues=None
        if(relajarModelo):
            # Obtener valores duales
            dualValues=getDualValues(model)
            print("Dual values:", dualValues)    
            
            
        #imprimo valor que toman las variables
        for i, varName in enumerate(model.variables.get_names()):
            print(f"{varName} = {model.solution.get_values(varName)}")

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
        # Obtener la cantidad de restricciones
        
        print("OUT - Solve Master Model")
        return objectiveValue,dualValues
    
    except CplexSolverError as e:
        handleSolverError(e, queue,solverTime)
  


def getDualValuesOLD(model, I, posXY_x, posXY_y):
    
    print("Extrayendo valores duales...")
    # Inicializar diccionarios para cada componente de P_star
    P_star = {"pi": {}, "lambda": {}, "mu": {}}
    
    # Obtener los valores duales de las restricciones
    dualValues = model.solution.get_dual_values()
    print(f"todos los valores : {dualValues}")
    constraintNames=model.linear_constraints.get_names()
    # Recorrer las restricciones y mapear duales
    
    for _, (name, dualValue) in enumerate(zip(constraintNames, dualValues)):
        if name.startswith("consItem_"):
            # Restricciones relacionadas a ítems
            itemId = int(name.split("_")[1])  # Extraer el ID del ítem
            P_star["pi"][itemId] = dualValue
            print(f"Dual para ítem {itemId}: {dualValue}")
            
        elif name.startswith("consH_Bin"):
            # Restricciones relacionadas a posiciones horizontales
            # Extraer las coordenadas x, y del nombre de la restricción
            x, y = map(int, name.split("_")[1:])
            pos = (x, y)  # Crear la tupla de posición
            P_star["lambda"][pos] = dualValue
            print(f"Dual para posición horizontal {pos}: {dualValue}")
        
        elif name.startswith("consH_"):
            # Restricciones relacionadas a posiciones horizontales
            # Extraer las coordenadas x, y del nombre de la restricción
            x, y = map(int, name.split("_")[1:])
            pos = (x, y)  # Crear la tupla de posición
            P_star["lambda"][pos] = dualValue
            print(f"Dual para posición horizontal {pos}: {dualValue}")
        
        elif name.startswith("consV_"):
            # Restricciones relacionadas a posiciones verticales
            # Extraer las coordenadas x, y del nombre de la restricción
            x, y = map(int, name.split("_")[1:])
            pos = (x, y)  # Crear la tupla de posición
            P_star["mu"][pos] = dualValue
            print(f"Dual para posición vertical {pos}: {dualValue}")
            
        
    return P_star