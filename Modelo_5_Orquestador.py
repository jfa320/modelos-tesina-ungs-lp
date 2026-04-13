import multiprocessing
import os
import time
from Objetos import Rebanada
from Objetos import Item

from Position_generator import generatePositionsXYM
from Modelo_5_Propio_Maestro import * 
from Modelo_5_Propio_Esclavo_Alternativo import * 
from Config import *
from Utils.visualizacion_bin import exportar_solucion_bin_a_png

from Objetos.ConfigData import ConfigData

MODEL_NAME = "Model5Orchestrator"


#TODO: corregir esto. Ubicar items en otro lado
def generarListaItems(ITEMS_QUANTITY, ITEM_HEIGHT, ITEM_WIDTH):
    return [Item(alto=ITEM_HEIGHT, ancho=ITEM_WIDTH) for _ in range(ITEMS_QUANTITY)]

EPS = 1e-9  # tolerancia numérica

EPS_MASTER = 1e-4
MAX_ESTANCAMIENTO = 5
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


def obtenerRebanadasActivas(rebanadas, variablesActivasMaestro):
    idsActivos = set()

    for nombreVariable in variablesActivasMaestro:
        if not nombreVariable.startswith("p_"):
            continue
        idsActivos.add(int(nombreVariable.split("_")[1]))

    return [rebanada for rebanada in rebanadas if rebanada.getId() in idsActivos]


def exportarLayoutFinal(binWidth, binHeight, itemWidth, itemHeight, itemsQuantity, rebanadasActivas):
    outputPath = os.path.join("Resultados", f"{CASE_NAME}_layout.png")
    exportar_solucion_bin_a_png(binWidth, binHeight, itemWidth, itemHeight, itemsQuantity, rebanadasActivas, outputPath)
    print(f"Layout final exportado en: {outputPath}")


