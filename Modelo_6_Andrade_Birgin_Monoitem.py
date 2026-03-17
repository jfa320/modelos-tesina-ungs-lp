import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time
from Utils.Model_Functions import *
from Config import *

MODEL_NAME = "AndradeBirginBigM"


def createModel(maxTime):
    model = cplex.Cplex()

    model.set_results_stream(None)
    model.set_problem_type(cplex.Cplex.problem_type.MILP)
    model.objective.set_sense(model.objective.sense.maximize)
    model.parameters.timelimit.set(maxTime)

    maxItemDim = max(ITEM_WIDTH, ITEM_HEIGHT)

    bigMx = 2 * BIN_WIDTH + 2 * maxItemDim
    bigMy = 2 * BIN_HEIGHT + 2 * maxItemDim

    # -----------------------------
    # Variables
    # -----------------------------
    usedVarNames = [f"f_{i}" for i in ITEMS]
    usedVarObj = [1.0] * ITEMS_QUANTITY
    addVariables(model, usedVarNames, usedVarObj, "B")

    rotVarNames = [f"r_{i}" for i in ITEMS]
    rotVarObj = [0.0] * ITEMS_QUANTITY
    addVariables(model, rotVarNames, rotVarObj, "B")

    centerVarNames = [f"cx2_{i}" for i in ITEMS] + [f"cy2_{i}" for i in ITEMS]
    centerVarObj = [0.0] * len(centerVarNames)
    addVariables(model, centerVarNames, centerVarObj, "I")

    effDimVarNames = [f"wEff_{i}" for i in ITEMS] + [f"hEff_{i}" for i in ITEMS]
    effDimVarObj = [0.0] * len(effDimVarNames)
    addVariables(model, effDimVarNames, effDimVarObj, "I")

    relativePosVars = []
    for i in ITEMS:
        for j in ITEMS:
            if i < j:
                relativePosVars.append(f"q_{i},{j}")
                relativePosVars.append(f"q_{j},{i}")

    addVariables(model, relativePosVars, [0.0] * len(relativePosVars), "B")

    # -----------------------------
    # Dimensiones efectivas
    # -----------------------------
    delta = ITEM_HEIGHT - ITEM_WIDTH

    for i in ITEMS:
        # wEff_i = ITEM_WIDTH + delta * r_i
        consCoeff = [1.0, -delta]
        consVars = [f"wEff_{i}", f"r_{i}"]
        consRhs = ITEM_WIDTH
        consSense = "E"
        addConstraint(model, consCoeff, consVars, consRhs, consSense)

        # hEff_i = ITEM_HEIGHT - delta * r_i
        consCoeff = [1.0, delta]
        consVars = [f"hEff_{i}", f"r_{i}"]
        consRhs = ITEM_HEIGHT
        consSense = "E"
        addConstraint(model, consCoeff, consVars, consRhs, consSense)

    # -----------------------------
    # Contención en el bin
    # -----------------------------
    for i in ITEMS:
        # cx2_i - wEff_i >= -bigMx * (1 - f_i)
        consCoeff = [1.0, -1.0, -bigMx]
        consVars = [f"cx2_{i}", f"wEff_{i}", f"f_{i}"]
        consRhs = -bigMx
        consSense = "G"
        addConstraint(model, consCoeff, consVars, consRhs, consSense)

        # cx2_i + wEff_i <= 2*BIN_WIDTH + bigMx*(1-f_i)
        consCoeff = [1.0, 1.0, bigMx]
        consVars = [f"cx2_{i}", f"wEff_{i}", f"f_{i}"]
        consRhs = 2 * BIN_WIDTH + bigMx
        consSense = "L"
        addConstraint(model, consCoeff, consVars, consRhs, consSense)

        # cy2_i - hEff_i >= -bigMy * (1 - f_i)
        consCoeff = [1.0, -1.0, -bigMy]
        consVars = [f"cy2_{i}", f"hEff_{i}", f"f_{i}"]
        consRhs = -bigMy
        consSense = "G"
        addConstraint(model, consCoeff, consVars, consRhs, consSense)

        # cy2_i + hEff_i <= 2*BIN_HEIGHT + bigMy*(1-f_i)
        consCoeff = [1.0, 1.0, bigMy]
        consVars = [f"cy2_{i}", f"hEff_{i}", f"f_{i}"]
        consRhs = 2 * BIN_HEIGHT + bigMy
        consSense = "L"
        addConstraint(model, consCoeff, consVars, consRhs, consSense)

    # -----------------------------
    # No superposición
    # -----------------------------
    for i in ITEMS:
        for j in ITEMS:
            if i < j:
                qij = f"q_{i},{j}"
                qji = f"q_{j},{i}"

                # 1) i a la derecha de j
                consCoeff = [
                    1.0, -1.0,
                    -1.0, -1.0,
                    bigMx, bigMx,
                    -bigMx, -bigMx
                ]
                consVars = [
                    f"cx2_{i}", f"cx2_{j}",
                    f"wEff_{i}", f"wEff_{j}",
                    qij, qji,
                    f"f_{i}", f"f_{j}"
                ]
                consRhs = -2 * bigMx
                consSense = "G"
                addConstraint(model, consCoeff, consVars, consRhs, consSense)

                # 2) j a la derecha de i
                consCoeff = [
                    1.0, -1.0,
                    -1.0, -1.0,
                    -bigMx, -bigMx,
                    -bigMx, -bigMx
                ]
                consVars = [
                    f"cx2_{j}", f"cx2_{i}",
                    f"wEff_{i}", f"wEff_{j}",
                    qij, qji,
                    f"f_{i}", f"f_{j}"
                ]
                consRhs = -4 * bigMx
                consSense = "G"
                addConstraint(model, consCoeff, consVars, consRhs, consSense)

                # 3) i arriba de j
                consCoeff = [
                    1.0, -1.0,
                    -1.0, -1.0,
                    -bigMy, bigMy,
                    -bigMy, -bigMy
                ]
                consVars = [
                    f"cy2_{i}", f"cy2_{j}",
                    f"hEff_{i}", f"hEff_{j}",
                    qij, qji,
                    f"f_{i}", f"f_{j}"
                ]
                consRhs = -3 * bigMy
                consSense = "G"
                addConstraint(model, consCoeff, consVars, consRhs, consSense)

                # 4) j arriba de i
                consCoeff = [
                    1.0, -1.0,
                    -1.0, -1.0,
                    bigMy, -bigMy,
                    -bigMy, -bigMy
                ]
                consVars = [
                    f"cy2_{j}", f"cy2_{i}",
                    f"hEff_{i}", f"hEff_{j}",
                    qij, qji,
                    f"f_{i}", f"f_{j}"
                ]
                consRhs = -3 * bigMy
                consSense = "G"
                addConstraint(model, consCoeff, consVars, consRhs, consSense)

    return model


