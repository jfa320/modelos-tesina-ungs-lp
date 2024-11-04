import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
import multiprocessing
import time


from Position_generator import generate_positions

#Basado en la simplificacion del modelo 2 del overleaf (modelo discretizado en posiciones) - ver seccion 3.3 de ese documento para modelo completo

MODEL_NAME="Model2Pos1"

modelStatus="1"
solverStatus="1"
objectiveValue=0
solverTime=1

# Todos los casos siguientes mejoran con rotacion

# Caso 1:
# ITEMS_QUANTITY=6 # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 6 # W en el modelo
# BIN_HEIGHT = 4 # H en el modelo

# ITEM_WIDTH= 2 # w en el modelo
# ITEM_HEIGHT= 3 # h en el modelo


#Caso 2: 

# ITEMS_QUANTITY=6 # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 5 # W en el modelo
# BIN_HEIGHT = 5 # H en el modelo

# ITEM_WIDTH= 3 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

#Caso 3: 

# ITEMS_QUANTITY=8 # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 6 # W en el modelo
# BIN_HEIGHT = 6 # H en el modelo

# ITEM_WIDTH= 4 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

#Caso 4: 

# ITEMS_QUANTITY=5 # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 7 # W en el modelo
# BIN_HEIGHT = 3 # H en el modelo

# ITEM_WIDTH= 3 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

#Caso 5: 

# ITEMS_QUANTITY = 6  # constante N del modelo
# ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 
# BIN_WIDTH = 6  # W en el modelo
# BIN_HEIGHT = 3  # H en el modelo

# ITEM_WIDTH = 3  # w en el modelo
# ITEM_HEIGHT = 2  # h en el modelo


CASE_NAME="inst2"

ITEMS_QUANTITY= 10 # constante n del modelo
ITEMS = list(range(1, ITEMS_QUANTITY + 1)) # constante I del modelo
BIN_WIDTH = 6 # W en el modelo
BIN_HEIGHT = 4 # H en el modelo

ITEM_WIDTH= 2 # w en el modelo
ITEM_HEIGHT= 3 # h en el modelo


#SET_POS_X  constante X en el modelo
#SET_POS_Y  constante Y en el modelo

#SET_POS_X_I constante X_i en el modelo
#SET_POS_Y_I constante Y_i en el modelo

SET_POS_X, SET_POS_Y, SET_POS_X_I, SET_POS_Y_I = generate_positions(BIN_WIDTH, BIN_HEIGHT, ITEM_WIDTH, ITEM_HEIGHT)

QUANTITY_X_I=len(SET_POS_X_I) #constante Q(X_i) del modelo
QUANTITY_Y_I=len(SET_POS_Y_I) #constante Q(Y_i) del modelo

EXECUTION_TIME=2 # in seconds

