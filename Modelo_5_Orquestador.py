import math
import multiprocessing
import time
from Objetos import Rebanada
from Objetos import Item
from Modelo_5_Propio_Maestro import * 
from Modelo_5_Propio_Esclavo_Alternativo import * 

# Parámetros iniciales TODO: ver donde reubicar esto (otro archivo?)
numItems = 5  # Número de ítems en el problema
altoBin = 10  # Altura total del bin
anchoBin = 5  # Ancho total del bin
numRebanadas = 3  # Número de rebanadas a generar
altoItem=2
anchoItem=2 
posXY_x={} #TODO: realizar llamado al generador de posiciones 
posXY_y={} #TODO: realizar llamado al generador de posiciones

def generarListaItems(numItems,altoItem,anchoItem):
    listaItems=[]
    for _ in range(numItems):
        listaItems.append(Item(alto=altoItem, ancho=anchoItem))
    return listaItems

#TODO: corregir esto. Ubicar items en otro lado
items= generarListaItems(numItems,altoItem,anchoItem)

def generarRebanadas(altoBin, anchoBin, nRebanadas):
    # tener en cuenta que en caso de haber remanente en la division, eso no se aprovecha en el bin (TODO: POSIBLE MEJORA)
    altoRebanada = math.floor(altoBin / nRebanadas)  # Redondea hacia abajo
    rebanadas = []

    for _ in range(nRebanadas):
        rebanada = Rebanada(
            alto=altoRebanada,
            ancho=anchoBin,  # Ancho constante para cada rebanada
            items=[],  # Inicialmente vacía
            posicionesOcupadas=[]
        )
        rebanadas.append(rebanada)

    return rebanadas


# Orquestador principal
def orquestador(queue,manualInterruption,maxTime):
    rebanadas = generarRebanadas(altoBin,anchoBin,numRebanadas)  # Inicialización con rebanadas básicas

    while True:
        # Creo modelo
        #TODO: Aca podria mejorar evitando la creacion del modelo en cada vuelta.
        # En su lugar, podria crear uno y luego agregar las columnas (rebanadas) nuevas
        
        masterModel = createMasterModel(maxTime,rebanadas,altoBin,anchoBin,altoItem,anchoItem,items, posXY_x, posXY_y)
        # Resolver modelo maestro
        _ , precios_duales = solveMasterModel(masterModel, queue, manualInterruption)
        print(f"Precios duales: {precios_duales}")
        
        # Crear modelo esclavo
        #TODO: Revisar si el formato de precios_duales es el que manejo en el esclavo al realizar las pruebas
        slaveModel= createSlaveModel(maxTime,posXY_x,posXY_y,items,precios_duales)
        # Resolver modelo esclavo
        #TODO: REVISAR ESTO DE LA NUEVA REBANADA (26/12/2024)
        nueva_rebanada = solveMasterModel(slaveModel,queue, manualInterruption)
        
        if nueva_rebanada is None:
            print("No se encontraron nuevas rebanadas. Fin de la generación de columnas.")
            break
        
        # Agregar nueva rebanada al maestro
        print(f"Nueva rebanada encontrada: {nueva_rebanada}")
        rebanadas.append(nueva_rebanada)
        iteracion += 1
    
    print("Resolviendo modelo maestro final...")
    solucion_final, _ = resolverModeloMaestro(rebanadas)
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