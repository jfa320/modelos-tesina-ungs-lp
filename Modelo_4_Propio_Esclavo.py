import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
from Objetos.Rebanada import Rebanada
from Objetos.Item import Item
import multiprocessing
import time

from Position_generator import *

NOMBRE_MODELO="Model4Esclavo"

modelStatus="1"
solverStatus="1"
objective_value=0
solverTime=1

# Constantes del problema

# Caso 5: 

# CANTIDAD_ITEMS = 6  # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 6  # W en el modelo
# ALTO_REBANADA = 3  # H en el modelo

# ANCHO_OBJETO = 3  # w en el modelo
# ALTO_OBJETO = 2  # h en el modelo


NOMBRE_CASO="inst2"

CANTIDAD_ITEMS= 10 # constante n del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo
ANCHO_BIN = 6 # W en el modelo
ALTO_REBANADA = 4 # H en el modelo

ANCHO_OBJETO= 2 # w en el modelo
ALTO_OBJETO= 3 # h en el modelo

S_star=[] #TODO Definir como le llega del maestro

# Generación de posiciones factibles para ítems y sus versiones rotadas
CONJUNTO_POS_X, CONJUNTO_POS_Y, CONJUNTO_POS_X_I, CONJUNTO_POS_Y_I = generate_positions_no_height_limit(ANCHO_BIN, ALTO_REBANADA, ANCHO_OBJETO, ALTO_OBJETO)
CONJUNTO_POS_X_I_ROT = [x for x in range(ANCHO_BIN) if x <= ANCHO_BIN - ALTO_OBJETO]
CONJUNTO_POS_Y_I_ROT = [y for y in range(ALTO_REBANADA) if y <= ALTO_REBANADA]

CANT_X_I = len(CONJUNTO_POS_X_I)
CANT_Y_I = len(CONJUNTO_POS_Y_I)
CANT_X_I_ROT = len(CONJUNTO_POS_X_I_ROT)
CANT_Y_I_ROT = len(CONJUNTO_POS_Y_I_ROT)

EXECUTION_TIME=2 # in seconds

