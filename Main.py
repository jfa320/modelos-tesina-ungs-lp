import Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION 
import Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION 

if __name__ == '__main__':
    EXECUTION_TIME=2
    CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime=Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION.executeWithTimeLimit(EXECUTION_TIME)
    
    CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime=Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION.executeWithTimeLimit(EXECUTION_TIME)
    