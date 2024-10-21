from Modelo_4_Propio_Maestro import createAndSolveMasterModel
from Modelo_4_Propio_Esclavo import createAndSolveSlaveModel

if __name__ == '__main__':
    timer=iniciarTimer()
    rutaResultados=""
    
    while(timer<TIEMPO_LIMITE):
    
        rebanadaInicial=obtenerRebanadaInicial()
        dualSol=createAndSolveMasterModel(rebanadaInicial)
        rebanada=createAndSolveSlaveModel(dualSol)
        
        while(rebanada!=0): #Es decir la rebanada tiene potencial de mejora
            addNewVariableNewContraintsMasterModel(rebanada) # esto agregaria la variable de rebanada en el maestro y sus restricciones
            dualSol=solveMasterModel(rebanada) # aca no deberia crear otro modelo, sino agarrar el actual y resolverlo con el agregado del paso previo
            rebanada=createAndSolveSlaveModel(dualSol)
        #aca se resuelve por ultima vez cuando no hay rebanadas con potencial de mejora | ademas devuelvo la ruta con los resultados para cargar en PAVER
        rutaResultados=finalSolveMasterModel(rebanada) 
        break
        
        
    if(timer==TIEMPO_LIMITE):
        print("El programa supero el tiempo, por lo que se anulo la ejecucion") 
    else:
        print("Ver resultados obteneidos en archivo paver: "+rutaResultados)    
    
    
        
        
        

