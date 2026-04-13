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
    H = altoBin  
    R = rebanadas 
    posiciones = [(x, y) for x in range(anchoBin) for y in range(altoBin)]


    TI= len(items)  # Total de ítems
   
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
        print("======================================")
        print("COEFICIENTES FO MAESTRO")
        print("======================================")
        def resumirRebanada(rebanada):
            return sorted((item.getPosicionX(), item.getPosicionY(), item.getRotado()) for item in rebanada.getItems())

        for r, nombre, coef in zip(R, p_r_names, coeffs_p_r):
            print(f"{nombre} | id={r.getId()} | totalItems={r.getTotalItems()} | lenItems={len(r.getItems())} | resumen={resumirRebanada(r)}")
        
        addVariables(model, p_r_names, coeffs_p_r, model.variables.type.binary)


        p_r_by_id = {r.getId(): f"p_{r.getId()}" for r in R}
    
        model.objective.set_sense(model.objective.sense.maximize)

        added_constraints = set()
        
        
        # # ----------------------------------------------------
        # Precomputar celdas ocupadas por cada rebanada: Φ(r)
        celulasPorReb = {}
        for r in R:
            ocupadas = set()
            for it in r.getItems():
                if it.getPosicionX() is None or it.getPosicionY() is None:
                    continue
                x, y = it.getPosicion()
                for dx in range(it.getAncho()):
                    for dy in range(it.getAlto()):
                        ocupadas.add((x + dx, y + dy))
            celulasPorReb[r.getId()] = ocupadas


        # Restricción de posiciones ocupadas por rebanadas
        for (a, b) in posiciones:
            rebanadasQueOcupanPos = [r for r in R if (a, b) in celulasPorReb[r.getId()]]
            if rebanadasQueOcupanPos:
                indexes = [f"p_{r.getId()}" for r in rebanadasQueOcupanPos]
                coeffs = [1.0] * len(rebanadasQueOcupanPos)
                addConstraintSet(
                    model,
                    coeffs,
                    indexes,
                    1.0,
                    "L",
                    added_constraints,
                    f"consItem_{a}_{b}",
                    DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
                )

        # # ----------------------------------------------------
       
        indexes = [p_r_by_id[r.getId()] for r in R]

        coeffs = [r.getTotalItems() for r in R]
        consRhs=TI
        consSense="L"
        addConstraintSet(model,coeffs,indexes,consRhs,consSense,added_constraints,f"consLimiteItems",DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS)
        
        # print(f"Rebanadas usadas: {R}")
        print("OUT - Create Master Model")
        return model
    
    except CplexSolverError:
        raise


def solveMasterModel(model, queue, manualInterruption, relajarModelo, initialTime):
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
        variablesActivas = []
        if(relajarModelo):
            # Obtener valores duales
            dualValues=getDualValues(model)
            # print("Dual values:", dualValues)    
            
            
        # imprimo valor que toman las variables
        for i, varName in enumerate(model.variables.get_names()):
            valorVariable = model.solution.get_values(varName)
            if valorVariable > 0.5:
                variablesActivas.append(varName)

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
        return objectiveValue, dualValues, variablesActivas
    
    except CplexSolverError as e:
        handleSolverError(e, queue,solverTime)
        
def getDualValues(model):
    print("Extrayendo valores duales...")

    P_star = {"pi": {}}

    dualValues = model.solution.get_dual_values()
    constraintNames = model.linear_constraints.get_names()

    for name, dualValue in zip(constraintNames, dualValues):
        if name.startswith("consItem_"):
            # nombre: consItem_a_b
            _, a, b = name.split("_")
            P_star["pi"][f"({a},{b})"] = dualValue

    return P_star


