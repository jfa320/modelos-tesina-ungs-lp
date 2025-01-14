import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *

MODEL_NAME="Model5Master"


def createMasterModel(maxTime,rebanadas,altoBin,anchoBin,altoItem,anchoItem,items,posXY_x,posXY_y):
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
        model.set_problem_type(cplex.Cplex.problem_type.LP) 

        model.parameters.timelimit.set(maxTime)

        # Variables
        # Variables p_r (binarias)
        p_r_names = [f"p_{r.getId()}" for r in R]
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
            indexes = [p_r_names[r.getId()-1] for r in R if r.contieneItem(i)]
            coeffs = [1] * len(indexes)
            consRhs=1.0
            consSense="L"
            addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consItem_{i.getId()}")

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
                    addConstraintSet(model, coeff, vars, rhs=1, sense="L",added_constraints=added_constraints)
                
                # Restricción (3): No solapamiento vertical
                if V_ab_positions:
                    coeff = [1 if (x, y) in R_r_xy[r.getId()-1] else 0 for (x, y) in V_ab_positions]
                    vars = [f"p_{r.getId()}"] * len(V_ab_positions)
                    addConstraintSet(model, coeff, vars, rhs=1, sense="L",added_constraints=added_constraints)
                
                # Restricción (4): No solapamiento en intersección
                overlap_positions = set(H_ab_positions) & set(V_ab_positions)
                if overlap_positions:
                    coeff = [1 if (x, y) in R_r_xy[r.getId()-1] else 0 for (x, y) in overlap_positions]
                    vars = [f"p_{r.getId()}"] * len(overlap_positions)
                    addConstraintSet(model, coeff, vars, rhs=1, sense="L",added_constraints=added_constraints)
        
        # Generación del conjunto de posiciones válidas
        posicionesValidas = set()  # Usamos un conjunto para evitar duplicados

        # Unimos todas las posiciones de H_a,b y V_a,b para cada (a, b)
        for (a, b) in H_ab.keys():  # Iteramos sobre todas las claves de H_a,b
            posicionesValidas.update(H_ab[(a, b)])  # Agregamos las posiciones horizontales
        for (a, b) in V_ab.keys():  # Iteramos sobre todas las claves de V_a,b
            posicionesValidas.update(V_ab[(a, b)])  # Agregamos las posiciones verticales

        # Convertimos el conjunto a una lista si se necesita orden específico
        posicionesValidas = list(posicionesValidas)
        print("pos: ",posicionesValidas)
        print("aca: ",R_r_xy)
        # Generación de la restricción en CPLEX
        for (a, b) in posicionesValidas:  # Iteramos sobre las posiciones válidas
            restriccion = cplex.SparsePair()  # Creamos una nueva restricción
            restriccion.ind = []  # Índices de las variables que participan en la restricción
            restriccion.val = []  # Coeficientes correspondientes a esas variables

            for r in R:  # Iteramos sobre cada rebanada
                # Verificamos posiciones en H_{a,b}
                for (x, y) in H_ab.get((a, b), []):  # Posiciones horizontales asociadas a (a, b)
                    if (x, y) in R_r_xy[r.getId() - 1]:  # Si (x, y) está ocupado por la rebanada r
                        restriccion.ind.append(p_r_names[r.getId()-1])  # Agregamos la variable p_r[r]
                        restriccion.val.append(1)  # Coeficiente de la variable es 1 indicando que esa pos existe en r

                # Verificamos posiciones en V_{a,b}
                for (x, y) in V_ab.get((a, b), []):  # Posiciones verticales asociadas a (a, b)
                    if (x, y) in R_r_xy[r.getId() - 1]:  # Si (x, y) está ocupado por la rebanada r
                        restriccion.ind.append(p_r_names[r.getId()-1])  # Agregamos la variable p_r[r]
                        restriccion.val.append(1)  # Coeficiente de la variable es 1 indicando que esa pos existe en r
            
            addConstraintSet(model, restriccion.val, restriccion.ind, rhs=1, sense="L",added_constraints=added_constraints)
        
        print("OUT - Create Master Model")
        
        return model
    
    except CplexSolverError as e:
        handleSolverError(e)


def solveMasterModel(model, queue, manualInterruption, items):
    print("IN - Solve Master Model")
    # valores por default para enviar a paver
    modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1
    
    # Obtener la cantidad de restricciones
    cantidad_restricciones = model.linear_constraints.get_num()

    # Imprimir el resultado
    print(f"Cantidad de restricciones: {cantidad_restricciones}")

    try:    
        # Desactivar la interrupción manual aquí
        initialTime = model.get_time()
        manualInterruption.value = False
        # relajo el modelo
        model.set_problem_type(cplex.Cplex.problem_type.LP)
        # Resolver el modelo
        model.solve()
        objectiveValue = model.solution.get_objective_value()
        # Obtener los valores duales de las restricciones
        dualValues = model.solution.get_dual_values()

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
        
        print("OUT - Solve Master Model")
        return objectiveValue, dualValues
    
    except CplexSolverError as e:
        handleSolverError(e, queue,solverTime)
