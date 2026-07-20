import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time
from Utils.Model_Functions import *
from Config import *

# Basado en la simplificacion del modelo 1 (modelo base - Pisinger & Sigurd) - ver seccion 2.8 en Overleaf para modelo completo
# Caso sencillo que mejora con rotacion
MODEL_NAME = "Model1"


def aplicar_instancia(instance):
    global CASE_NAME, BIN_WIDTH, BIN_HEIGHT, ITEM_WIDTH, ITEM_HEIGHT
    CASE_NAME = instance["case_name"]
    BIN_WIDTH = instance["bin_width"]
    BIN_HEIGHT = instance["bin_height"]
    ITEM_WIDTH = instance["item_width"]
    ITEM_HEIGHT = instance["item_height"]


def run_model_for_instance(instance, create_model_fn, solve_model_fn, queue, manual_interruption, max_time):
    aplicar_instancia(instance)
    run_model(create_model_fn, solve_model_fn, queue, manual_interruption, max_time)


def calcular_cota_fisica_items():
    return (BIN_WIDTH // ITEM_WIDTH) * (BIN_HEIGHT // ITEM_HEIGHT)


def create_model(max_time):
    # Crear un modelo de CPLEX
    model = cplex.Cplex()

    model.set_results_stream(None)  # deshabilito log de CPLEX de la info paso a paso
    model.set_problem_type(cplex.Cplex.problem_type.MILP)
    model.objective.set_sense(model.objective.sense.maximize)
    # Definir el limite tiempo de la ejecución en un minuto
    model.parameters.timelimit.set(max_time)

    # Definir variables y objetivos
    items = list(range(1, calcular_cota_fisica_items() + 1))
    vars_names = [f"f_{i}" for i in items]
    coeffs = [1.0] * len(items)
    add_variables(model, vars_names, coeffs, "B")

    additional_vars_names = [f"x_{i}" for i in items] + [f"y_{i}" for i in items]
    additional_coeff_obj = [0.0] * len(additional_vars_names)
    add_variables(model, additional_vars_names, additional_coeff_obj, "I")

    additional_vars_names = set()
    for i in items:
        for j in items:
            if i != j:
                additional_vars_names.add(f"l_{i},{j}")  # agrego variable l_{ij}
                additional_vars_names.add(f"l_{j},{i}")  # agrego variable l_{ij}
                additional_vars_names.add(f"b_{i},{j}")  # agrego variable b_{ij}
                additional_vars_names.add(f"b_{j},{i}")  # agrego variable b_{ij}
    additional_vars_names = list(additional_vars_names)
    additional_coeff_obj = [0.0] * len(additional_vars_names)
    add_variables(model, additional_vars_names, additional_coeff_obj, "B")

    # Añadir las restricciones para cada par (i, j) con i < j
    for i in items:
        for j in items:
            if i < j:  # Aca fue necesario reescribir la restriccion para que funcione con CPLEX
                cons_coeff = [1.0, 1.0, 1.0, 1.0, -1.0, -1.0]
                cons_vars = [f"l_{i},{j}", f"l_{j},{i}", f"b_{i},{j}", f"b_{j},{i}", f"f_{i}", f"f_{j}"]
                cons_rhs = -1.0
                cons_sense = "G"  # "G" indica >=
                add_constraint(model, cons_coeff, cons_vars, cons_rhs, cons_sense)

    # Añadir las restricciones x_i - x_j + W l_{ij} <= W - w para cada i en I
    for i in items:
        for j in items:
            if i != j:
                cons_coeff = [1.0, -1.0, BIN_WIDTH]
                cons_vars = [f"x_{i}", f"x_{j}", f"l_{i},{j}"]
                cons_rhs = BIN_WIDTH - ITEM_WIDTH
                cons_sense = "L"  # "L" indica <=
                add_constraint(model, cons_coeff, cons_vars, cons_rhs, cons_sense)

    # Añadir las restricciones y_i - y_j + H b_{ij} <= H - h para cada i en I
    for i in items:
        for j in items:
            if i != j:
                cons_coeff = [1.0, -1.0, BIN_HEIGHT]
                cons_vars = [f"y_{i}", f"y_{j}", f"b_{i},{j}"]
                cons_rhs = BIN_HEIGHT - ITEM_HEIGHT
                cons_sense = "L"  # "L" indica <=
                add_constraint(model, cons_coeff, cons_vars, cons_rhs, cons_sense)

    # Añadir la restricción x_i + W f_i <= 2W - w para cada i en I
    for i in items:
        cons_coeff = [1.0, BIN_WIDTH]  # Coeficientes para x_i y f_i
        cons_vars = [f"x_{i}", f"f_{i}"]  # Variables en la restricción
        cons_rhs = 2 * BIN_WIDTH - ITEM_WIDTH  # Lado derecho de la restricción
        cons_sense = "L"  # "L" indica <=
        add_constraint(model, cons_coeff, cons_vars, cons_rhs, cons_sense)

    # Añadir la restricción y_i + H f_i <= 2H - h para cada i en I
    for i in items:
        cons_coeff = [1.0, BIN_HEIGHT]  # Coeficientes para y_i y f_i
        cons_vars = [f"y_{i}", f"f_{i}"]  # Variables en la restricción
        cons_rhs = 2 * BIN_HEIGHT - ITEM_HEIGHT  # Lado derecho de la restricción
        cons_sense = "L"  # "L" indica <=
        add_constraint(model, cons_coeff, cons_vars, cons_rhs, cons_sense)

    return model


def solve_model(model, queue, manual_interruption):
    # Desactivar la interrupción manual aquí
    manual_interruption.value = False

    # Resolver el modelo
    model.solve()

    # Obtener y mostrar los resultados
    objective_value = model.solution.get_objective_value()
    print("-------------------------------------------")
    print("Modelo 1 - Sin Rotacion")
    print(f"Optimal value: {objective_value}")

    model_status, solver_status = "1", "1"
    status = model.solution.get_status()
    if status == 105:
        print("The solver stopped because it reached the time limit.")
        model_status = "2"

    return model_status, solver_status, objective_value


def execute_with_time_limit(max_time, instance=None):
    global model_status, solver_status, objective_value, solver_time
    global exceding_limit_time
    exceding_limit_time = False

    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    manual_interruption = multiprocessing.Value('b', True)

    if instance is None:
        instance = get_instance(CASE_NAME)

    # Crear el subproceso que correrá la función
    process = multiprocessing.Process(target=run_model_for_instance, args=(instance, create_model, solve_model, queue, manual_interruption, max_time))

    # Iniciar el subproceso
    process.start()

    initial_time = time.time()

    # Monitorear la cola mientras el proceso está en ejecución
    while process.is_alive():
        if manual_interruption.value and time.time() - initial_time > max_time:
            print("Limit time reached. Aborting process.")
            model_status = "14"  # valor en paver para marcar que el modelo no devolvio respuesta por error
            solver_status = "4"  # el solver finalizo la ejecucion del modelo
            solver_time = max_time
            exceding_limit_time = True
            process.terminate()
            process.join()
            break
        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            print(message)
            model_status = message["modelStatus"]
            solver_status = message["solverStatus"]
            objective_value = message["objectiveValue"]
            solver_time = message["solverTime"]

    if exceding_limit_time:
        print("El modelo excedió el tiempo límite de ejecución.")
        objective_value = "n/a"
        model_status = "14"

    return instance["case_name"], MODEL_NAME, model_status, solver_status, objective_value, solver_time