def solveModel(model, queue, manualInterruption):
    manualInterruption.value = False
    initialTime = time.time()

    try:
        model.solve()
        solverTime = time.time() - initialTime

        status = model.solution.get_status()
        statusString = model.solution.get_status_string(status)

        hasSolution = model.solution.is_primal_feasible()

        if hasSolution:
            objectiveValue = model.solution.get_objective_value()
        else:
            objectiveValue = "n/a"

        print("-------------------------------------------")
        print("Modelo Andrade-Birgin con Big-M")
        print(f"Optimal value: {objectiveValue}")

        # # Podés inspeccionar la solución acá si querés
        # if hasSolution:
        #     for i in ITEMS:
        #         fi = model.solution.get_values(f"f_{i}")
        #         if fi > 0.5:
        #             ri = model.solution.get_values(f"r_{i}")
        #             cx2 = model.solution.get_values(f"cx2_{i}")
        #             cy2 = model.solution.get_values(f"cy2_{i}")
        #             wEff = model.solution.get_values(f"wEff_{i}")
        #             hEff = model.solution.get_values(f"hEff_{i}")
        #             print(
        #                 f"item {i}: used={fi}, rot={ri}, "
        #                 f"center=({cx2 / 2.0}, {cy2 / 2.0}), size=({wEff}, {hEff})"
        #             )

        modelStatus = "1"
        solverStatus = "1"

        if status == 105:
            print("The solver stopped because it reached the time limit.")
            modelStatus = "2"

        queue.put({
            "modelStatus": modelStatus,
            "solverStatus": solverStatus,
            "objectiveValue": objectiveValue,
            "solverTime": solverTime
        })

    except CplexSolverError as e:
        solverTime = time.time() - initialTime
        print(f"CplexSolverError: {e}")

        queue.put({
            "modelStatus": "14",
            "solverStatus": "4",
            "objectiveValue": "n/a",
            "solverTime": solverTime
        })


def runModel(createModelFn, solveModelFn, queue, manualInterruption, maxTime):
    try:
        model = createModelFn(maxTime)
        solveModelFn(model, queue, manualInterruption)
    except Exception as e:
        print(f"Error while running model: {e}")
        queue.put({
            "modelStatus": "14",
            "solverStatus": "4",
            "objectiveValue": "n/a",
            "solverTime": maxTime
        })


def executeWithTimeLimit(maxTime):
    global modelStatus, solverStatus, objectiveValue, solverTime
    global excedingLimitTime

    excedingLimitTime = False

    queue = multiprocessing.Queue()
    manualInterruption = multiprocessing.Value('b', True)

    process = multiprocessing.Process(
        target=runModel,
        args=(createModel, solveModel, queue, manualInterruption, maxTime)
    )

    process.start()
    initialTime = time.time()

    while process.is_alive():
        if manualInterruption.value and time.time() - initialTime > maxTime:
            print("Limit time reached. Aborting process.")
            modelStatus = "14"
            solverStatus = "4"
            solverTime = maxTime
            excedingLimitTime = True
            process.terminate()
            process.join()
            break
        time.sleep(0.1)

    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            print(message)
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            objectiveValue = message["objectiveValue"]
            solverTime = message["solverTime"]

    if excedingLimitTime:
        print("El modelo excedió el tiempo límite de ejecución.")
        objectiveValue = "n/a"
        modelStatus = "14"

    return CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime