import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
import time

MODEL_NAME="Model5Master"
DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS = True


def calcularPosicionesOcupadas(posicion, ancho, alto):
        """
        Retorna todas las posiciones ocupadas por un ítem ubicado en `posicion` con dimensiones `ancho` x `alto`.
        """
        x, y = posicion
        posicionesOcupadas = set()
        for dx in range(ancho):
            for dy in range(alto):
                posicionesOcupadas.add((x + dx, y + dy))
        return posicionesOcupadas

def createMasterModel(maxTime,rebanadas,altoBin,anchoBin,altoItem,anchoItem,items,posXY_x,posXY_y):
    print("IN - Create Master Model")
    H = altoBin  # Alto del bin 
    R = rebanadas  # Lista de rebanadas disponibles
    # SOLO posiciones que están ocupadas por al menos una rebanada existente
    posiciones = set()

    for r in R:
        for item in r.getItems():
            if item.getPosicionX() is not None and item.getPosicionY() is not None:
                pos = item.getPosicion()
                posiciones.update(
                    calcularPosicionesOcupadas(
                        pos,
                        item.getAncho(),
                        item.getAlto()
                    )
                )

    TI= len(items)  # Total de ítems
    #C_r= se puede modelar usando el metodo rebanada.getTotalItems() - Cantidad de items en rebanadas
   
    try:
        # Crear instancia del problema
        model = cplex.Cplex()
        model.set_problem_type(cplex.Cplex.problem_type.MILP) 
        model.parameters.timelimit.set(maxTime)
        
        #Desactivo el presolve
        model.parameters.preprocessing.presolve.set(0)
        #Seteo el metodo simplex para resolver el modelo
        model.parameters.lpmethod.set(1)
        # Variables
        # Variables p_r (binarias)
        p_r_names = [f"p_{r.getId()}" for r in R]
        coeffs_p_r = [r.getTotalItems() for r in R] 
        addVariables(model, p_r_names,coeffs_p_r, model.variables.type.binary)
    
        model.objective.set_sense(model.objective.sense.maximize)

        added_constraints = set()
        
        
        # # ----------------------------------------------------
        # # Restricción de posiciones ocupadas por rebanadas
        # for (a, b) in posiciones:
        #     rebanadasQueOcupanPos = []  # Lista de rebanadas que ocupan (a, b)

        #     for r in R:
        #         posicionesOcupadas = set()
        #         rebanada = r 

        #         for item in rebanada.getItems():
        #             if item.getPosicionX() is not None and item.getPosicionY() is not None:
        #                 posicion = item.getPosicion()
        #                 posicionesOcupadas.update(calcularPosicionesOcupadas(posicion, item.getAncho(), item.getAlto()))
        #         if (a, b) in posicionesOcupadas:
        #             rebanadasQueOcupanPos.append(r)
            
        #     if rebanadasQueOcupanPos:
        #             # print(f"Agregando restricción para la posición ({a}, {b})")
        #             indexes = [p_r_names[r.getId()-1] for r in rebanadasQueOcupanPos]
        #             coeffs = [1] * len(rebanadasQueOcupanPos)
        #             consRhs=1.0
        #             consSense="L"
        #             addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consItem_{a}_{b}",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)
        
        # Precomputar ocupación de cada rebanada
        celulasPorReb = {}
        for r in R:
            ocupadas = set()
            for it in r.getItems():
                x,y = it.getPosicion()
                for dx in range(it.getAncho()):
                    for dy in range(it.getAlto()):
                        ocupadas.add((x+dx, y+dy))
            celulasPorReb[r.getId()] = ocupadas

        # Agregar restricción por cada par que se solape (r,s)
        for i, r1 in enumerate(R):
            for r2 in R[i+1:]:
                if celulasPorReb[r1.getId()] & celulasPorReb[r2.getId()]:
                    addConstraintSet(
                        model,
                        [1,1],
                        [f"p_{r1.getId()}", f"p_{r2.getId()}"],
                        1, "L",
                        added_constraints,
                        f"consNoSolape_{r1.getId()}_{r2.getId()}",
                        DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
                    )


        # # ----------------------------------------------------
        # Restricción de límite de ítems totales
        indexes = [p_r_names[r.getId()-1] for r in R]
        coeffs = [r.getTotalItems() for r in R]
        consRhs=TI
        consSense="L"
        addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consLimiteItems",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)
        
        print(f"Rebanadas usadas: {R}")
        print("OUT - Create Master Model")
        return model
    
    except CplexSolverError as e:
        handleSolverError(e)

# def createMasterModel(maxTime, rebanadas, altoBin, anchoBin, altoItem, anchoItem, items, posXY_x, posXY_y):
#     print("IN - Create Master Model")
#     H = altoBin                  # Alto del bin
#     W = anchoBin                 # Ancho del bin
#     R = rebanadas                # Lista de rebanadas disponibles
#     TI = len(items)              # Total de ítems

#     try:
#         # Crear instancia del problema
#         model = cplex.Cplex()
#         model.set_problem_type(cplex.Cplex.problem_type.MILP)
#         model.parameters.timelimit.set(maxTime)

