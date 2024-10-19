import cplex
from cplex.exceptions import CplexSolverError
from TraceFileGenerator import TraceFileGenerator
import multiprocessing
import time

from Position_generator import *

NOMBRE_MODELO="Model4Maestro"

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

ANCHO_BIN = 6 # W en el modelo
ANCHO_OBJETO= 2 # w en el modelo
ALTO_OBJETO= 3 # h en el modelo

REBANADAS=[] #TODO CARGAR ARRAY CON LO DEL ESCLAVO
ALTO_REBANADA = [] # H_r en el modelo #TODO CARGAR ARRAY
ALTO_BIN=4
POSICIONES_Y= generate_positions_modelo_maestro(ALTO_BIN, ) #TODO: PENSAR COMO MANEJAR LAS POSICIONES AHORA QUE TENGO QUE TENER EN CUENTA QUE SOBRESALEN ITEMS (VER MAIL)
CANTIDAD_ITEMS= 10 
ITEMS = list(range(1, CANTIDAD_ITEMS + 1)) # constante I del modelo

CANTIDAD_REBANADAS=len(REBANADAS)

POS_REL_ITEM_Y=[] #TODO PENSAR COMO CARGARLO, QUIZAS CON EL NUMERO DE ITEM Y SU POSICION
ALTOS_ITEM=[] #TODO CARGAR ARRAY CON LO QUE VENGA DEL ESCLAVO


EXECUTION_TIME=2 # in seconds