def createAndSolveModel(queue,manualInterruption,maxTime):
     #valores por default para enviar a paver
    modelStatus="1"
    solverStatus="1"
    objectiveValue=0
    solverTime=1

    try:
        # Crear un modelo de CPLEX
        model= cplex.Cplex()

        initialTime=model.get_time()

        # Definir el problema como uno de maximización
        model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

        # Definir el limite tiempo de la ejecución en un minuto
        model.parameters.timelimit.set(maxTime)

        # Generar nombres de variables dinámicamente
        # f_i: indica si el objeto i esta ubicado dentro del bin con f_i = 1 si esta ubicado en el bin y f_i = 0 de lo contrario

        varsNames = [f"m_{i}" for i in range(1, ITEMS_QUANTITY + 1)]

        # Definir los coeficientes de la función objetivo (todos son 1)
        coeffs = [1.0] * ITEMS_QUANTITY  # Esto asigna 1 como coeficiente a cada variable

        # Añadir estas variables al problema
        model.variables.add(names=varsNames, obj=coeffs, types="B" * ITEMS_QUANTITY)

        # Definir variables adicionales 


        additionalVarsNames = []
        for x in SET_POS_X_I:
            for y in SET_POS_Y_I:
                    for i in ITEMS:
                        additionalVarsNames.append(f"n_{i},{x},{y}") # agrego variable n_{i,x,y}

        for x in SET_POS_X:
            for y in SET_POS_Y:            
                additionalVarsNames.append(f"r_{x},{y}") # agrego variable r_{x,y}

        # Añadir las variables adicionales al problema con coeficientes 0 en la función objetivo
        additionalCoeffObj = [0.0] * len(additionalVarsNames)
        model.variables.add(names=additionalVarsNames, obj=additionalCoeffObj, types="B" * len(additionalVarsNames))

        # Añadir la restricción r_{x,y} = sum_{i in N} sum_{x' in X_i, x-w+1 <= x' <= x} sum_{y' in Y_i, y-h+1 <= y' <= y} n_{i,x',y'} para cada (x, y) en X x Y
        for x in SET_POS_X:
            for y in SET_POS_Y:
                consCoeff = [1.0]  # Coeficiente para r_{x,y}
                consVars = [f"r_{x},{y}"]  # Variable r_{x,y}

                # Añadir los coeficientes y variables de sum_{i in N} sum_{x' in X_i, x-w+1 <= x' <= x} sum_{y' in Y_i, y-h+1 <= y' <= y} n_{i,x',y'}
                for i in ITEMS:
                    for xPrime in SET_POS_X_I:
                        if x - ITEM_WIDTH + 1 <= xPrime <= x:
                            for yPrime in SET_POS_Y_I:
                                if y - ITEM_HEIGHT + 1 <= yPrime <= y:
                                    consCoeff.append(-1.0)
                                    consVars.append(f"n_{i},{xPrime},{yPrime}")

                consRhs = 0.0  # Lado derecho de la restricción
                consSense = "E"  # "E" indica ==

                # Añadir la restricción al problema
                model.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                    senses=[consSense],
                    rhs=[consRhs]
                )

        # Añadir la restricción m_i <= sum_{x in X_i} sum_{y in Y_i} n_{i,x,y} para cada i en items - restriccion 2 del modelo
        for i in ITEMS:
            consCoeff = [1.0]  # Coeficiente para m_i
            consVars = [f"m_{i}"]  # Variable m_i

            # Añadir los coeficientes y variables de sum_{x in X_i} sum_{y in Y_i} n_{i,x,y}
            for x in SET_POS_X_I:
                for y in SET_POS_Y_I:
                    consCoeff.append(-1.0)
                    consVars.append(f"n_{i},{x},{y}")

            consRhs = 0.0  # Lado derecho de la restricción
            consSense = "L"  # "L" indica <=

            # Añadir la restricción al problema
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                senses=[consSense],
                rhs=[consRhs]
            )

        # Añadir la restricción sum_{x in X_i} sum_{y in Y_i} n_{i,x,y} <= Q(X_i) Q(Y_i) m_i para cada i en items
        for i in ITEMS:
            consCoeff = [-1.0]  # Coeficiente para m_i
            consVars = [f"m_{i}"]  # Variable m_i

            # Añadir los coeficientes y variables de sum_{x in X_i} sum_{y in Y_i} n_{i,x,y}
            for x in SET_POS_X_I:
                for y in SET_POS_Y_I:
                    consCoeff.append(1.0)
                    consVars.append(f"n_{i},{x},{y}")

            consRhs = 0.0  # Lado derecho de la restricción
            consSense = "L"  # "L" indica <=

            # Añadir la restricción al problema
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                senses=[consSense],
                rhs=[QUANTITY_X_I * QUANTITY_Y_I]  # Right Hand Side (RHS) es Q(X_i) * Q(Y_i)
            )

        # Desactivar la interrupción manual aquí
        manualInterruption.value = False

        # Resolver el modelo
        model.solve()

        # Obtener y mostrar los resultados
        solutionValues = model.solution.get_values()
        objectiveValue = model.solution.get_objective_value()

        print("Optimal value:", objectiveValue)
        print("Variables values:")
        for var_name, value in zip(varsNames, solutionValues):
            print(f"{var_name} = {value}")

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

    except CplexSolverError as e:
        if e.args[2] == 1217:  # Codigo de error para "No solution exists"
            print("\nNo solutions for the given model.")
            modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solverStatus="4" #el solver finalizo la ejecucion del modelo
        else:
            print("CPLEX Solver Error:", e)
            modelStatus="12" #valor en paver para marcar un error desconocido
            solverStatus="10" #el solver tuvo un error en la ejecucion

        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objectiveValue": objectiveValue,
            "solverTime": solverTime
        })

def executeWithTimeLimit(maxTime):
    global modelStatus, solverStatus, objectiveValue, solverTime 

    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    manualInterruption = multiprocessing.Value('b', True)

    # Crear el subproceso que correrá la función
    process = multiprocessing.Process(target=createAndSolveModel, args=(queue,manualInterruption,maxTime))

    # Iniciar el subproceso
    process.start()

    initialTime = time.time()

    # Monitorear la cola mientras el proceso está en ejecución
    while process.is_alive():

        if manualInterruption.value:
            # Si se excede el tiempo, terminamos el proceso
            if time.time() - initialTime > maxTime:
                print("Limit time reached. Aborting process.")
                modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
                solverStatus="4" #el solver finalizo la ejecucion del modelo
                solverTime=maxTime
                process.terminate()
                process.join()
                break

        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            print(message)
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            objectiveValue = message["objectiveValue"]
            solverTime = message["solverTime"]



if __name__ == '__main__':
    executeWithTimeLimit(EXECUTION_TIME)
    generator = TraceFileGenerator("output.trc")
    generator.write_trace_record(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)
