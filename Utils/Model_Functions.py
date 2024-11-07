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
    
def handleSolverError(e, queue,solverTime):
    errorCode = e.args[2]
    modelStatus, solverStatus = ("14", "4") if errorCode == 1217 else ("12", "10")
    queue.put({
        "modelStatus": modelStatus,
        "solverStatus": solverStatus,
        "objectiveValue": 0,
        "solverTime": solverTime
    })