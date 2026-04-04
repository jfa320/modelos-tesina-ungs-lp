import multiprocessing
import time
from Objetos import Rebanada
from Objetos import Item

from Position_generator import generatePositionsXYM
from Modelo_5_Propio_Maestro import * 
from Modelo_5_Propio_Esclavo_Alternativo import * 
from Config import *

from Objetos.ConfigData import ConfigData


#TODO: corregir esto. Ubicar items en otro lado
def generarListaItems(ITEMS_QUANTITY, ITEM_HEIGHT, ITEM_WIDTH):
    return [Item(alto=ITEM_HEIGHT, ancho=ITEM_WIDTH) for _ in range(ITEMS_QUANTITY)]

EPS = 1e-9  # tolerancia numérica

EPS_MASTER = 1e-4
MAX_ESTANCAMIENTO = 3
MAX_EXTRA = 5


def generarRebanadasIniciales(binWidth, binHeight,
                              itemWidth, itemHeight,
                              posXY_x, posXY_y,
                              maxItems):

    def generarPorOrientacion(posiciones, w, h, rotado):
        rebanadas = []
        itemsColocados = 0

        posicionesSet = set(posiciones)

        # Agrupar posiciones por fila (y)
        posicionesPorFila = {}
        for (x, y) in posiciones:
            posicionesPorFila.setdefault(y, []).append(x)

        for y in sorted(posicionesPorFila.keys()):
            if itemsColocados >= maxItems:
                break

            rebanada = Rebanada(alto=binHeight, ancho=binWidth)
            ocupadas = set()
            x = 0

            # Recorremos TODO el ancho del bin
            while x + w <= binWidth:
                if itemsColocados >= maxItems:
                    break

                # Región ocupada por el ítem
                region = {(x + dx, y + dy)
                          for dx in range(w)
                          for dy in range(h)}

                # Evitar solapamiento dentro de la rebanada
                if region & ocupadas:
                    x += 1
                    continue

                # Validar SOLO el punto de inicio
                if (x, y) in posicionesSet:
                    item = Item(alto=h, ancho=w, rotado=rotado)
                    rebanada.colocarItem(item, x, y)
                    ocupadas |= region
                    itemsColocados += 1

                    # salto exacto del ancho del ítem
                    x += w
                else:
                    x += 1

            if rebanada.getPuntosDeInicioItems():
                rebanadas.append(rebanada)
                itemsColocados = 0  # mantenemos tu semántica original

        return rebanadas

    # Generar rebanadas no rotadas
    rebanadasNoRotadas = generarPorOrientacion(
        posXY_x, itemWidth, itemHeight, rotado=False
    )

    # Generar rebanadas rotadas
    rebanadasRotadas = generarPorOrientacion(
        posXY_y, itemHeight, itemWidth, rotado=True
    )

    return rebanadasNoRotadas + rebanadasRotadas

def construirFirmaRebanada(rebanada):
    return tuple(sorted((item.getPosicionX(), item.getPosicionY(), item.getRotado()) for item in rebanada.getItems()))

def resumirRebanada(rebanada):
    return sorted((item.getPosicionX(), item.getPosicionY(), item.getRotado()) for item in rebanada.getItems())

def extraerDualesNoNulos(precios_duales, tol=1e-9):
    dualesNoNulos = {}
    for clave, valor in precios_duales.get("pi", {}).items():
        if abs(valor) > tol:
            dualesNoNulos[clave] = valor
    return dualesNoNulos

def calcularReducedCostReal(rebanada, preciosDuales, w, h):
    sumaDuales = 0.0
    
    if(rebanada is None):
        return 0.0, 0, 0.0
    for item in rebanada.getItems():
        x = item.getPosicionX()
        y = item.getPosicionY()
        rotado = item.getRotado()

        ancho = h if rotado else w
        alto = w if rotado else h

        for dx in range(ancho):
            for dy in range(alto):
                clave = f"({x+dx},{y+dy})"
                sumaDuales += preciosDuales["pi"].get(clave, 0.0)

    c_r = len(rebanada.getItems())
    reducedCostReal = c_r - sumaDuales

    return reducedCostReal, c_r, sumaDuales


def agregarNoGoodCut(slaveModel, variablesActivas, cutId):
    if not variablesActivas:
        return

    addConstraint(
        slaveModel,
        [1.0] * len(variablesActivas),
        variablesActivas,
        len(variablesActivas) - 1,
        "L",
        f"nogood_{cutId}"
    )

def agregarRestriccionNoVacia(slaveModel):
    nombres = []
    valores = []

    for nombre in slaveModel.variables.get_names():
        if nombre.startswith("z_x_") or nombre.startswith("z_y_"):
            nombres.append(nombre)
            valores.append(1.0)

    if not nombres:
        return

    addConstraint(
        slaveModel,
        valores,
        nombres,
        1.0,
        "G",
        f"non_empty_{slaveModel.linear_constraints.get_num()}"
    )