def createAndSolveSlaveModel(queue,interrupcion_manual,tiempoMaximo):
    #valores por default para enviar a paver
    modelStatus="1"
    solverStatus="1"
    objective_value=0
    solverTime=1

    try:
        # Crear el modelo CPLEX
        modelo = cplex.Cplex()
        
        tiempoInicial=modelo.get_time()

        modelo.set_problem_type(cplex.Cplex.problem_type.LP)
        modelo.objective.set_sense(modelo.objective.sense.maximize)

        # Definir el limite tiempo de la ejecución en un minuto
        modelo.parameters.timelimit.set(tiempoMaximo)

        # Variables para indicar si el ítem o su versión rotada están en el bin (para la FO)
        nombreVariables = [f"m_{i}" for i in ITEMS] + [f"m_rot_{i}" for i in ITEMS] 
        coeficientes = [S_star[i-1] for i in ITEMS] + [S_star[i-1] for i in ITEMS] #TODO: Revisar en base a respuesta de Marcelo y ver como sacar ese dato del maestro
        modelo.variables.add(names=nombreVariables, obj=coeficientes, types="B" * len(nombreVariables))


        # Variables de posición para la versión original y rotada de los ítems
        nombreVariablesPosiciones = []
        for i in ITEMS:
            for x in CONJUNTO_POS_X_I:
                for y in CONJUNTO_POS_Y_I:
                    nombreVariablesPosiciones.append(f"n_{i},{x},{y}")
            for x_rot in CONJUNTO_POS_X_I_ROT:
                for y_rot in CONJUNTO_POS_Y_I_ROT:
                    nombreVariablesPosiciones.append(f"n_rot_{i},{x_rot},{y_rot}")

        coeficientesPos = [0.0] * len(nombreVariablesPosiciones)
        modelo.variables.add(names=nombreVariablesPosiciones, obj=coeficientesPos, types="B" * len(nombreVariablesPosiciones))

        # Variables para las posiciones libres (r_x,y)
        nombreVariablesR = [f"r_{x},{y}" for x in CONJUNTO_POS_X for y in CONJUNTO_POS_Y]
        modelo.variables.add(names=nombreVariablesR, obj=[0.0] * len(nombreVariablesR), types="B" * len(nombreVariablesR))

        # Restricción 1: Evita solapamiento de ítems en una posición (x,y)
        for x in CONJUNTO_POS_X:
            for y in CONJUNTO_POS_Y:
                coef_restriccion = [1.0]  # Coeficiente de r_{x,y}
                var_restriccion = [f"r_{x},{y}"]

                for i in ITEMS:
                    for x_prima in CONJUNTO_POS_X_I:
                        if x - ANCHO_OBJETO + 1 <= x_prima <= x:
                            for y_prima in CONJUNTO_POS_Y_I:
                                if y - ALTO_OBJETO + 1 <= y_prima <= y:
                                    coef_restriccion.append(-1.0)
                                    var_restriccion.append(f"n_{i},{x_prima},{y_prima}")

                    for x_prima_rot in CONJUNTO_POS_X_I_ROT:
                        if x - ALTO_OBJETO + 1 <= x_prima_rot <= x:
                            for y_prima_rot in CONJUNTO_POS_Y_I_ROT:
                                if y - ANCHO_OBJETO + 1 <= y_prima_rot <= y:
                                    coef_restriccion.append(-1.0)
                                    var_restriccion.append(f"n_rot_{i},{x_prima_rot},{y_prima_rot}")

                modelo.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(var_restriccion, coef_restriccion)],
                    senses=["E"], rhs=[0.0]
                )


        for i in ITEMS:
            coef_restriccion = [-1.0]  # Coeficiente para m_i
            var_restriccion = [f"m_{i}"]  # Variable m_i que indica si el ítem no rotado está en el bin

            # Sumamos todas las posiciones no rotadas posibles donde el ítem puede estar
            for x in CONJUNTO_POS_X_I:
                for y in CONJUNTO_POS_Y_I:
                    coef_restriccion.append(1.0)
                    var_restriccion.append(f"n_{i},{x},{y}")

            # La restricción asegura que m_i sea igual a la suma de posiciones ocupadas
            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(var_restriccion, coef_restriccion)],
                senses=["L"], rhs=[0.0]
            )

        # Restricción para ítems rotados: m_rot_i = suma de las posiciones rotadas donde está el ítem i
        for i in ITEMS:
            coef_restriccion_rot = [-1.0]  # Coeficiente para m_rot_i
            var_restriccion_rot = [f"m_rot_{i}"]  # Variable m_rot_i que indica si el ítem rotado está en el bin

            # Sumamos todas las posiciones rotadas posibles donde el ítem puede estar
            for x_rot in CONJUNTO_POS_X_I_ROT:
                for y_rot in CONJUNTO_POS_Y_I_ROT:
                    coef_restriccion_rot.append(1.0)
                    var_restriccion_rot.append(f"n_rot_{i},{x_rot},{y_rot}")

            # La restricción asegura que m_rot_i sea igual a la suma de posiciones ocupadas
            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(var_restriccion_rot, coef_restriccion_rot)],
                senses=["L"], rhs=[0.0]
            )

        # Restricción : suma de posiciones <= Q(X_i)*Q(Y_i) * m_i 
        for i in ITEMS:
            coef_restriccion = [-1.0]  # Coeficiente para m_i
            var_restriccion = [f"m_{i}"]

            for x in CONJUNTO_POS_X_I:
                for y in CONJUNTO_POS_Y_I:
                    coef_restriccion.append(1.0)
                    var_restriccion.append(f"n_{i},{x},{y}")

            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(var_restriccion, coef_restriccion)],
                senses=["L"], rhs=[CANT_X_I * CANT_Y_I]
            )

            coef_restriccion_rot = [-1.0]  # Coeficiente para m_rot_i
            var_restriccion_rot = [f"m_rot_{i}"]

            for x_rot in CONJUNTO_POS_X_I_ROT:
                for y_rot in CONJUNTO_POS_Y_I_ROT:
                    coef_restriccion_rot.append(1.0)
                    var_restriccion_rot.append(f"n_rot_{i},{x_rot},{y_rot}")

            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(var_restriccion_rot, coef_restriccion_rot)],
                senses=["L"], rhs=[CANT_X_I_ROT * CANT_Y_I_ROT]
            )

        # Restricción 4: m_i + m_rot_i <= 1 
        for i in ITEMS:
            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair([f"m_{i}", f"m_rot_{i}"], [1.0, 1.0])],
                senses=["L"], rhs=[1.0]
            )

        # Desactivar la interrupción manual aquí
        interrupcion_manual.value = False

        # Resolver el modelo
        modelo.solve()

        # Obtener resultados
        solution_values = modelo.solution.get_values()
        objective_value = modelo.solution.get_objective_value()
        
        items_en_rebanada = []
        print("Valor óptimo de la función objetivo:", objective_value)
        for var_name, value in zip(nombreVariables, solution_values):
            print(f"{var_name} = {value}")
            if value == 1.0:
                # Si la variable tiene valor 1, extraemos la información del ítem y posición
                item=Item()
                if "n_" in var_name:  # Ítem no rotado
                    # Extraer el ítem y su posición
                    partes = var_name.replace("n_", "").split(",")
                    i = int(partes[0])
                    y = int(partes[2])
                    item.set_id(i)
                    item.set_alto(ALTO_OBJETO) 
                    item.set_posicion_y(y)
                    item.set_rotado(False)
                    
                else:  # Ítem rotado
                    # Extraer el ítem rotado y su posición
                    partes = var_name.replace("n_rot_", "").split(",")
                    i = int(partes[0])
                    y = int(partes[2])
                    item.set_id(i)
                    item.set_alto(ANCHO_OBJETO) 
                    item.set_posicion_y(y)
                    item.set_rotado(True)
                items_en_rebanada.append(item)

        
        status = modelo.solution.get_status()
        tiempoFinal = modelo.get_time()
        solverTime=tiempoFinal-tiempoInicial
        solverTime=round(solverTime, 2)
        
        if status == 105:  # CPLEX código 105 = Time limit exceeded
            print("El solver se detuvo porque alcanzó el límite de tiempo.")
            modelStatus="2" #valor en paver para marcar un optimo local

        # Enviar resultados a través de la cola
        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objective_value": objective_value,
            "solverTime": solverTime
        })
        
        rebanada= Rebanada()
        rebanada.set_items(items_en_rebanada)
        rebanada.set_alto(findHighestHeight(items_en_rebanada))
        
        return rebanada

    except CplexSolverError as e:
        if e.args[2] == 1217:  # Codigo de error para "No solution exists"
            print("\nNo existen soluciones para el modelo dado.")
            modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solverStatus="4" #el solver finalizo la ejecucion del modelo
        else:
            print("CPLEX Solver Error:", e)
            modelStatus="12" #valor en paver para marcar un error desconocido
            solverStatus="10" #el solver tuvo un error en la ejecucion

        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objective_value": objective_value,
            "solverTime": solverTime
        })


