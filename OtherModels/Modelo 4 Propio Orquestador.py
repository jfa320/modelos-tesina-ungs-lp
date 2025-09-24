from Modelo_4_Propio_Maestro import createAndSolveMasterModel
from Modelo_4_Propio_Esclavo import createAndSolveSlaveModel,findHighestHeight

from Objetos.Rebanada import Rebanada
from Objetos.Item import Item

import multiprocessing
import time

from TraceFileGenerator import TraceFileGenerator

NOMBRE_MODELO="Model4"

modelStatus="1"
solverStatus="1"
objective_value=0
solverTime=1
rutaResultados=""
ALTO_FIJO_REBANADA=2 #Setear segun corresponda        
ANCHO_BIN=5 #Setear segun corresponda
ITEMS_EMPAQUETAR=[Item(alto, posicion_y, rotado) for alto, posicion_y, rotado in [(10, 5, True), (5, 30, False)]]
MAX_SECONDS=5    
    
NOMBRE_CASO="inst2"
    
def obtenerRebanadaInicial(anchoBin,items):
    rebanada=Rebanada()
    auxAncho=0
    itemsRebanada=[]
    for item in items:
        if(auxAncho<=anchoBin):
            auxAncho=auxAncho+item.get_ancho()
            itemsRebanada.append(item)
       
    rebanada.set_items(itemsRebanada)        
    rebanada.set_alto(findHighestHeight(itemsRebanada))
    
    return rebanada        

def ejecutarModelos(interrupcionManual):
    rebanadaInicial=obtenerRebanadaInicial(ANCHO_BIN,ITEMS_EMPAQUETAR)
    dualSol=createAndSolveMasterModel(interrupcionManual,MAX_SECONDS,rebanadaInicial) 
    rebanada=createAndSolveSlaveModel(dualSol)
    
    while(rebanada!=0): #Es decir la rebanada tiene potencial de mejora
        addNewVariableNewContraintsMasterModel(rebanada) # esto agregaria la variable de rebanada en el maestro y sus restricciones
        dualSol=solveMasterModel(rebanada) # aca no deberia crear otro modelo, sino agarrar el actual y resolverlo con el agregado del paso previo
        rebanada=createAndSolveSlaveModel(dualSol)
    #aca se resuelve por ultima vez cuando no hay rebanadas con potencial de mejora | ademas devuelvo la ruta con los resultados para cargar en PAVER
    rutaResultados=finalSolveMasterModel(rebanada)        
     
def executeWithTimeLimit(tiempo_maximo, funcion_a_ejecutar, *args):
    global modelStatus, solverStatus, objective_value, solverTime 

    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    interrupcion_manual = multiprocessing.Value('b', True)

    # Crear el subproceso que correrá la función
    proceso = multiprocessing.Process(target=funcion_a_ejecutar, args=(queue,interrupcion_manual,*args))

    # Iniciar el subproceso
    proceso.start()

    tiempo_inicial = time.time()

    # Monitorear la cola mientras el proceso está en ejecución
    while proceso.is_alive():

        if interrupcion_manual.value:
            # Si se excede el tiempo, terminamos el proceso
            if time.time() - tiempo_inicial > tiempo_maximo:
                print("Tiempo límite alcanzado. Abortando el proceso.")
                modelStatus="14" #valor en paver para marcar que el modelo no devolvio respuesta por error
                solverStatus="4" #el solver finalizo la ejecucion del modelo
                solverTime=tiempo_maximo
                proceso.terminate()
                proceso.join()
                break
        else:
            # Si el subproceso ha terminado antes de alcanzar el tiempo límite
            proceso_exitoso = True        
        time.sleep(0.1)  # Evitar consumir demasiados recursos

    if proceso_exitoso:
        print("Ejecución exitosa. Ver resultados obtenidos en archivo paver: "+rutaResultados)    
        
    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            print(message)
            modelStatus = message["modelStatus"]
            solverStatus = message["solverStatus"]
            objective_value = message["objective_value"]
            solverTime = message["solverTime"]
            

if __name__ == '__main__':
    
    executeWithTimeLimit(MAX_SECONDS,ejecutarModelos)
    generator = TraceFileGenerator("output.trc")
    generator.write_trace_record(NOMBRE_CASO, NOMBRE_MODELO, modelStatus, solverStatus, objective_value, solverTime)