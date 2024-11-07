import Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION 
import Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION 
import Modelo_2_simplificado__seccion_3_3_overleaf_SIN_ROTACION
import Modelo_2_simplificado__seccion_3_4_overleaf_CON_ROTACION
import Modelo_3_simplificado__seccion_3_5_SIN_ROTACION
import Modelo_3_simplificado__seccion_3_6_CON_ROTACION

from TraceFileGenerator import TraceFileGenerator

if __name__ == '__main__':
    EXECUTION_TIME=2
    generator = TraceFileGenerator("output.trc")
    
    CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime=Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION.executeWithTimeLimit(EXECUTION_TIME)
    generator.writeTraceRecord(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)
    CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime=Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION.executeWithTimeLimit(EXECUTION_TIME)
    generator.writeTraceRecord(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)
    CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime=Modelo_2_simplificado__seccion_3_3_overleaf_SIN_ROTACION.executeWithTimeLimit(EXECUTION_TIME)
    generator.writeTraceRecord(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)
    CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime=Modelo_2_simplificado__seccion_3_4_overleaf_CON_ROTACION.executeWithTimeLimit(EXECUTION_TIME)
    generator.writeTraceRecord(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)
    CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime=Modelo_3_simplificado__seccion_3_5_SIN_ROTACION.executeWithTimeLimit(EXECUTION_TIME)
    generator.writeTraceRecord(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)
    CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime=Modelo_3_simplificado__seccion_3_6_CON_ROTACION.executeWithTimeLimit(EXECUTION_TIME)
    generator.writeTraceRecord(CASE_NAME, MODEL_NAME, modelStatus, solverStatus, objectiveValue, solverTime)
    