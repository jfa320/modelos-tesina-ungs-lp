import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator


from Objetos.Rebanada import Rebanada
from Objetos.Item import Item

from Position_generator import *

NOMBRE_MODELO="Model4Maestro"

modelStatus="1"
solverStatus="1"
objectiveValue=0
solverTime=1

# Constantes del problema

# Caso 5: 

# ITEMS_QUANTITY = 6  # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 6  # W en el modelo
# sliceHeight = 3  # H en el modelo

# ITEM_WIDTH = 3  # w en el modelo
# ITEM_HEIGHT = 2  # h en el modelo


CASE_NAME="inst2"

BIN_WIDTH = 6 # W en el modelo
BIN_HEIGHT=4
ITEM_WIDTH= 2 # w en el modelo
ITEM_HEIGHT= 3 # h en el modelo

slices=[] #TODO CARGAR ARRAY CON LO DEL ESCLAVO
sliceHeight = [] # H_r en el modelo #TODO CARGAR ARRAY
SET_POS_Y= generate_positions_modelo_maestro(BIN_HEIGHT)
ITEMS_QUANTITY= 10 
ITEMS = list(range(1, ITEMS_QUANTITY + 1)) # constante I del modelo

slicesQuantity=len(slices)

REL_POS_ITEM_Y=[] #TODO PENSAR COMO CARGARLO, QUIZAS CON EL NUMERO DE ITEM Y SU POSICION
ITEMS_HEIGHT=[] #TODO CARGAR ARRAY CON LO QUE VENGA DEL ESCLAVO


EXECUTION_TIME=2 # in seconds

