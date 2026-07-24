import cplex
from cplex.exceptions import CplexSolverError
import time


def add_variables(model, var_names, obj_coeffs, var_type):
    n = len(var_names)
    types = [var_type] * n

    lb = [0.0] * n
    if var_type == "B":
        ub = [1.0] * n
    else:
        ub = [cplex.infinity] * n

    model.variables.add(
        names=var_names,
        obj=obj_coeffs,
        lb=lb,
        ub=ub,
        types=types
    )


def add_constraint(model, coeff, vars, rhs, sense, constraint_name=None):
    if constraint_name:
        model.linear_constraints.add(
            lin_expr=[cplex.SparsePair(vars, coeff)],
            senses=[sense],
            rhs=[rhs],
            names=[constraint_name]
        )
    else:
        model.linear_constraints.add(
            lin_expr=[cplex.SparsePair(vars, coeff)],
            senses=[sense],
            rhs=[rhs]
        )


def add_constraint_set(
    model,
    coeff,
    vars,
    rhs,
    sense,
    added_constraints,
    constraint_name=None,
    disable_duplicate_constraint_check=False
):
    filtered = [(c, v) for c, v in zip(coeff, vars) if c != 0]
    if filtered:
        coeff, vars = zip(*filtered)
    else:
        coeff, vars = (), ()

    new_constraint = (tuple(coeff), tuple(vars), rhs, sense)

    if new_constraint in added_constraints and not disable_duplicate_constraint_check:
        return

    if vars:
        add_constraint(model, coeff, vars, rhs, sense, constraint_name)
        added_constraints.add(new_constraint)


def handle_solver_error(e, queue, solver_time):
    error_code = e.args[2]
    model_status, solver_status = ("14", "4") if error_code == 1217 else ("12", "10")
    queue.put({
        "modelStatus": model_status,
        "solverStatus": solver_status,
        "objectiveValue": 0,
        "solverTime": solver_time
    })


def run_model(create_model, solve_model, queue, manual_interruption, max_time):
    # Default values for PAVER.
    model_status, solver_status, objective_value, solver_time = "1", "1", 0, 1
    start = time.time()

    try:
        model = create_model(max_time)
        model_status, solver_status, objective_value = solve_model(model, queue, manual_interruption)
        solver_time = round(time.time() - start, 2)

    except CplexSolverError as e:
        solver_time = round(time.time() - start, 2)
        handle_solver_error(e, queue, solver_time)
        return

    except Exception as e:
        solver_time = round(time.time() - start, 2)
        print(f"Unexpected error during model creation/solve: {e}")

    queue.put({
        "modelStatus": model_status,
        "solverStatus": solver_status,
        "objectiveValue": objective_value,
        "solverTime": solver_time
    })
