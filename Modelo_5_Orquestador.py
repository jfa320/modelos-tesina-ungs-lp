import math
import multiprocessing
import time
from Objetos import Rebanada
from Objetos import Item

from Position_generator import generatePositionsXY
from Modelo_5_Propio_Maestro import * 
from Modelo_5_Propio_Esclavo_Alternativo import * 

# TODO: Parámetros iniciales, ver donde reubicar esto (otro archivo?)
numItems = 6  # Número de ítems en el problema
altoBin = 4  # Altura total del bin
anchoBin = 6  # Ancho total del bin
altoItem=3
anchoItem=2 
numRebanadas = 4  # Número de rebanadas a generar # TODO: ver esto, esta muy hardcoded
posXY_x, posXY_y=generatePositionsXY(anchoBin,altoBin, anchoItem, altoItem)

#TODO: corregir esto. Ubicar items en otro lado
def generarListaItems(numItems, altoItem, anchoItem):
    return [Item(alto=altoItem, ancho=anchoItem) for _ in range(numItems)]

items=generarListaItems(numItems,altoItem,anchoItem)

def generarRebanadasIniciales(altoBin, anchoBin, nRebanadas, items):
    # TODO: POSIBLE MEJORA, tener en cuenta que en caso de haber remanente en la division, eso no se aprovecha en el bin ()
    altoRebanada = math.floor(altoBin / nRebanadas)  # Redondea hacia abajo
    rebanadas = []

    for i in range(nRebanadas):
        rebanada = Rebanada(
            alto=altoRebanada,
            ancho=anchoBin,  # Ancho constante para cada rebanada
            items=[],  # Inicialmente vacía
            posicionesOcupadas=[]
        )
        
        # Agregar un ítem si está disponible
        if i < len(items):  # Verificar si hay ítems restantes
            item = items[i]
            rebanada.appendItem(item)  
            rebanada.appendPosicionOcupada((0, 0))  
        
        rebanadas.append(rebanada)

    return rebanadas

# Orquestador principal
def orquestador(queue,manualInterruption,maxTime):
    rebanadas = generarRebanadasIniciales(altoBin,anchoBin,numRebanadas,items)  # Inicialización con rebanadas básicas

    while True:
        # Creo modelo
        #TODO: Aca podria mejorar evitando la creacion del modelo en cada vuelta.
        # En su lugar, podria crear uno y luego agregar las columnas (rebanadas) nuevas
        
        masterModel = createMasterModel(maxTime,rebanadas,altoBin,anchoBin,altoItem,anchoItem,items, posXY_x, posXY_y)
        # Resolver modelo maestro
        _ , precios_duales = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=True, items=items, posXY_x=posXY_x, posXY_y= posXY_y)
        print(f"Precios duales: {precios_duales}")
        #TODO: borrar este hardcodeo
        # precios_duales=[2.0, 1.0]
        # print(f"Precios duales hard: {precios_duales}")
        # Crear modelo esclavo
        #TODO: Revisar si el formato de precios_duales es el que manejo en el esclavo al realizar las pruebas
        slaveModel= createSlaveModel(maxTime,posXY_x,posXY_y,items,precios_duales)
        # Resolver modelo esclavo
        nueva_rebanada = solveSlaveModel(slaveModel,queue,manualInterruption,anchoBin,altoItem,anchoItem)
        
        if nueva_rebanada is None:
            print("No se encontraron nuevas rebanadas. Fin de la generación de columnas.")
            break
        
        # Agregar nueva rebanada al maestro
        print(f"Nueva rebanada encontrada: {nueva_rebanada}")
        rebanadas.append(nueva_rebanada)
    
    print("Resolviendo modelo maestro final...")
    solucion_final, _ =  solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=True, items=items, posXY_x=posXY_x, posXY_y= posXY_y)
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
            print(message)
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            objectiveValue = message["objectiveValue"]
            solverTime = message["solverTime"]
    return CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime