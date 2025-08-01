import math
import multiprocessing
import time
from Objetos import Rebanada
from Objetos import Item

from Position_generator import generatePositionsXY
from Modelo_5_Propio_Maestro import * 
from Modelo_5_Propio_Esclavo_Alternativo import * 
from Config import *


numRebanadas = math.ceil(BIN_HEIGHT/max(ITEM_WIDTH,ITEM_HEIGHT))  # Número de rebanadas a generar # TODO: ver esto, esta muy hardcoded - aca corregir
posXY_x, posXY_y=generatePositionsXY(BIN_WIDTH,BIN_HEIGHT, ITEM_WIDTH, ITEM_HEIGHT)
altoRebanada = math.ceil(BIN_HEIGHT / numRebanadas)  # Redondea hacia abajo
altoRebanada = 1 if altoRebanada == 0 else altoRebanada
#TODO: corregir esto. Ubicar items en otro lado
def generarListaItems(ITEMS_QUANTITY, ITEM_HEIGHT, ITEM_WIDTH):
    return [Item(alto=ITEM_HEIGHT, ancho=ITEM_WIDTH) for _ in range(ITEMS_QUANTITY)]

items=generarListaItems(ITEMS_QUANTITY,ITEM_HEIGHT,ITEM_WIDTH)

def generarRebanadasIniciales(binHeight, binWidth, itemWidth, itemHeight, posXY_x, posXY_y):
    rebanadas = []
    rebanadaId = 0

    # Agrupar posiciones por coordenada Y para ítems NO rotados
    posicionesPorFila_x = {}
    for (x, y) in posXY_x:
        posicionesPorFila_x.setdefault(y, []).append((x, y))

    for y in sorted(posicionesPorFila_x.keys()):
        rebanada = Rebanada(alto=binHeight, ancho=binWidth)
        ocupadas = set()
        for (x, _) in sorted(posicionesPorFila_x[y]):
            if x + itemWidth <= binWidth:
                region = {(x + dx, y + dy) for dx in range(itemWidth) for dy in range(itemHeight)}
                if not region & ocupadas:
                    item = Item(alto=itemHeight, ancho=itemWidth, rotado=False)
                    rebanada.agregarItem(item, x, y)
                    ocupadas |= region
        if rebanada.getPosicionesOcupadas():
            rebanadas.append(rebanada)
            rebanadaId += 1

    # Agrupar posiciones por coordenada Y para ítems ROTADOS
    posicionesPorFila_y = {}
    for (x, y) in posXY_y:
        posicionesPorFila_y.setdefault(y, []).append((x, y))

    for y in sorted(posicionesPorFila_y.keys()):
        rebanada = Rebanada(alto=binHeight, ancho=binWidth)
        ocupadas = set()
        for (x, _) in sorted(posicionesPorFila_y[y]):
            if x + itemHeight <= binWidth:
                region = {(x + dx, y + dy) for dx in range(itemHeight) for dy in range(itemWidth)}
                if not region & ocupadas:
                    item = Item(alto=itemWidth, ancho=itemHeight, rotado=True)
                    rebanada.agregarItem(item, x, y)
                    ocupadas |= region
        if rebanada.getPosicionesOcupadas():
            rebanadas.append(rebanada)
            rebanadaId += 1

    return rebanadas



def generarRebanadasIniciale08062025(binHeight, binWidth, itemWidth, itemHeight):
    rebanadas = []

    # Rebanadas con ítems NO rotados
    y = 0
    while y + itemHeight <= binHeight:
        x = 0
        rebanadaNoRotada = Rebanada(alto=altoRebanada, ancho=binWidth)

        while x + itemWidth <= binWidth:
            item = Item(alto=itemHeight, ancho=itemWidth, rotado=False)
            rebanadaNoRotada.agregarItem(item, x, y)
            x += itemWidth

        if rebanadaNoRotada.getPosicionesOcupadas():
            rebanadas.append(rebanadaNoRotada)

        y += itemHeight  # Avanza según ítems no rotados

    # Rebanadas con ítems ROTADOS
    y = 0
    while y + itemWidth <= binHeight:
        x = 0
        rebanadaRotada = Rebanada(alto=altoRebanada, ancho=binWidth)

        while x + itemHeight <= binWidth:
            item = Item(alto=itemWidth, ancho=itemHeight, rotado=True)
            rebanadaRotada.agregarItem(item, x, y)
            x += itemHeight

        if rebanadaRotada.getPosicionesOcupadas():
            rebanadas.append(rebanadaRotada)

        y += itemWidth  # Avanza según ítems rotados

    return rebanadas


def generarRebanadasIniciales07062025(binHeight,binWidth, itemWidth, itemHeight):
    rebanadas = []
    y = 0

    while y + itemHeight <= binHeight:
        x = 0
        rebanada = Rebanada(alto=altoRebanada, ancho=binWidth)

        while x + itemWidth <= binWidth:
            item = Item(alto=itemHeight, ancho=itemWidth)
            rebanada.agregarItem(item,x, y)
            x += itemWidth

        if rebanada.getPosicionesOcupadas():
            rebanadas.append(rebanada)
        y += itemHeight
    return rebanadas

def generarRebanadasInicialesB(BIN_HEIGHT, BIN_WIDTH, nRebanadas, items):
    # Este genera rebanadas ubicando solo un item en ellas pero tiene fallos porque a veces genera rebanadas que no respeta dimensiones del bin
    # TODO: POSIBLE MEJORA, tener en cuenta que en caso de haber remanente en la division, eso no se aprovecha en el bin ()
    
    
    
    print(f"altoRebanada: {altoRebanada}")
    rebanadas = []
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