# Orquestador principal
def orquestador(queue,manualInterruption,maxTime,initialTime,configData):
    try:
        Rebanada.resetIdCounter()
        iteracionesSinMejora = 0

        binWidth = configData.getBinWidth()
        binHeight = configData.getBinHeight()  
        itemWidth = configData.getItemWidth()
        itemHeight = configData.getItemHeight()
        itemsQuantity = configData.getItemsQuantity()

        posXY_x, posXY_y=generatePositionsXYM(binWidth,binHeight, itemWidth, itemHeight)

        items=generarListaItems(itemsQuantity,itemHeight,itemWidth)


        rebanadas= generarRebanadasIniciales(binWidth, binHeight, itemWidth, itemHeight,posXY_x,posXY_y, itemsQuantity)  
        
        iteracion = 0

        firmasGeneradas = {construirFirmaRebanada(r) for r in rebanadas}
        objectiveMasterAnterior = None

        while True:
            #TODO: Aca podria mejorar evitando la creacion del modelo en cada vuelta.
            # En su lugar, podria crear uno y luego agregar las columnas (rebanadas) nuevas

            masterModel = createMasterModel(maxTime,rebanadas,binHeight,binWidth,itemHeight,itemWidth,items, posXY_x, posXY_y)
            # Resolver modelo maestro
            objectiveMaster , precios_duales = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=True, initialTime=initialTime)

            if objectiveMasterAnterior is None:
                print("FO maestro relajado anterior: None (primera iteración)")
            else:
                mejoraMaster = objectiveMaster - objectiveMasterAnterior

            slaveModel= createSlaveModel(maxTime,posXY_x,posXY_y,items,precios_duales, binWidth,itemHeight,itemWidth,binHeight)
            nueva_rebanada,dual_value, variablesActivas  = solveSlaveModel(slaveModel,queue,manualInterruption,binWidth,itemHeight,itemWidth)

            esDuplicada = False
            
            if(nueva_rebanada is not None):
                firma = construirFirmaRebanada(nueva_rebanada)
                esDuplicada = firma in firmasGeneradas
            
            if dual_value is None:
                print("El esclavo no devolvió una solución factible. CORTE.")
                break

            if dual_value <= EPS:
                solucionesExcluidas = []

                if variablesActivas:
                    solucionesExcluidas.append(variablesActivas)


                for _ in range(MAX_EXTRA):
                    slaveModel = createSlaveModel(
                        maxTime,
                        posXY_x,
                        posXY_y,
                        items,
                        precios_duales,
                        binWidth,
                        itemHeight,
                        itemWidth,
                        binHeight
                    )

                    agregarRestriccionNoVacia(slaveModel)

                    for i, activas in enumerate(solucionesExcluidas):
                        agregarNoGoodCut(slaveModel, activas, i)

                    nuevaRebanadaExtra, dualValueExtra, variablesActivasExtra = solveSlaveModel(
                        slaveModel,
                        queue,
                        manualInterruption,
                        binWidth,
                        itemHeight,
                        itemWidth
                    )

                    if dualValueExtra is None:
                        break

                    if dualValueExtra < -EPS:
                        print("[EXTRA] FO <- EPS. No se agrega.")
                        break

                    if nuevaRebanadaExtra is None:
                        print("[EXTRA] No se genero ninguna rebanada. Corte.")
                        break

                    if not variablesActivasExtra:
                        print("[EXTRA] No hay variables activas. Corte.")
                        break

                    

                    firmaExtra = construirFirmaRebanada(nuevaRebanadaExtra)

                    if firmaExtra not in firmasGeneradas:
                        rebanadas.append(nuevaRebanadaExtra)
                        firmasGeneradas.add(firmaExtra)

                    solucionesExcluidas.append(variablesActivasExtra)

                break

            if esDuplicada:
                print("Rebanada duplicada detectada. Corte de generación.")
                break
            
            if nueva_rebanada is None:
                        print("El esclavo no generó ninguna rebanada. CORTE.")
                        break

            firmasGeneradas.add(firma)
            rebanadas.append(nueva_rebanada)

            if objectiveMasterAnterior is not None:
                mejoraMaster = objectiveMaster - objectiveMasterAnterior
                if abs(mejoraMaster) <= EPS_MASTER:
                    iteracionesSinMejora += 1
                else:
                    iteracionesSinMejora = 0

            if iteracionesSinMejora >= MAX_ESTANCAMIENTO:
                print("Corte por estancamiento numerico del maestro.")
                break


            objectiveMasterAnterior = objectiveMaster
            iteracion += 1
            
        

        masterModel = createMasterModel(maxTime,rebanadas,binHeight,binWidth,itemHeight,itemWidth,items, posXY_x, posXY_y)
        objectiveValue, _ = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=False, initialTime=initialTime)
        return objectiveValue
    
    except CplexSolverError as e:
        solverTime = round(time.time() - initialTime, 2)
        handleSolverError(e, queue, solverTime)
        return None

def executeWithTimeLimit(maxTime):
    global modelStatus, solverStatus, objectiveValue, solverTime 
    global excedingLimitTime
    excedingLimitTime=False
    initialTime = time.time()
    

    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    manualInterruption = multiprocessing.Value('b', True)

    configData = ConfigData(
        itemsQuantity=ITEMS_QUANTITY,
        binWidth=BIN_WIDTH,
        binHeight=BIN_HEIGHT,
        itemWidth=ITEM_WIDTH,
        itemHeight=ITEM_HEIGHT
    )

    # Crear el subproceso que correrá la función
    process = multiprocessing.Process(target=orquestador, args=(queue,manualInterruption,maxTime,initialTime,configData))

    # Iniciar el subproceso
    process.start()


    # Monitorear la cola mientras el proceso está en ejecución
    while process.is_alive():
        if manualInterruption.value and time.time() - initialTime > maxTime:
            print("Limit time reached. Aborting process.")
            modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solverStatus="4" #el solver finalizo la ejecucion del modelo
            solverTime=maxTime
            excedingLimitTime=True
            process.terminate()
            process.join()
            break
        time.sleep(0.1)  # Evitar consumir demasiados recursos

    
    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            objectiveValue = message["objectiveValue"]
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            solverTime = message["solverTime"]
            print(f"Optimal value: {objectiveValue}")
            print(message)
    if excedingLimitTime:
        print("El modelo excedió el tiempo límite de ejecución.")
        objectiveValue = "n/a"
        modelStatus = "14" 
    
        
    return CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime
