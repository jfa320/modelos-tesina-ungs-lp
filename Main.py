import argparse

import Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION
import Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION
import Modelo_5_Orquestador
import Modelo_6_Andrade_Birgin_Monoitem
import Modelo_7_Backtracking_Monoitem_Exacto
from Config import DEFAULT_CASE_NAME, get_instance, list_instance_names
from TraceFileGenerator import TraceFileGenerator


DEFAULT_EXECUTION_TIME = 1200  # tiempo de ejecucion en segundos para cada modelo - se puede cambiar via parametro de linea de comando

MODELS = [
    Modelo_5_Orquestador,
    Modelo_1_simplificado__seccion_2_8_overleaf_SIN_ROTACION,
    Modelo_1_simplificado__seccion_2_9_overleaf_CON_ROTACION,
    Modelo_6_Andrade_Birgin_Monoitem,
    Modelo_7_Backtracking_Monoitem_Exacto,
]


def parse_args():
    parser = argparse.ArgumentParser(description="Ejecuta modelos sobre una o varias instancias.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--case", default=DEFAULT_CASE_NAME, help="Instancia a ejecutar.")
    group.add_argument("--cases", nargs="+", help="Instancias a ejecutar.")
    group.add_argument("--all", action="store_true", help="Ejecuta todas las instancias configuradas.")
    parser.add_argument("--time", type=int, default=DEFAULT_EXECUTION_TIME, help="Tiempo limite por modelo en segundos.")
    parser.add_argument("--output", default="output.trc", help="Nombre del archivo .trc dentro de Resultados.")
    return parser.parse_args()


def selected_case_names(args):
    if args.all:
        return list_instance_names()
    if args.cases:
        return args.cases
    return [args.case]


def main():
    args = parse_args()
    generator = TraceFileGenerator(args.output)

    for case_name in selected_case_names(args):
        instance = get_instance(case_name)
        print(
            f"Ejecutando {instance['case_name']}: "
            f"bin=({instance['bin_width']},{instance['bin_height']}), "
            f"item=({instance['item_width']},{instance['item_height']})"
        )

        for model in MODELS:
            print(f"Modelo: {model.MODEL_NAME}")
            case_name, model_name, model_status, solver_status, objective_value, solver_time = model.execute_with_time_limit(
                args.time,
                instance,
            )
            generator.write_trace_record(case_name, model_name, model_status, solver_status, objective_value, solver_time)


if __name__ == '__main__':
    main()