def generarRebanadasInicialesA(binHeight, binWidth, nRebanadas, items):
    import math

    altoRebanada = max(1, math.floor(binHeight / nRebanadas))
    itemIndex = 0
    rebanadas = []

    for r in range(nRebanadas):
        nuevaRebanada = Rebanada(
            alto=altoRebanada,
            ancho=binWidth,
            items=[],
            posicionesOcupadas=[]
        )

        xActual = 0

        while (
            itemIndex < len(items)
            and xActual + items[itemIndex].get_ancho() <= binWidth
            and items[itemIndex].get_alto() <= altoRebanada
        ):
            item = items[itemIndex]
            posicion = (xActual, 0)
            nuevaRebanada.appendItem(item, posicion)
            print(f"Rebanada {r + 1}: colocando Item {item.getId()} en {posicion}")
            xActual += item.get_ancho()
            itemIndex += 1

        if nuevaRebanada.getTotalItems() > 0:
            rebanadas.append(nuevaRebanada)
        else:
            break

    return rebanadas


# Orquestador principal
def orquestador(queue,manualInterruption,maxTime):
    MAX_ITERACIONES = 1
    # rebanadas = generarRebanadasIniciales(BIN_HEIGHT,BIN_WIDTH,numRebanadas,items)  # Inicialización con rebanadas básicas
    rebanadas= generarRebanadasIniciales(BIN_HEIGHT,BIN_WIDTH, ITEM_WIDTH, ITEM_HEIGHT,posXY_x,posXY_y)  # Inicialización con rebanadas básicas
    # itemAux=Item(alto=ITEM_HEIGHT, ancho=ITEM_WIDTH)
    # rebanadaAux=Rebanada(alto=altoRebanada, ancho=BIN_WIDTH, items=[], posicionesOcupadas=[])
    # rebanadaAux.agregarItem(itemAux, 0, 0)  # Agregar un ítem a la rebanada auxiliar
    # rebanadas.append(rebanadaAux)  
    
    # itemAux=Item(alto=ITEM_WIDTH, ancho=ITEM_HEIGHT,rotado=True)
    # rebanadaAux=Rebanada(alto=altoRebanada, ancho=BIN_WIDTH, items=[], posicionesOcupadas=[])
    # rebanadaAux.agregarItem(itemAux, 0, 2)  # Agregar un ítem a la rebanada auxiliar
    # rebanadas.append(rebanadaAux)  

    iteracion = 0
    print(f"Rebanadas iniciales: {rebanadas}")
    print(f"posXY_x: {posXY_x}")
    print(f"posXY_y: {posXY_y}")
    vueltaNro=1
    while True:
        # Creo modelo
        #TODO: Aca podria mejorar evitando la creacion del modelo en cada vuelta.
        # En su lugar, podria crear uno y luego agregar las columnas (rebanadas) nuevas
        masterModel = createMasterModel(maxTime,rebanadas,BIN_HEIGHT,BIN_WIDTH,ITEM_HEIGHT,ITEM_WIDTH,items, posXY_x, posXY_y)
        posicionesBin = set(posXY_x) | set(posXY_y)
        # Resolver modelo maestro
        _ , precios_duales = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=True, items=items, posXY_x=posXY_x, posXY_y= posXY_y)
        print(f"Precios duales: {precios_duales}")
        
        # Crear modelo esclavo
        slaveModel= createSlaveModel(maxTime,posXY_x,posXY_y,items,precios_duales,altoRebanada, BIN_WIDTH,ITEM_HEIGHT,ITEM_WIDTH)
        # Resolver modelo esclavo
        nueva_rebanada = solveSlaveModel(slaveModel,queue,manualInterruption,BIN_WIDTH,ITEM_HEIGHT,ITEM_WIDTH)
        
        if nueva_rebanada is None:
            print("No se encontraron nuevas rebanadas. Fin de la generación de columnas.")
            break
        vueltaNro+=1
        # Agregar nueva rebanada al maestro
        print(f"Nueva rebanada encontrada: {nueva_rebanada}")
        rebanadas.append(nueva_rebanada)
        iteracion += 1

        if iteracion >= MAX_ITERACIONES:
            print("Se alcanzó el máximo de iteraciones. Corte preventivo.")
            break
    
    print("Resolviendo modelo maestro final...")
    masterModel = createMasterModel(maxTime,rebanadas,BIN_HEIGHT,BIN_WIDTH,ITEM_HEIGHT,ITEM_WIDTH,items, posXY_x, posXY_y)
    
    resultado = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=False, items=items, posXY_x=posXY_x, posXY_y= posXY_y)
    if resultado is not None:
        solucion_final, _ = resultado
        print(f"Solución final: {solucion_final}")
    else:
        print("solveMasterModel devolvió None :(")
    


def executeWithTimeLimit(maxTime):
    global modelStatus, solverStatus, objectiveValue, solverTime 
    
    print("ESTO ES MODELO 5 ORQUESTADOR")
    print(f"numRebanadas: {numRebanadas}")
    print(f"BIN_HEIGHT: {BIN_HEIGHT}")
    print(f"BIN_WIDTH: {BIN_WIDTH}")
    print(f"ITEM_WIDTH: {ITEM_WIDTH}")
    print(f"ITEM_HEIGHT: {ITEM_HEIGHT}")  
    print(f"altoRebanada: {altoRebanada}")

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