def executeWithTimeLimit(tiempo_maximo):
    global modelStatus, solverStatus, objective_value, solverTime 

    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    interrupcion_manual = multiprocessing.Value('b', True)

    # Crear el subproceso que correrá la función
    proceso = multiprocessing.Process(target=createAndSolveSlaveModel, args=(queue,interrupcion_manual,tiempo_maximo))

    # Iniciar el subproceso
    proceso.start()

    tiempo_inicial = time.time()

    # Monitorear la cola mientras el proceso está en ejecución
    while proceso.is_alive():

        if interrupcion_manual.value:
            # Si se excede el tiempo, terminamos el proceso
            if time.time() - tiempo_inicial > tiempo_maximo:
                print("Tiempo límite alcanzado. Abortando el proceso.")
                modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
                solverStatus="4" #el solver finalizo la ejecucion del modelo
                solverTime=tiempo_maximo
                proceso.terminate()
                proceso.join()
                break

        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            print(message)
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            objective_value = message["objective_value"]
            solverTime = message["solverTime"]



if __name__ == '__main__':
 
    executeWithTimeLimit(EXECUTION_TIME)
    generator = TraceFileGenerator("output.trc")
    generator.write_trace_record(NOMBRE_CASO, NOMBRE_MODELO, modelStatus, solverStatus, objective_value, solverTime)



def findHighestHeight(lista_items):
    highestHeight=0
    for item in lista_items:
        if(item.get_posicion_y()+item.get_alto()>highestHeight):
                highestHeight=item.get_posicion_y()+item.get_alto()
    return highestHeight