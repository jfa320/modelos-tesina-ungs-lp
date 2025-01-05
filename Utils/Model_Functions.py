import cplex
from cplex.exceptions import CplexSolverError

def addVariables(model, varNames, objCoeffs, varType):
    model.variables.add(names=varNames, obj=objCoeffs, types=varType * len(varNames))

def addConstraint(model, coeff, vars, rhs, sense,constraintName=None):
    
    if(constraintName):
        model.linear_constraints.add(
            lin_expr=[cplex.SparsePair(vars, coeff)],
            senses=[sense],
            rhs=[rhs],
            names=[constraintName]
        )
    else:
        model.linear_constraints.add(
            lin_expr=[cplex.SparsePair(vars, coeff)],
            senses=[sense],
            rhs=[rhs]
        )
    
def addConstraintSet(model, coeff, vars, rhs, sense, added_constraints,constraintName=None):
    # Crear una representación única de la restricción
    
    #filtro de variables con coeficientes 0 - es lo mismo que hace CPLEX, de esta manera evito que se repitan restricciones
    filtered = [(c, v) for c, v in zip(coeff, vars) if c != 0]
    if filtered:
        coeff, vars = zip(*filtered)
    else:
        coeff, vars = (), ()

    new_constraint = (tuple(coeff), tuple(vars), rhs, sense)
    
    if new_constraint in added_constraints:
        print(f"La restricción ya existe: {new_constraint}. No se agrega nuevamente.")
        return
    
    # Agregar la restricción al modelo
    if vars:
        print(f"agrego restriccion nro: {len(added_constraints)+1}")
        addConstraint(model, coeff, vars, rhs, sense, constraintName)
        # Registrar la nueva restricción
        added_constraints.add(new_constraint)
    
    
def handleSolverError(e, queue,solverTime):
    errorCode = e.args[2]
    modelStatus, solverStatus = ("14", "4") if errorCode == 1217 else ("12", "10")
    queue.put({
        "modelStatus": modelStatus,
        "solverStatus": solverStatus,
        "objectiveValue": 0,
        "solverTime": solverTime
    })