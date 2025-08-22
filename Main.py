import Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION 
import Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION 
import Modelo_2_simplificado__seccion_3_3_overleaf_SIN_ROTACION
import Modelo_2_simplificado__seccion_3_4_overleaf_CON_ROTACION
import Modelo_3_simplificado__seccion_3_5_SIN_ROTACION
import Modelo_3_simplificado__seccion_3_6_CON_ROTACION
import Modelo_5_Orquestador

from TraceFileGenerator import TraceFileGenerator

#Setear caso a probar en archivo Config.py

if __name__ == '__main__':
    EXECUTION_TIME = 100 # tiempo de ejecución en segundos para cada modelo
    generator = TraceFileGenerator("output.trc")
    
    # models = [
    #     Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION,
    #     Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION,
    #     Modelo_2_simplificado__seccion_3_3_overleaf_SIN_ROTACION,
    #     Modelo_2_simplificado__seccion_3_4_overleaf_CON_ROTACION,
    #     Modelo_3_simplificado__seccion_3_5_SIN_ROTACION,
    #     Modelo_3_simplificado__seccion_3_6_CON_ROTACION,
    # ]
    
    # models = [
    #     Modelo_5_Orquestador
    # ]
    
    models = [
        Modelo_5_Orquestador,
        Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION,
        Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION
    ]
    
    for model in models:
        CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime = model.executeWithTimeLimit(EXECUTION_TIME)
        generator.writeTraceRecord(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)