#         # Desactivo el presolve
#         model.parameters.preprocessing.presolve.set(0)
#         # Seteo el método simplex para resolver el modelo
#         model.parameters.lpmethod.set(1)

#         # ----------------------------------------------------
#         # Variables p_r (binarias), una por rebanada
#         p_r_names = [f"p_{r.getId()}" for r in R]
#         coeffs_p_r = [r.getTotalItems() for r in R]   # C_r
#         addVariables(model, p_r_names, coeffs_p_r, model.variables.type.binary)

#         # Maximizar sum_r C_r * p_r
#         model.objective.set_sense(model.objective.sense.maximize)

#         added_constraints = set()

#         # ----------------------------------------------------
#         # Precomputar Φ(r): celdas ocupadas por cada rebanada r
#         # Φ(r) = { (x,y) : la rebanada r tiene algún ítem que cubre esa celda }
#         # Precomputar ocupación de cada rebanada
#         celulasPorReb = {}
#         for r in R:
#             ocupadas = set()
#             for it in r.getItems():
#                 # Extraer dimensiones y corregir si vienen invertidas
#                 w = it.getAncho()
#                 h = it.getAlto()
                
#                 if it.getRotado():
#                     w = it.getAlto()
#                     h = it.getAncho()
#                 else:
#                     w = it.getAncho()
#                     h = it.getAlto()

#                 x, y = it.getPosicion()

#                 for dx in range(w):
#                     for dy in range(h):
#                         ocupadas.add((x + dx, y + dy))

#             celulasPorReb[r.getId()] = ocupadas


#         # ----------------------------------------------------
#         # Restricciones por celda (a,b) ∈ P:
#         #   sum_{r : (a,b) ∈ Φ(r)} p_r ≤ 1
#         #
#         # Construyo P = TODAS las celdas del bin
#         P = [(x, y) for x in range(W) for y in range(H)]

#         for (a, b) in P:
#             rebanadasQueOcupanPos = []
#             for r in R:
#                 if (a, b) in celulasPorReb[r.getId()]:
#                     rebanadasQueOcupanPos.append(r)

#             if rebanadasQueOcupanPos:
#                 indexes = [f"p_{r.getId()}" for r in rebanadasQueOcupanPos]
#                 coeffs = [1.0] * len(rebanadasQueOcupanPos)
#                 consRhs = 1.0
#                 consSense = "L"
#                 nombreCons = f"consItem_{a}_{b}"

#                 addConstraintSet(
#                     model,
#                     coeffs,
#                     indexes,
#                     consRhs,
#                     consSense,
#                     added_constraints,
#                     nombreCons,
#                     DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
#                 )

#         # ----------------------------------------------------
#         # Restricción de límite de ítems totales:
#         #   sum_r C_r * p_r ≤ TI
#         indexes = [f"p_{r.getId()}" for r in R]
#         coeffs = [r.getTotalItems() for r in R]
#         consRhs = TI
#         consSense = "L"
#         addConstraintSet(
#             model,
#             coeffs,
#             indexes,
#             consRhs,
#             consSense,
#             added_constraints,
#             "consLimiteItems",
#             DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
#         )

#         print(f"Rebanadas usadas: {R}")
#         print("OUT - Create Master Model")
#         return model

#     except CplexSolverError as e:
#         handleSolverError(e)


def solveMasterModel(model, queue, manualInterruption, relajarModelo, items, posXY_x, posXY_y,initialTime):
    print("IN - Solve Master Model")
    # valores por default para enviar a paver
    modelStatus, solverStatus, objectiveValue, solverTime = "1", "1", 0, 1
    
    try:    
        # Desactivar la interrupción manual aquí
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
        
        
        
        if status == 105:  # CPLEX código 105 = Time limit exceeded
            print("The solver stopped because it reached the time limit.")
            modelStatus="2" #valor en paver para marcar un optimo local

        if(not relajarModelo):
            finalTime = time.time()
            solverTime=finalTime-initialTime
            solverTime=round(solverTime, 2)
            # Enviar resultados a través de la cola solo cuando el modelo no está relajado, es decir, cuando se va a resolver finalmente
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
        
def getDualValues(model):
    print("Extrayendo valores duales...")
    # Inicializar diccionarios para cada componente de P_star
    P_star = {"pi": {}}
    
    # Obtener los valores duales de las restricciones
    dualValues = model.solution.get_dual_values()
    print(f"todos los valores : {dualValues}")
    constraintNames=model.linear_constraints.get_names()
    # Recorrer las restricciones y mapear duales
    print("constraintNames: ",constraintNames)
    print("dualValues: ",dualValues)
    for _, (name, dualValue) in enumerate(zip(constraintNames, dualValues)):
        if name.startswith("consItem_"):
            # Restricciones relacionadas a ítems
            xPos = str(name.split("_")[1])  # Extraer el ID del ítem
            yPos = str(name.split("_")[2])  # Extraer el ID del ítem
            P_star["pi"][f"({xPos},{yPos})"] = dualValue
            print(f"Dual para ítem ({xPos},{yPos}): {dualValue}")
            
        
    return P_star

