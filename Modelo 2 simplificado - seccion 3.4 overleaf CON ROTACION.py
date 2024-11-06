import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
import multiprocessing
import time

from Position_generator import generate_positions

NOMBRE_MODELO="Model2Pos1"

modelStatus="1"
solverStatus="1"
objectiveValue=0
solverTime=1

# Constantes del problema

# Caso 5: 

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


# Generación de posiciones factibles para ítems y sus versiones rotadas
SET_POS_X, SET_POS_Y, SET_POS_X_I, SET_POS_Y_I = generate_positions(BIN_WIDTH, BIN_HEIGHT, ITEM_WIDTH, ITEM_HEIGHT)
SET_POS_X_I_ROT = [x for x in range(BIN_WIDTH) if x <= BIN_WIDTH - ITEM_HEIGHT]
SET_POS_Y_I_ROT = [y for y in range(BIN_HEIGHT) if y <= BIN_HEIGHT - ITEM_WIDTH]

QUANTITY_X_I = len(SET_POS_X_I)
QUANTITY_Y_I = len(SET_POS_Y_I)
QUANTITY_X_I_ROT = len(SET_POS_X_I_ROT)
QUANTITY_Y_I_ROT = len(SET_POS_Y_I_ROT)

EXECUTION_TIME=2 # in seconds

def createAndSolveModel(queue,manualInterruption,maxTime):
    #valores por default para enviar a paver
    modelStatus="1"
    solverStatus="1"
    objectiveValue=0
    solverTime=1

    try:
        # Crear el modelo CPLEX
        model = cplex.Cplex()
        
        model.set_results_stream(None) # deshabilito log de CPLEX de la info paso a paso
        
        initialTime=model.get_time()

        model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

        # Definir el limite tiempo de la ejecución en un minuto
        model.parameters.timelimit.set(maxTime)

        # Variables para indicar si el ítem o su versión rotada están en el bin
        varsNames = [f"m_{i}" for i in ITEMS] + [f"m_rot_{i}" for i in ITEMS]
        coeffs = [1.0] * ITEMS_QUANTITY * 2
        model.variables.add(names=varsNames, obj=coeffs, types="B" * len(varsNames))

        # Variables de posición para la versión original y rotada de los ítems
        positionVarsNames = []
        for i in ITEMS:
            for x in SET_POS_X_I:
                for y in SET_POS_Y_I:
                    positionVarsNames.append(f"n_{i},{x},{y}")
            for xRot in SET_POS_X_I_ROT:
                for yRot in SET_POS_Y_I_ROT:
                    positionVarsNames.append(f"n_rot_{i},{xRot},{yRot}")

        posCoeffs = [0.0] * len(positionVarsNames)
        model.variables.add(names=positionVarsNames, obj=posCoeffs, types="B" * len(positionVarsNames))

        # Variables para las posiciones libres (r_x,y)
        rVarsNames = [f"r_{x},{y}" for x in SET_POS_X for y in SET_POS_Y]
        model.variables.add(names=rVarsNames, obj=[0.0] * len(rVarsNames), types="B" * len(rVarsNames))

        # Restricción 1: Evita solapamiento de ítems en una posición (x,y)
        for x in SET_POS_X:
            for y in SET_POS_Y:
                consCoeff = [1.0]  # Coeficiente de r_{x,y}
                consVars = [f"r_{x},{y}"]

                for i in ITEMS:
                    for xPrime in SET_POS_X_I:
                        if x - ITEM_WIDTH + 1 <= xPrime <= x:
                            for yPrime in SET_POS_Y_I:
                                if y - ITEM_HEIGHT + 1 <= yPrime <= y:
                                    consCoeff.append(-1.0)
                                    consVars.append(f"n_{i},{xPrime},{yPrime}")

                    for xPrimeRot in SET_POS_X_I_ROT:
                        if x - ITEM_HEIGHT + 1 <= xPrimeRot <= x:
                            for yPrimeRot in SET_POS_Y_I_ROT:
                                if y - ITEM_WIDTH + 1 <= yPrimeRot <= y:
                                    consCoeff.append(-1.0)
                                    consVars.append(f"n_rot_{i},{xPrimeRot},{yPrimeRot}")

                model.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                    senses=["E"], rhs=[0.0]
                )


        for i in ITEMS:
            consCoeff = [-1.0]  # Coeficiente para m_i
            consVars = [f"m_{i}"]  # Variable m_i que indica si el ítem no rotado está en el bin

            # Sumamos todas las posiciones no rotadas posibles donde el ítem puede estar
            for x in SET_POS_X_I:
                for y in SET_POS_Y_I:
                    consCoeff.append(1.0)
                    consVars.append(f"n_{i},{x},{y}")

            # La restricción asegura que m_i sea igual a la suma de posiciones ocupadas
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                senses=["E"], rhs=[0.0]
            )

        # Restricción para ítems rotados: m_rot_i = suma de las posiciones rotadas donde está el ítem i
        for i in ITEMS:
            consCoeffRot = [-1.0]  # Coeficiente para m_rot_i
            consVarsRot = [f"m_rot_{i}"]  # Variable m_rot_i que indica si el ítem rotado está en el bin

            # Sumamos todas las posiciones rotadas posibles donde el ítem puede estar
            for xRot in SET_POS_X_I_ROT:
                for yRot in SET_POS_Y_I_ROT:
                    consCoeffRot.append(1.0)
                    consVarsRot.append(f"n_rot_{i},{xRot},{yRot}")

            # La restricción asegura que m_rot_i sea igual a la suma de posiciones ocupadas
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consVarsRot, consCoeffRot)],
                senses=["E"], rhs=[0.0]
            )

        # Restricción 3: suma de posiciones <= Q(X_i)*Q(Y_i) * m_i
        for i in ITEMS:
            consCoeff = [-1.0]  # Coeficiente para m_i
            consVars = [f"m_{i}"]

            for x in SET_POS_X_I:
                for y in SET_POS_Y_I:
                    consCoeff.append(1.0)
                    consVars.append(f"n_{i},{x},{y}")

            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consVars, consCoeff)],
                senses=["L"], rhs=[QUANTITY_X_I * QUANTITY_Y_I]
            )

            consCoeffRot = [-1.0]  # Coeficiente para m_rot_i
            consVarsRot = [f"m_rot_{i}"]

            for xRot in SET_POS_X_I_ROT:
                for yRot in SET_POS_Y_I_ROT:
                    consCoeffRot.append(1.0)
                    consVarsRot.append(f"n_rot_{i},{xRot},{yRot}")

            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(consVarsRot, consCoeffRot)],
                senses=["L"], rhs=[QUANTITY_X_I_ROT * QUANTITY_Y_I_ROT]
            )

        # Restricción 4: m_i + m_rot_i <= 1
        for i in ITEMS:
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair([f"m_{i}", f"m_rot_{i}"], [1.0, 1.0])],
                senses=["L"], rhs=[1.0]
            )

        # Desactivar la interrupción manual aquí
        manualInterruption.value = False

        # Resolver el modelo
        model.solve()

        # Obtener resultados
        solution_values = model.solution.get_values()
        objectiveValue = model.solution.get_objective_value()

        print("Optimal value:", objectiveValue)
        
        #aca imprimo el valor que toman las variables
        # for var_name, value in zip(varsNames, solution_values):
        #     print(f"{var_name} = {value}")
        
        status = model.solution.get_status()
        tiempoFinal = model.get_time()
        solverTime=tiempoFinal-initialTime
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
    generator.write_trace_record(CASE_NAME, NOMBRE_MODELO, modelStatus, solverStatus, objectiveValue, solverTime)

