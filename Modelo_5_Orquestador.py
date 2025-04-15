import math
import multiprocessing
import time
from Objetos import Rebanada
from Objetos import Item

from Position_generator import generatePositionsXY
from Modelo_5_Propio_Maestro import * 
from Modelo_5_Propio_Esclavo_Alternativo import * 
from Config import *


numRebanadas = 3  # Número de rebanadas a generar # TODO: ver esto, esta muy hardcoded - aca corregir
posXY_x, posXY_y=generatePositionsXY(BIN_WIDTH,BIN_HEIGHT, ITEM_WIDTH, ITEM_HEIGHT)
altoRebanada = 0  # Inicializar la altura de la rebanada (se calculará más adelante) 

#TODO: corregir esto. Ubicar items en otro lado
def generarListaItems(ITEMS_QUANTITY, ITEM_HEIGHT, ITEM_WIDTH):
    return [Item(alto=ITEM_HEIGHT, ancho=ITEM_WIDTH) for _ in range(ITEMS_QUANTITY)]

items=generarListaItems(ITEMS_QUANTITY,ITEM_HEIGHT,ITEM_WIDTH)

def generarRebanadasIniciales(BIN_HEIGHT, BIN_WIDTH, nRebanadas, items):
    # TODO: POSIBLE MEJORA, tener en cuenta que en caso de haber remanente en la division, eso no se aprovecha en el bin ()
    altoRebanada = math.floor(BIN_HEIGHT / nRebanadas)  # Redondea hacia abajo
    rebanadas = []
    print(f"BIN_HEIGHT: {BIN_HEIGHT}")
    print(f"nRebanadas: {nRebanadas}")
    print(f"altoRebanada: {altoRebanada}")
    for i in range(nRebanadas):
        rebanada = Rebanada(
            alto=altoRebanada,
            ancho=BIN_WIDTH,  # Ancho constante para cada rebanada
            items=[],  # Inicialmente vacía
            posicionesOcupadas=[]
        )
        
        # Agregar un ítem si está disponible
        if i < len(items):  # Verificar si hay ítems restantes
            item = items[i]
            rebanada.appendItem(item, (0, 0))  
        
        rebanadas.append(rebanada)

    return rebanadas

# Orquestador principal
def orquestador(queue,manualInterruption,maxTime):
    rebanadas = generarRebanadasIniciales(BIN_HEIGHT,BIN_WIDTH,numRebanadas,items)  # Inicialización con rebanadas básicas
    rebanadas[0].appendItem(items[1], (2, 0))
    vueltaNro=1
    while True:
        # Creo modelo
        #TODO: Aca podria mejorar evitando la creacion del modelo en cada vuelta.
        # En su lugar, podria crear uno y luego agregar las columnas (rebanadas) nuevas
        print("rebanadas: ACA:::: ",rebanadas)
        masterModel = createMasterModel(maxTime,rebanadas,BIN_HEIGHT,BIN_WIDTH,ITEM_HEIGHT,ITEM_WIDTH,items, posXY_x, posXY_y)
        posicionesBin = set(posXY_x) | set(posXY_y)
        # Resolver modelo maestro
        _ , precios_duales = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=True, items=items, posXY_x=posXY_x, posXY_y= posXY_y)
        print(f"Precios duales: {precios_duales}")
        
        # Crear modelo esclavo
        slaveModel= createSlaveModel(maxTime,posXY_x,posXY_y,items,precios_duales,altoRebanada, BIN_WIDTH,ITEM_HEIGHT,ITEM_WIDTH)
        # Resolver modelo esclavo
        nueva_rebanada = solveSlaveModel(slaveModel,queue,manualInterruption,BIN_WIDTH,ITEM_HEIGHT,ITEM_WIDTH)
        
        print(f"Vuelta Nro: {vueltaNro}")
        if nueva_rebanada is None:
            print("No se encontraron nuevas rebanadas. Fin de la generación de columnas.")
            break
        vueltaNro+=1
        # Agregar nueva rebanada al maestro
        print(f"Nueva rebanada encontrada: {nueva_rebanada}")
        rebanadas.append(nueva_rebanada)
    
    print("Resolviendo modelo maestro final...")
    masterModel = createMasterModel(maxTime,rebanadas,BIN_HEIGHT,BIN_WIDTH,ITEM_HEIGHT,ITEM_WIDTH,items, posXY_x, posXY_y)
    solucion_final, _ =  solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=False, items=items, posXY_x=posXY_x, posXY_y= posXY_y)
    print(f"Solución final: {solucion_final}")


def executeWithTimeLimit(maxTime):
    global modelStatus, solverStatus, objectiveValue, solverTime 
    
    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    manualInterruption = multiprocessing.Value('b', True)

    # Crear el subproceso que correrá la función
    process = multiprocessing.Process(target=orquestador, args=(queue,manualInterruption,maxTime))

    # Iniciar el subproceso
    process.start()

    initialTime = time.time()

    # Monitorear la cola mientras el proceso está en ejecución
    while process.is_alive():
        if manualInterruption.value and time.time() - initialTime > maxTime:
            print("Limit time reached. Aborting process.")
            modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solverStatus="4" #el solver finalizo la ejecucion del modelo
            solverTime=maxTime
            process.terminate()
            process.join()
            break
        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            objectiveValue = message["objectiveValue"]
            solverTime = message["solverTime"]
    return CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime