import cplex
from cplex.exceptions import CplexSolverError

def addVariables(model, varNames, objCoeffs, varType):
    model.variables.add(names=varNames, obj=objCoeffs, types=varType * len(varNames))

def addConstraint(model, coeff, vars, rhs, sense):
    model.linear_constraints.add(
        lin_expr=[cplex.SparsePair(vars, coeff)],
        senses=[sense],
        rhs=[rhs]
    )
    
def addConstraintSet(model, coeff, vars, rhs, sense, added_constraints):
    # Crear una representación única de la restricción
    new_constraint = (tuple(coeff), tuple(vars), rhs, sense)
    print(f"set: {added_constraints}")
    # Verificar si la restricción ya ha sido agregada
    if new_constraint in added_constraints:
        print(f"La restricción ya existe: {new_constraint}. No se agrega nuevamente.")
        return

    # Agregar la restricción al modelo
    addConstraint(model, coeff, vars, rhs, sense)
    
    # Registrar la nueva restricción
    added_constraints.add(new_constraint)
    print(f"Restricción agregada: {new_constraint}")  
    
def handleSolverError(e, queue,solverTime):
    errorCode = e.args[2]
    modelStatus, solverStatus = ("14", "4") if errorCode == 1217 else ("12", "10")
    queue.put({
        "modelStatus": modelStatus,
        "solverStatus": solverStatus,
        "objectiveValue": 0,
        "solverTime": solverTime
    })