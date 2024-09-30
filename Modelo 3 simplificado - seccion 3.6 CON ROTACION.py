import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time

from Position_generator_modelo_3 import *



# Caso 5: 

CANTIDAD_ITEMS = 6  # constante N del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
ANCHO_BIN = 6  # W en el modelo
ALTO_BIN = 3  # H en el modelo

ANCHO_OBJETO = 3  # w en el modelo
ALTO_OBJETO = 2  # h en el modelo

#prueba para validar el corte al minuto de la ejecucion
CANTIDAD_ITEMS= 3250 # constante n del modelo
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo
ANCHO_BIN = 16 # W en el modelo
ALTO_BIN = 14 # H en el modelo

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
EXECUTION_TIME=60 # in seconds

def createAndSolveModel(queue,interrupcion_manual,tiempoMaximo):
    try:
        # Crear el modelo
        model = cplex.Cplex()

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

        # Imprimir resultados
        print("Estado de la solución:", model.solution.get_status_string())
        print("Valor de la función objetivo:", model.solution.get_objective_value())
        for i, var_name in enumerate(n_vars):
            print(f"{var_name} = {model.solution.get_values(var_name)}")


        # Imprimir los valores de las variables x_j^i
        print("\nValores de las variables x_j^i:")
        for i in range(len(I)):
            for j in range(len(T)):
                var_name = x_vars[i][j]
                value = model.solution.get_values(var_name)
                if value > 0:  # Mostrar solo las variables que están activas
                    print(f"{var_name} = {value}")

        # Imprimir los valores de las variables y_j^i
        print("\nValores de las variables y_j^i:")
        for i in range(len(I)):
            for j in range(len(T_rot)):
                var_name = y_vars[i][j]
                value = model.solution.get_values(var_name)
                if value > 0:  # Mostrar solo las variables que están activas
                    print(f"{var_name} = {value}")

    except CplexSolverError as e:
            if e.args[2] == 1217:
                print("\nNo existen soluciones para el modelo dado.")
            else:
                print("CPLEX Solver Error:", e)

def executeWithTimeLimit(tiempo_maximo):
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
        # Verificar si hay mensajes en la cola y mostrarlos
        while not queue.empty():
            print(queue.get())

        if interrupcion_manual.value:
            # Si se excede el tiempo, terminamos el proceso
            if time.time() - tiempo_inicial > tiempo_maximo:
                print("Tiempo límite alcanzado. Abortando el proceso.")
                proceso.terminate()
                proceso.join()
                break

        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Asegurarse de imprimir los mensajes restantes si el proceso terminó por sí mismo
    while not queue.empty():
        print(queue.get())



if __name__ == '__main__':
    # Ejecutar la función con un límite de tiempo de 10 segundos
    executeWithTimeLimit(EXECUTION_TIME)