def createAndSolveMasterModel(manualInterruption,maxTime,initialSlice):
    #valores por default para enviar a paver
    modelStatus="1"
    solverStatus="1"
    objectiveValue=0
    solverTime=1
    slices.append(initialSlice)
    slicesQuantity=len(slices)
    
    try:
        # Crear el modelo CPLEX
        model = cplex.Cplex()
        
        initialTime=model.get_time()

        model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

        # Definir el limite tiempo de la ejecución en un minuto
        model.parameters.timelimit.set(maxTime)

        # Variables para indicar si uso o no la rebanada r en el bin (para la FO)
        # Acá defino la FUNCION OBJETIVO
        pRName  = [f"p_{r}" for r in range(slicesQuantity)]
        coeffs = [1.0] * slicesQuantity
        model.variables.add(names=pRName, obj=coeffs, lb=[0.0] * slicesQuantity, ub=[1.0] * slicesQuantity, types="C" * slicesQuantity) #Relajo la variable binaria a continua para buscar solucion dual


        # Variables para indicar si la rebanada r ocupa la posición p (s_{rp})
        sRPNames = [f"s_{r},{p}" for r in range(slicesQuantity) for p in SET_POS_Y]
        sRPCoeffs = [0.0]* (len(slices) * len(SET_POS_Y)) 
        model.variables.add(names=sRPNames, obj=sRPCoeffs, lb=[0.0] * len(sRPNames), ub=[1.0] * len(sRPNames), types="C" * len(sRPNames)) #Relajo la variable binaria a continua para buscar solucion dual

        # Variables para indicar la ubicacion y donde se ubica una rebanada r
        yRNames = [f"y_{r}" for r in range(slicesQuantity)]
        model.variables.add(names=yRNames, obj=[0.0] * len(yRNames), types="C" * len(yRNames), lb=[0.0] * len(yRNames))

        # Variables para determinar si una rebanada i se ubica arriba de otra rebanada j
        zIJNames = [f"z_{i},{j}" for i in range(slicesQuantity) for j in range(slicesQuantity) if i != j]
        model.variables.add(names=zIJNames, obj=[0.0] * len(zIJNames), lb=[0.0] * len(zIJNames), ub=[1.0] * len(zIJNames), types="C" * len(zIJNames)) #Relajo la variable binaria a continua para buscar solucion dual

        # Variables w_{i,r} (indica si el ítem i está en la rebanada r)
        wIRNames = [f"w_{i},{r}" for i in ITEMS for r in range(slicesQuantity)]
        model.variables.add(names=wIRNames, obj=[0.0] * len(wIRNames), lb=[0.0] * len(wIRNames), ub=[1.0] * len(wIRNames), types="C" * len(wIRNames)) #Relajo la variable binaria a continua para buscar solucion dual
     
        # Variables y_{i,r} indica la posicion absoluta en el eje y del item i de la rebanada r en el bin
        yIRNames = [f"y_{i},{r}" for i in ITEMS for r in range(slicesQuantity)]
        model.variables.add(names=yIRNames, obj=[0.0] * len(yIRNames), types="C" * len(yIRNames), lb=[0.0] * len(yIRNames))

        
        # Restricción (1): Cada ítem se ubica solo en una rebanada
        for i in ITEMS:
            varW_ir = [f"w_{i},{r}" for r in range(slicesQuantity)]
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=varW_ir, val=[1] * len(varW_ir))],
                senses=["L"], rhs=[1]
            )
        
        # Restricción (2): Un ítem pertenece a una rebanada solo si la rebanada es seleccionada
        for i in ITEMS:
            for r in range(slicesQuantity):
                model.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=[f"w_{i},{r}", f"p_{r}"], val=[1, -1])],
                    senses=["L"], rhs=[0]
                )

        # Restricción (3): La suma de las alturas de las slices seleccionadas no excede la altura del bin
        model.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=pRName, val=[sliceHeight[r] for r in range(slicesQuantity)])],
            senses=["L"], rhs=[BIN_HEIGHT]
        )

        # Restricción (4): Si se elige una rebanada, debe ocupar una sola posición en el bin
        for r in range(slicesQuantity):
            varS_rp = [f"s_{r},{p}" for p in SET_POS_Y]
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=varS_rp + [f"p_{r}"], val=[1] * len(varS_rp) + [-1])],
                senses=["L"], rhs=[0]
            )

        # Restricciones (5) y (6): Las slices no deben solaparse verticalmente
        for r in range(slicesQuantity):
            for rp in range(slicesQuantity):
                if r != rp:
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=[f"y_{r}", f"y_{rp}", f"z_{rp},{r}"], val=[1, -1, BIN_HEIGHT])],
                        senses=["L"], rhs=[BIN_HEIGHT] - sliceHeight[r]
                    )
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=[f"y_{rp}", f"y_{r}", f"z_{r},{rp}"], val=[1, -1, BIN_HEIGHT])],
                        senses=["L"], rhs=[BIN_HEIGHT] - sliceHeight[rp]
                    )

        # Restricción (7): Cada par de slices deben estar en una relación de arriba o abajo, no ambas
        for r in range(slicesQuantity):
            for rp in range(slicesQuantity):
                if r != rp:
                    model.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=[f"z_{r},{rp}", f"z_{rp},{r}"], val=[1, 1])],
                        senses=["E"], rhs=[1]
                    )

        # Restricción (8): Establece la posicion absoluta en el bin de cada item de una rebanada
        for i in ITEMS:
            for r in range(slicesQuantity):
                model.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=[f"y_{i},{r}", f"y_{r}"], val=[1, -1])],
                    senses=["E"], rhs=[REL_POS_ITEM_Y[i,r]] #TODO REVISAR COMO ACCEDER A ESTE ARRAY (quizas usar diccionarios)
                )

        # Restricción (9) y (10): Asegura que los items de las slices no se solapen entre sí
        for i in ITEMS:
            for j in ITEMS:
                if i != j:  # Solo si i y j son distintos
                    for r in range(slicesQuantity):
                        for rPrime in range(slicesQuantity):
                            if r != rPrime:  # Solo si r y r' son distintos
                                
                                # Restricción (9): y_{ir} + h_i <= y_{jr'} + H * z_{r,r'}
                                constraint_9 = cplex.SparsePair(
                                    ind=[f"y_{i},{r}", f"y_{j},{rPrime}", f"z_{r},{rPrime}"],
                                    val=[1.0, -1.0, -BIN_HEIGHT]
                                )
                                model.linear_constraints.add(
                                    lin_expr=[constraint_9],
                                    senses=["L"],  
                                    rhs=[-ITEMS_HEIGHT[i]]  #TODO: VER SI ACCEDO ASI AL ALTO
                                )
                                
                                # Restricción (10): y_{jr'} + h_j <= y_{ir} + H * (1 - z_{r,r'})
                                # Esto es equivalente a y_{jr'} + h_j <= y_{ir} + H - H * z_{r,r'}
                                cons10 = cplex.SparsePair(
                                    ind=[f"y_{j},{rPrime}", f"y_{i},{r}", f"z_{r},{rPrime}"],
                                    val=[1.0, -1.0, BIN_HEIGHT]
                                )
                                model.linear_constraints.add(
                                    lin_expr=[cons10],
                                    senses=["L"],  
                                    rhs=[BIN_HEIGHT - ITEMS_HEIGHT[j]]  #TODO: VER SI ACCEDO ASI AL ALTO
                                )
        
        # Desactivar la interrupción manual aquí
        manualInterruption.value = False

        # Resolver el modelo
        model.solve()

        # Obtener resultados
        solutionValues = model.solution.get_values()
        objectiveValue = model.solution.get_objective_value()
        dualValues = model.solution.get_dual_values() #aca obtengo solucion dual
        
        print("Optimal value:", objectiveValue)
        for varName, value in zip(pRName, solutionValues):
            print(f"{varName} = {value}")
            
        dualSol = {}
        
        for i, dual in enumerate(dualValues):
            print(f"Constraint_ {i}: Dual Value = {dual}")
            dualSol[f"Constraint_{i}"] = dual
        
        status = model.solution.get_status()
        finalTime = model.get_time()
        solverTime=finalTime-initialTime
        solverTime=round(solverTime, 2)
        
        if status == 105:  # CPLEX código 105 = Time limit exceeded
            print("The solver stopped because it reached the time limit.")
            modelStatus="2" #valor en paver para marcar un optimo local

        return dualSol

    except CplexSolverError as e:
        if e.args[2] == 1217:  # Codigo de error para "No solution exists"
            print("\nNo solutions for the given model.")
            modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solverStatus="4" #el solver finalizo la ejecucion del modelo
        else:
            print("CPLEX Solver Error:", e)
            modelStatus="12" #valor en paver para marcar un error desconocido
            solverStatus="10" #el solver tuvo un error en la ejecucion


