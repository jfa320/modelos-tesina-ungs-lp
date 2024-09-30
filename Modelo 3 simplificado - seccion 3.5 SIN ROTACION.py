import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time

from Position_generator_modelo_3 import *


# Caso 5: 

# CANTIDAD_ITEMS = 6  # constante N del modelo
# ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) 
# ANCHO_BIN = 6  # W en el modelo
# ALTO_BIN = 3  # H en el modelo

# ANCHO_OBJETO = 3  # w en el modelo
# ALTO_OBJETO = 2  # h en el modelo

#prueba para validar el corte al minuto de la ejecucion
CANTIDAD_ITEMS= 325 # constante n del modelo
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
J = generate_positions2_without_rotation(W, H, w, h) #posiciones
P = [(x, y) for x in range(W) for y in range(H)]  #puntos
C = create_C_matrix(W, H, J,w,h,P)

# Conjunto de posiciones válidas por item 
T = J
Q = len(T)  # Cantidad total de posiciones válidas por item

#seteo tiempo de ejecucion
EXECUTION_TIME=60 # in seconds

def createAndSolveModel(queue,interrupcion_manual,tiempoMaximo):
    try:

        # Crear el modelo
        model = cplex.Cplex()

        # Variables
        n_vars = []
        x_vars = []

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

        # Función objetivo: maximizar la suma de n_i
        objective = [1.0] * len(I)
        model.objective.set_sense(model.objective.sense.maximize)
        model.objective.set_linear(list(zip(n_vars, objective)))
        
        # Definir el limite tiempo de la ejecución en un minuto
        model.parameters.timelimit.set(tiempoMaximo)


        # Restricción 1: Cada punto del bin está ocupado por a lo sumo un item
        for index_p,_ in enumerate(P):
            indices = []
            coefficients = []
            for i in I:
                for index_j,j in enumerate(T):
                    if C[index_j][index_p] == 1:
                        indices.append(f"x_{j}^{i}")
                        coefficients.append(1.0)
            model.linear_constraints.add(
                lin_expr=[[indices, coefficients]],
                senses=["L"],
                rhs=[1.0]
            )

        # Restricción 2: No exceder el área del bin
        indices = []
        coefficients = []
        seen_indices = set()  # Conjunto para verificar duplicados

        for i in I:
            for index_j, j in enumerate(T):
                for index_p, _ in enumerate(P):
                    if C[index_j][index_p] == 1:
                        var_name = f"x_{j}^{i}"
                        if var_name not in seen_indices:  # Verificar si ya se ha agregado
                            indices.append(var_name)
                            coefficients.append(1.0)
                            seen_indices.add(var_name)  # Marcar como agregado

        # Agregar la restricción al modelo sin duplicados
        model.linear_constraints.add(
            lin_expr=[[indices, coefficients]],
            senses=["L"],
            rhs=[W * H]
        )

        # Restricción 3: n_i <= suma(x_j^i)
        for i in I:
            indices = [f"x_{j}^{i}" for j in T]
            coefficients = [1.0] * len(T)
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

        # Desactivar la interrupción manual aquí
        interrupcion_manual.value = False

        # Resolver el modelo
        model.solve()

        # Imprimir resultados
        print("Estado de la solución:", model.solution.get_status_string())
        print("Valor de la función objetivo:", model.solution.get_objective_value())


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


