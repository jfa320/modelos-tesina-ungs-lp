import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
import multiprocessing
import time

from Position_generator_modelo_3 import *

NOMBRE_MODELO="Model3Pos2"

modelStatus="1"
solverStatus="1"
objective_value=0
solverTime=1

# Caso 5: 

# CANTIDAD_ITEMS = 6  # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 6  # W en el modelo
# ALTO_BIN = 3  # H en el modelo

# ANCHO_OBJETO = 3  # w en el modelo
# ALTO_OBJETO = 2  # h en el modelo

#prueba para validar el corte al minuto de la ejecucion
NOMBRE_CASO="inst2"
CANTIDAD_ITEMS= 10 # constante n del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo
ANCHO_BIN = 6 # W en el modelo
ALTO_BIN = 4 # H en el modelo

ANCHO_OBJETO= 2 # w en el modelo
ALTO_OBJETO= 3 # h en el modelo

# Parámetros
W = ANCHO_BIN  # Ancho del bin
H = ALTO_BIN  # Alto del bin
w = ANCHO_OBJETO # Ancho del item
h = ALTO_OBJETO  # Alto del item

I = range(CANTIDAD_ITEMS)  # Conjunto de items
J = generate_positions2_without_rotation(W, H, w, h)  # Posiciones sin rotación

J_rot = generate_positions2_without_rotation(W, H, h, w)  # Posiciones con rotación de 90 grados

P = [(x, y) for x in range(W) for y in range(H)]  # Puntos del bin
C = create_C_matrix(W, H, J, w, h, P)  # Matriz C para posiciones sin rotación
C_rot = create_C_matrix(W, H, J_rot, h, w, P)  # Matriz C para posiciones rotadas

# Conjunto de posiciones válidas por ítem
T = J
T_rot = J_rot
Q = len(T)  # Cantidad total de posiciones válidas por ítem
Q_rot = len(T_rot)  # Cantidad total de posiciones válidas rotadas por ítem

#seteo tiempo de ejecucion
EXECUTION_TIME=2 # in seconds

def createAndSolveModel(queue,interrupcion_manual,tiempoMaximo):
    #valores por default para enviar a paver
    modelStatus="1"
    solverStatus="1"
    objective_value=0
    solverTime=1

    try:
        # Crear el modelo
        model = cplex.Cplex()
        tiempoInicial=model.get_time()

        # Variables
        n_vars = []
        x_vars = []
        y_vars = []

        # Añadir las variables n_i
        for i in I:
            var_name = f"n_{i}"
            model.variables.add(names=[var_name], types=[model.variables.type.binary])
            n_vars.append(var_name)

        # Añadir las variables x_j^i
        for i in I:
            x_vars_i = []
            for j in T:
                var_name = f"x_{j}^{i}"
                model.variables.add(names=[var_name], types=[model.variables.type.binary])
                x_vars_i.append(var_name)
            x_vars.append(x_vars_i)

        # Añadir las variables y_j^i para las posiciones rotadas
        for i in I:
            y_vars_i = []
            for j in T_rot:
                var_name = f"y_{j}^{i}"
                model.variables.add(names=[var_name], types=[model.variables.type.binary])
                y_vars_i.append(var_name)
            y_vars.append(y_vars_i)

        # Función objetivo: maximizar la suma de n_i
        objective = [1.0] * len(I)
        model.objective.set_sense(model.objective.sense.maximize)
        model.objective.set_linear(list(zip(n_vars, objective)))

        # Definir el limite tiempo de la ejecución en un minuto
        model.parameters.timelimit.set(tiempoMaximo)

        # Restricción 1: Cada punto del bin está ocupado por a lo sumo un ítem (incluyendo rotaciones)
        for index_p, _ in enumerate(P):
            indices = []
            coefficients = []
            for i in I:
                for index_j, j in enumerate(T):
                    if C[index_j][index_p] == 1:
                        indices.append(f"x_{j}^{i}")
                        coefficients.append(1.0)
                for index_j, j in enumerate(T_rot):
                    if C_rot[index_j][index_p] == 1:
                        indices.append(f"y_{j}^{i}")
                        coefficients.append(1.0)
            model.linear_constraints.add(
                lin_expr=[[indices, coefficients]],
                senses=["L"],
                rhs=[1.0]
            )

        # Restricción 2: No exceder el área del bin
        indices = []
        coefficients = []
        seen_indices = set()

        for i in I:
            for index_j, j in enumerate(T):
                for index_p, _ in enumerate(P):
                    if C[index_j][index_p] == 1:
                        var_name = f"x_{j}^{i}"
                        if var_name not in seen_indices:
                            indices.append(var_name)
                            coefficients.append(1.0)
                            seen_indices.add(var_name)
            for index_j, j in enumerate(T_rot):
                for index_p, _ in enumerate(P):
                    if C_rot[index_j][index_p] == 1:
                        var_name = f"y_{j}^{i}"
                        if var_name not in seen_indices:
                            indices.append(var_name)
                            coefficients.append(1.0)
                            seen_indices.add(var_name)

        model.linear_constraints.add(
            lin_expr=[[indices, coefficients]],
            senses=["L"],
            rhs=[W * H]
        )

        # Restricción 3: n_i <= suma(x_j^i + y_j^i)
        for i in I:
            indices = [f"x_{j}^{i}" for j in T] + [f"y_{j}^{i}" for j in T_rot]
            coefficients = [1.0] * (len(T) + len(T_rot))
            indices.append(f"n_{i}")
            coefficients.append(-1.0)
            model.linear_constraints.add(
                lin_expr=[[indices, coefficients]],
                senses=["G"],
                rhs=[0.0]
            )

        # Restricción 4: suma(x_j^i) <= Q(i) * n_i
        for i in I:
            indices = [f"x_{j}^{i}" for j in T]
            coefficients = [1.0] * len(T)
            indices.append(f"n_{i}")
            coefficients.append(-Q)
            model.linear_constraints.add(
                lin_expr=[[indices, coefficients]],
                senses=["L"],
                rhs=[0.0]
            )

        # Restricción 5: suma(y_j^i) <= Q_rot(i) * n_i
        for i in I:
            indices = [f"y_{j}^{i}" for j in T_rot]
            coefficients = [1.0] * len(T_rot)
            indices.append(f"n_{i}")
            coefficients.append(-Q_rot)
            model.linear_constraints.add(
                lin_expr=[[indices, coefficients]],
                senses=["L"],
                rhs=[0.0]
            )

        # Desactivar la interrupción manual aquí
        interrupcion_manual.value = False

        # Resolver el modelo
        model.solve()
        objective_value = model.solution.get_objective_value()

        # Imprimir resultados
        print("Estado de la solución:", model.solution.get_status_string())
        print("Valor de la función objetivo:", objective_value)
        for i, var_name in enumerate(n_vars):
            print(f"{var_name} = {model.solution.get_values(var_name)}")

        status = model.solution.get_status()
        tiempoFinal = model.get_time()
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
    proceso = multiprocessing.Process(target=createAndSolveModel, args=(queue,interrupcion_manual,tiempo_maximo))

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