def createAndSolveModel(queue,interrupcion_manual,tiempoMaximo):
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

        # Variables para indicar si uso o no la rebanada r en el bin (para la FO)
        # Acá defino la FUNCION OBJETIVO
        nombre_p_r  = [f"p_{r}" for r in REBANADAS]
        coeficientes = coeficientes = [1.0] * CANTIDAD_REBANADAS
        modelo.variables.add(names=nombre_p_r, obj=coeficientes, types="B" * CANTIDAD_REBANADAS)


        # Variables para indicar si la rebanada r ocupa la posición p (s_{rp})
        nombre_s_rp = [f"s_{r},{p}" for r in REBANADAS for p in POSICIONES_Y]
        coef_s_rp = [0.0]* (len(REBANADAS) * len(POSICIONES_Y)) 
        modelo.variables.add(names=nombre_s_rp, obj=coef_s_rp, types="B" * len(nombre_s_rp))

        # Variables para indicar la ubicacion y donde se ubica una rebanada r
        nombre_y_r = [f"y_{r}" for r in REBANADAS]
        modelo.variables.add(names=nombre_y_r, obj=[0.0] * len(nombre_y_r), types="C" * len(nombre_y_r), lb=[0.0] * len(nombre_y_r))

        # Variables para determinar si una rebanada i se ubica arriba de otra rebanada j
        nombre_z_ij = [f"z_{i},{j}" for i in REBANADAS for j in REBANADAS if i != j]
        modelo.variables.add(names=nombre_z_ij, obj=[0.0] * len(nombre_z_ij), types="B" * len(nombre_z_ij))

        # Variables w_{i,r} (indica si el ítem i está en la rebanada r)
        nombre_w_ir = [f"w_{i},{r}" for i in ITEMS for r in REBANADAS]
        modelo.variables.add(names=nombre_w_ir, obj=[0.0] * len(nombre_w_ir), types="B" * len(nombre_w_ir))
     
        # Variables y_{i,r} indica la posicion absoluta en el eje y del item i de la rebanada r en el bin
        nombre_y_ir = [f"y_{i},{r}" for i in ITEMS for r in REBANADAS]
        modelo.variables.add(names=nombre_y_ir, obj=[0.0] * len(nombre_y_ir), types="C" * len(nombre_y_ir), lb=[0.0] * len(nombre_y_ir))

        
        # Restricción (1): Cada ítem se ubica solo en una rebanada
        for i in ITEMS:
            varW_ir = [f"w_{i},{r}" for r in REBANADAS]
            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=varW_ir, val=[1] * len(varW_ir))],
                senses=["L"], rhs=[1]
            )
        
        # Restricción (2): Un ítem pertenece a una rebanada solo si la rebanada es seleccionada
        for i in ITEMS:
            for r in REBANADAS:
                modelo.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=[f"w_{i},{r}", f"p_{r}"], val=[1, -1])],
                    senses=["L"], rhs=[0]
                )

        # Restricción (3): La suma de las alturas de las rebanadas seleccionadas no excede la altura del bin
        modelo.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=nombre_p_r, val=[ALTO_REBANADA[r] for r in REBANADAS])],
            senses=["L"], rhs=[ALTO_BIN]
        )

        # Restricción (4): Si se elige una rebanada, debe ocupar una sola posición en el bin
        for r in REBANADAS:
            varS_rp = [f"s_{r},{p}" for p in POSICIONES_Y]
            modelo.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind=varS_rp + [f"p_{r}"], val=[1] * len(varS_rp) + [-1])],
                senses=["L"], rhs=[0]
            )

        # Restricciones (5) y (6): Las rebanadas no deben solaparse verticalmente
        for r in REBANADAS:
            for rp in REBANADAS:
                if r != rp:
                    modelo.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=[f"y_{r}", f"y_{rp}", f"z_{rp},{r}"], val=[1, -1, ALTO_BIN])],
                        senses=["L"], rhs=[ALTO_BIN] - ALTO_REBANADA[r]
                    )
                    modelo.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=[f"y_{rp}", f"y_{r}", f"z_{r},{rp}"], val=[1, -1, ALTO_BIN])],
                        senses=["L"], rhs=[ALTO_BIN] - ALTO_REBANADA[rp]
                    )

        # Restricción (7): Cada par de rebanadas deben estar en una relación de arriba o abajo, no ambas
        for r in REBANADAS:
            for rp in REBANADAS:
                if r != rp:
                    modelo.linear_constraints.add(
                        lin_expr=[cplex.SparsePair(ind=[f"z_{r},{rp}", f"z_{rp},{r}"], val=[1, 1])],
                        senses=["E"], rhs=[1]
                    )

        # Restricción (8): Establece la posicion absoluta en el bin de cada item de una rebanada
        for i in ITEMS:
            for r in REBANADAS:
                modelo.linear_constraints.add(
                    lin_expr=[cplex.SparsePair(ind=[f"y_{i},{r}", f"y_{r}"], val=[1, -1])],
                    senses=["E"], rhs=[POS_REL_ITEM_Y[i,r]] #TODO REVISAR COMO ACCEDER A ESTE ARRAY (quizas usar diccionarios)
                )

        # Restricción (9) y (10): Asegura que los items de las rebanadas no se solapen entre sí
        for i in ITEMS:
            for j in ITEMS:
                if i != j:  # Solo si i y j son distintos
                    for r in REBANADAS:
                        for r_prime in REBANADAS:
                            if r != r_prime:  # Solo si r y r' son distintos
                                
                                # Restricción (9): y_{ir} + h_i <= y_{jr'} + H * z_{r,r'}
                                constraint_9 = cplex.SparsePair(
                                    ind=[f"y_{i},{r}", f"y_{j},{r_prime}", f"z_{r},{r_prime}"],
                                    val=[1.0, -1.0, -ALTO_BIN]
                                )
                                modelo.linear_constraints.add(
                                    lin_expr=[constraint_9],
                                    senses=["L"],  
                                    rhs=[-ALTOS_ITEM[i]]  #TODO: VER SI ACCEDO ASI AL ALTO
                                )
                                
                                # Restricción (10): y_{jr'} + h_j <= y_{ir} + H * (1 - z_{r,r'})
                                # Esto es equivalente a y_{jr'} + h_j <= y_{ir} + H - H * z_{r,r'}
                                constraint_10 = cplex.SparsePair(
                                    ind=[f"y_{j},{r_prime}", f"y_{i},{r}", f"z_{r},{r_prime}"],
                                    val=[1.0, -1.0, ALTO_BIN]
                                )
                                modelo.linear_constraints.add(
                                    lin_expr=[constraint_10],
                                    senses=["L"],  
                                    rhs=[ALTO_BIN - ALTOS_ITEM[j]]  #TODO: VER SI ACCEDO ASI AL ALTO
                                )
        
        # Desactivar la interrupción manual aquí
        interrupcion_manual.value = False

        # Resolver el modelo
        modelo.solve()

        # Obtener resultados
        solution_values = modelo.solution.get_values()
        objective_value = modelo.solution.get_objective_value()

        print("Valor óptimo de la función objetivo:", objective_value)
        for var_name, value in zip(nombre_p_r, solution_values):
            print(f"{var_name} = {value}")
        
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

