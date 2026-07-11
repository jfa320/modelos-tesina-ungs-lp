import Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION 
import Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION 
import Modelo_5_Orquestador

import Modelo_6_Andrade_Birgin_Monoitem
import Modelo_7_Backtracking_Monoitem_Exacto

from TraceFileGenerator import TraceFileGenerator

#Setear caso a probar en archivo Config.py
if __name__ == '__main__':
    EXECUTION_TIME = 1200 # tiempo de ejecución en segundos para cada modelo (20 minutos)
    generator = TraceFileGenerator("output.trc")
    
    models = [
        Modelo_5_Orquestador,
        Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION,
        Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION,
        Modelo_6_Andrade_Birgin_Monoitem,
        Modelo_7_Backtracking_Monoitem_Exacto
    ]
    
    for model in models:
        case_name, model_name, model_status, solver_status, objective_value, solver_time = model.execute_with_time_limit(EXECUTION_TIME)
        generator.write_trace_record(case_name, model_name, model_status, solver_status, objective_value, solver_time)
