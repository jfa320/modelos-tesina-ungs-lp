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

# Orquestador principal
def orquestador(queue,manualInterruption,maxTime,initialTime,configData):
    MAX_ITERACIONES = 30
    Rebanada.resetIdCounter()

    binWidth = configData.getBinWidth()
    binHeight = configData.getBinHeight()  
    itemWidth = configData.getItemWidth()
    itemHeight = configData.getItemHeight()
    itemsQuantity = configData.getItemsQuantity()

    posXY_x, posXY_y=generatePositionsXYM(binWidth,binHeight, itemWidth, itemHeight)

    items=generarListaItems(itemsQuantity,itemHeight,itemWidth)


    rebanadas= generarRebanadasIniciales(binWidth, binHeight, itemWidth, itemHeight,posXY_x,posXY_y, itemsQuantity)  
    rebanadasIniciales=rebanadas.copy()
    
    iteracion = 0
    # print(f"Rebanadas iniciales: {rebanadas}")
    print(f"posXY_x: {posXY_x}")
    print(f"posXY_y: {posXY_y}")
    print("----------------------------------")
    
    while True:
        # Creo modelo
        #TODO: Aca podria mejorar evitando la creacion del modelo en cada vuelta.
        # En su lugar, podria crear uno y luego agregar las columnas (rebanadas) nuevas
        
        masterModel = createMasterModel(maxTime,rebanadas,binHeight,binWidth,itemHeight,itemWidth,items, posXY_x, posXY_y)
        # Resolver modelo maestro
        _ , precios_duales = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=True, items=items, posXY_x=posXY_x, posXY_y= posXY_y,initialTime=initialTime)
        print(f"Precios duales: {precios_duales}")
        # Crear modelo esclavo
        slaveModel= createSlaveModel(maxTime,posXY_x,posXY_y,items,precios_duales, binWidth,itemHeight,itemWidth,binHeight)
        # # Resolver modelo esclavo
        nueva_rebanada,dual_value = solveSlaveModel(slaveModel,queue,manualInterruption,binWidth,itemHeight,itemWidth)
        
        if nueva_rebanada is None:
            print("El esclavo no generó ninguna rebanada.")
            break
        
        # c_r = cantidad de ítems de la rebanada
        c_r = len(nueva_rebanada.getItems())
        reducedCost = dual_value 
        print(f"Valor objetivo del esclavo (reduced cost) = {dual_value}")
        print(f"c_r (#items) = {c_r}")
        print(f"Costo reducido = {reducedCost}")

        if reducedCost <= EPS:
            print("No existe ninguna columna con costo reducido positivo.")
            break

        rebanadas.append(nueva_rebanada)        
        iteracion += 1
        if iteracion >= MAX_ITERACIONES:
            print("Se alcanzó el máximo de iteraciones. Corte preventivo.")
            break
    
    print("Resolviendo modelo maestro final...")
    # print(f"Rebanadas iniciales: {rebanadasIniciales}")
    print(f"posXY_x: {posXY_x}")
    print(f"posXY_y: {posXY_y}")
    masterModel = createMasterModel(maxTime,rebanadas,binHeight,binWidth,itemHeight,itemWidth,items, posXY_x, posXY_y)
    objectiveValue, _ = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=False, items=items, posXY_x=posXY_x, posXY_y= posXY_y,initialTime=initialTime)
    return objectiveValue

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
    if(excedingLimitTime):
        print("El modelo excedió el tiempo límite de ejecución.")
        objectiveValue = "n/a"
        modelStatus = "14" 
    
        
    return CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime