import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
import time

MODEL_NAME = "Model5Master"
DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS = True


def calcular_posiciones_ocupadas(posicion, ancho, alto):
        """
        Retorna todas las posiciones ocupadas por un ítem ubicado en `posicion` con dimensiones `ancho` x `alto`.
        """
        x, y = posicion
        posiciones_ocupadas = set()
        for dx in range(ancho):
            for dy in range(alto):
                posiciones_ocupadas.add((x + dx, y + dy))
        return posiciones_ocupadas

def create_master_model(max_time, rebanadas, alto_bin, ancho_bin, alto_item, ancho_item, pos_xy_x, pos_xy_y):
    print("IN - Create Master Model")
    h = alto_bin
    rebanadas_modelo = rebanadas
    posiciones = [(x, y) for x in range(ancho_bin) for y in range(alto_bin)]

    try:
        # Crear instancia del problema
        model = cplex.Cplex()
        model.set_problem_type(cplex.Cplex.problem_type.MILP) 
        model.parameters.timelimit.set(max_time)
        
        #Desactivo el presolve
        model.parameters.preprocessing.presolve.set(0)
        #Seteo el metodo simplex para resolver el modelo
        model.parameters.lpmethod.set(1)
        # Variables
        # Variables p_r (binarias)
        p_r_names = [f"p_{r.get_id()}" for r in rebanadas_modelo]
        coeffs_p_r = [r.get_total_items() for r in rebanadas_modelo]
        print("======================================")
        print("COEFICIENTES FO MAESTRO")
        print("======================================")
        def resumir_rebanada(rebanada):
            return sorted((item.get_posicion_x(), item.get_posicion_y(), item.get_rotado()) for item in rebanada.get_items())

        for r, nombre, coef in zip(rebanadas_modelo, p_r_names, coeffs_p_r):
            print(f"{nombre} | id={r.get_id()} | totalItems={r.get_total_items()} | lenItems={len(r.get_items())} | resumen={resumir_rebanada(r)}")
        
        add_variables(model, p_r_names, coeffs_p_r, model.variables.type.binary)


        p_r_by_id = {r.get_id(): f"p_{r.get_id()}" for r in rebanadas_modelo}
    
        model.objective.set_sense(model.objective.sense.maximize)

        added_constraints = set()
        
        
        # # ----------------------------------------------------
        # Precomputar celdas ocupadas por cada rebanada: Φ(r)
        celulas_por_rebanada = {}
        for r in rebanadas_modelo:
            ocupadas = set()
            for it in r.get_items():
                if it.get_posicion_x() is None or it.get_posicion_y() is None:
                    continue
                x, y = it.get_posicion()
                for dx in range(it.get_ancho()):
                    for dy in range(it.get_alto()):
                        ocupadas.add((x + dx, y + dy))
            celulas_por_rebanada[r.get_id()] = ocupadas


        # Restricción de posiciones ocupadas por rebanadas
        for (a, b) in posiciones:
            rebanadas_que_ocupan_posicion = [r for r in rebanadas_modelo if (a, b) in celulas_por_rebanada[r.get_id()]]
            if rebanadas_que_ocupan_posicion:
                indexes = [f"p_{r.get_id()}" for r in rebanadas_que_ocupan_posicion]
                coeffs = [1.0] * len(rebanadas_que_ocupan_posicion)
                add_constraint_set(
                    model,
                    coeffs,
                    indexes,
                    1.0,
                    "L",
                    added_constraints,
                    f"consItem_{a}_{b}",
                    DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
                )

        # print(f"Rebanadas usadas: {R}")
        print("OUT - Create Master Model")
        return model
    
    except CplexSolverError:
        raise


def solve_master_model(model, queue, manual_interruption, relajar_modelo, initial_time):
    print("IN - Solve Master Model")
    # valores por default para enviar a paver
    model_status, solver_status, objective_value, solver_time = "1", "1", 0, 1
    
    try:    
        # Desactivar la interrupción manual aquí
        manual_interruption.value = False
        
        
        if(relajar_modelo):
            print("Relajando modelo...")
            model.set_problem_type(cplex.Cplex.problem_type.LP)
        else:
            print("NO RELAJO MODELO - QUEDA COMO MILP")
            model.set_problem_type(cplex.Cplex.problem_type.MILP)
        
        # Resolver el modelo
        model.solve()
            
        objective_value = model.solution.get_objective_value()
        # Imprimir resultados
        print("Optimal value:", objective_value)
        dual_values = None
        variables_activas = []
        if(relajar_modelo):
            # Obtener valores duales
            dual_values = get_dual_values(model)
            # print("Dual values:", dualValues)    
            
            
        # imprimo valor que toman las variables
        for i, var_name in enumerate(model.variables.get_names()):
            valor_variable = model.solution.get_values(var_name)
            if valor_variable > 0.5:
                variables_activas.append(var_name)

        status = model.solution.get_status()
        
        
        
        if status == 105:  # CPLEX código 105 = Time limit exceeded
            print("The solver stopped because it reached the time limit.")
            model_status = "2" #valor en paver para marcar un optimo local

        if(not relajar_modelo):
            final_time = time.time()
            solver_time = final_time - initial_time
            solver_time = round(solver_time, 2)
            # Enviar resultados a través de la cola solo cuando el modelo no está relajado, es decir, cuando se va a resolver finalmente
            queue.put({
                "modelStatus": model_status,
                "solverStatus": solver_status,
                "objectiveValue": objective_value,
                "solverTime": solver_time
            })
        # Obtener la cantidad de restricciones
        
        print("OUT - Solve Master Model")
        return objective_value, dual_values, variables_activas
    
    except CplexSolverError as e:
        handle_solver_error(e, queue, solver_time)
        
def get_dual_values(model):
    print("Extrayendo valores duales...")

    p_star = {"pi": {}}

    dual_values = model.solution.get_dual_values()
    constraint_names = model.linear_constraints.get_names()

    for name, dual_value in zip(constraint_names, dual_values):
        if name.startswith("consItem_"):
            # nombre: consItem_a_b
            _, a, b = name.split("_")
            p_star["pi"][f"({a},{b})"] = dual_value

    return p_star