# Orquestador principal
def orquestador(queue,manualInterruption,maxTime,initialTime,configData):
    try:
        # Reiniciar el contador de IDs de Rebanada para cada ejecución
        Rebanada.resetIdCounter()
        iteracionesSinMejora = 0

        # Seteo configuraciones en base a los datos recibidos en configData
        binWidth = configData.getBinWidth()
        binHeight = configData.getBinHeight()  
        itemWidth = configData.getItemWidth()
        itemHeight = configData.getItemHeight()
        itemsQuantity = configData.getItemsQuantity()

        # Genero posiciones a usar en el bin 
        posXY_x, posXY_y=generatePositionsXYM(binWidth,binHeight, itemWidth, itemHeight)
        
        # Creo items a ubicar en los bins (sin posicion ni orientacion definida, eso lo decide el modelo)
        items=generarListaItems(itemsQuantity,itemHeight,itemWidth)

        # Genero rebanadas iniciales a partir de las posiciones generadas y la info de los items
        rebanadas= generarRebanadasIniciales(binWidth, binHeight, itemWidth, itemHeight,posXY_x,posXY_y, itemsQuantity)  
        
        iteracion = 0

        # Construyo firma de rebanadas iniciales para evitar que se generen nuevamente en alguna iteracion
        firmasGeneradas = {construirFirmaRebanada(r) for r in rebanadas}
        objectiveMasterAnterior = None

        while True:
            #TODO: Aca podria mejorar evitando la creacion del modelo en cada vuelta.
            # En su lugar, podria crear uno y luego agregar las columnas (rebanadas) nuevas

            masterModel = createMasterModel(maxTime,rebanadas,binHeight,binWidth,itemHeight,itemWidth,items, posXY_x, posXY_y)
            # Resolver modelo maestro
            objectiveMaster , precios_duales, _ = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=True, initialTime=initialTime)

            if objectiveMasterAnterior is None:
                print("FO maestro relajado anterior: None (primera iteración)")
            else:
                mejoraMaster = objectiveMaster - objectiveMasterAnterior

            slaveModel= createSlaveModel(maxTime,posXY_x,posXY_y,precios_duales, binWidth,itemHeight,itemWidth,binHeight)
            nueva_rebanada, objectiveValueSlaveModel, variablesActivas  = solveSlaveModel(slaveModel,queue,manualInterruption,binWidth,itemHeight,itemWidth)

            esDuplicada = False
            
            # validacion de duplicados solo si se genero una nueva rebanada
            if(nueva_rebanada is not None):
                firma = construirFirmaRebanada(nueva_rebanada)
                esDuplicada = firma in firmasGeneradas

            # Si el esclavo no devolvió una solución factible, corto el proceso
            if objectiveValueSlaveModel is None:
                print("El esclavo no devolvió una solución factible. CORTE.")
                break
            
            # Si la FO del esclavo es menor o igual a EPS, se considera que no hay mejora significativa pero aun no se cierra el proceso, 
            # sino que se generan algunas adicionales  
            if objectiveValueSlaveModel <= EPS:
                solucionesExcluidas = []
                
                # excluyo la solución actual del esclavo para forzar la generación de una nueva rebanada en la próxima iteración
                if variablesActivas:
                    solucionesExcluidas.append(variablesActivas)

                # inicio el proceso de generacion de nuevas rebanadas, realizado MAX_EXTRA iteraciones 
                # o hasta que ocurra algun corte 
                for _ in range(MAX_EXTRA):
                    slaveModel = createSlaveModel(
                        maxTime,
                        posXY_x,
                        posXY_y,
                        precios_duales,
                        binWidth,
                        itemHeight,
                        itemWidth,
                        binHeight
                    )

                    # obligo al modelo a generar rebanadas con al menos 1 item (no quiero triviales)
                    agregarRestriccionNoVacia(slaveModel)

                    # obligo al modelo a que no me devuelva la misma rebanada anterior
                    # evitando que se activen las mismas variables que en la solución anterior del esclavo
                    for i, activas in enumerate(solucionesExcluidas):
                        agregarNoGoodCut(slaveModel, activas, i)

                    # resuelvo el modelo esclavo modificado
                    nuevaRebanadaExtra, objectiveValueExtra, variablesActivasExtra = solveSlaveModel(
                        slaveModel,
                        queue,
                        manualInterruption,
                        binWidth,
                        itemHeight,
                        itemWidth
                    )
                    
                    # Si el esclavo no devolvió una solución factible, corto la generación de rebanadas extra
                    if objectiveValueExtra is None:
                        break
                    
                    # Si el valor objetivo es claramente negativo, no conviene agregar la rebanada
                    if objectiveValueExtra < -EPS:
                        print("[EXTRA] FO del esclavo < -EPS. No se agrega.")
                        break
                    
                    # Si no se genero ninguna rebanda extra, corto el proceso
                    if nuevaRebanadaExtra is None:
                        print("[EXTRA] No se genero ninguna rebanada. Corte.")
                        break
                    
                    # Si no se genero ninguna variable activa en el esclavo, corto el proceso
                    if not variablesActivasExtra:
                        print("[EXTRA] No hay variables activas. Corte.")
                        break

                    
                    # Construyo firma de la nueva rebanada extra generada para validar duplicados
                    firmaExtra = construirFirmaRebanada(nuevaRebanadaExtra)

                    # Si la firma de la nueva rebanada extra no se ha generado antes, la agrego a la lista de rebanadas y a las firmas generadas
                    if firmaExtra not in firmasGeneradas:
                        rebanadas.append(nuevaRebanadaExtra)
                        firmasGeneradas.add(firmaExtra)

                    # excluyo la solucion actual del esclavo para forzar la generación de una nueva rebanada en la próxima iteración
                    solucionesExcluidas.append(variablesActivasExtra)

                break
            
            # Si la nueva rebanada es duplicada, corto el proceso para evitar ciclos
            if esDuplicada:
                print("Rebanada duplicada detectada. Corte de generación.")
                break

            # Si el esclavo no generó ninguna rebanada, corto el proceso
            if nueva_rebanada is None:
                print("El esclavo no generó ninguna rebanada. CORTE.")
                break
            
            # Agrego la nueva rebanada generada a la lista de rebanadas y su firma al conjunto de firmas generadas
            firmasGeneradas.add(firma)
            rebanadas.append(nueva_rebanada)

            # Actualizo el contador de iteraciones sin mejora del maestro
            if objectiveMasterAnterior is not None:
                mejoraMaster = objectiveMaster - objectiveMasterAnterior
                if abs(mejoraMaster) <= EPS_MASTER:
                    iteracionesSinMejora += 1
                else:
                    iteracionesSinMejora = 0

            # Si el maestro no mejora luego de MAX_ESTANCAMIENTO iteraciones, corto el proceso para evitar estancamiento numérico
            if iteracionesSinMejora >= MAX_ESTANCAMIENTO:
                print("Corte por estancamiento numerico del maestro.")
                break

            # Actualizo el valor de la FO del maestro anterior para la próxima iteración
            objectiveMasterAnterior = objectiveMaster
            iteracion += 1
            
        
        # Resuelvo el modelo maestro final sin relajar para obtener una solución entera factible y su valor objetivo final
        masterModel = createMasterModel(maxTime,rebanadas,binHeight,binWidth,itemHeight,itemWidth,items, posXY_x, posXY_y)
        objectiveValueSlaveModel, _, variablesActivasMaestro = solveMasterModel(masterModel, queue, manualInterruption, relajarModelo=False, initialTime=initialTime)
        # Genero png con layout final solo con las rebanadas activas en la solución final del maestro
        rebanadasActivas = obtenerRebanadasActivas(rebanadas, variablesActivasMaestro)
        if rebanadasActivas:
            exportarLayoutFinal(binWidth, binHeight, itemWidth, itemHeight, itemsQuantity, rebanadasActivas)
        else:
            print("No se generó ninguna rebanada activa en la solución final del maestro. No se exporta layout.")
        # Devuelvo resultado
        return objectiveValueSlaveModel
    
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
