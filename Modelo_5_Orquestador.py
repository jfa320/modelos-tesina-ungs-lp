import multiprocessing
import os
import math
import time
from Objetos import Rebanada
from Objetos import Item

from Position_generator import generate_positions_xym2
from Modelo_5_Propio_Maestro import * 
from Modelo_5_Propio_Esclavo_Alternativo import * 
from Config import *
from Utils.visualizacion_bin import exportar_solucion_bin_a_png

from Objetos.ConfigData import ConfigData

MODEL_NAME = "Model5Orchestrator"

EPS = 1e-9  # tolerancia numérica

EPS_MASTER = 1e-4
MAX_ESTANCAMIENTO = 5
MAX_EXTRA = 5


def calcular_alto_rebanada(bin_width, bin_height, item_width, item_height, porcentaje=0.05):
    cota_maxima = math.floor((bin_height * bin_width) / (item_height * item_width))
    items_objetivo = math.ceil(cota_maxima * porcentaje)

    items_por_fila_normal = math.floor(bin_width / item_width)
    filas_normal = math.ceil(items_objetivo / items_por_fila_normal)
    alto_normal = filas_normal * item_height

    items_por_fila_rotado = math.floor(bin_width / item_height)
    filas_rotado = math.ceil(items_objetivo / items_por_fila_rotado)
    alto_rotado = filas_rotado * item_width

    return min(alto_normal, alto_rotado)

def calcular_cota_fisica_items(bin_width, bin_height, item_width, item_height):
    return math.floor((bin_width * bin_height) / (item_width * item_height))


def generar_rebanadas_iniciales(bin_width, bin_height,
                                item_width, item_height,
                                pos_xy_x, pos_xy_y,
                                max_items):

    alto_rebanada = calcular_alto_rebanada(bin_width, bin_height, item_width, item_height)

    def generar_por_orientacion(posiciones, w, h, rotado):
        rebanadas = []
        items_colocados = 0

        posiciones_set = set(posiciones)

        # Agrupar posiciones por fila (y)
        posiciones_por_fila = {}
        for (x, y) in posiciones:
            posiciones_por_fila.setdefault(y, []).append(x)

        for y in sorted(posiciones_por_fila.keys()):
            if items_colocados >= max_items:
                break

            rebanada = Rebanada(alto=alto_rebanada, ancho=bin_width)
            ocupadas = set()
            x = 0

            # Recorremos TODO el ancho del bin
            while x + w <= bin_width:
                if items_colocados >= max_items:
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
                if (x, y) in posiciones_set:
                    item = Item(alto=h, ancho=w, rotado=rotado)
                    rebanada.colocar_item(item, x, y)
                    ocupadas |= region
                    items_colocados += 1

                    # salto exacto del ancho del ítem
                    x += w
                else:
                    x += 1

            if rebanada.get_puntos_de_inicio_items():
                rebanadas.append(rebanada)
                items_colocados = 0  # mantenemos tu semántica original

        return rebanadas

    # Generar rebanadas no rotadas
    rebanadas_no_rotadas = generar_por_orientacion(
        pos_xy_x, item_width, item_height, rotado=False
    )

    # Generar rebanadas rotadas
    rebanadas_rotadas = generar_por_orientacion(
        pos_xy_y, item_height, item_width, rotado=True
    )

    return rebanadas_no_rotadas + rebanadas_rotadas

def construir_firma_rebanada(rebanada):
    return tuple(sorted((item.get_posicion_x(), item.get_posicion_y(), item.get_rotado()) for item in rebanada.get_items()))

def resumir_rebanada(rebanada):
    return sorted((item.get_posicion_x(), item.get_posicion_y(), item.get_rotado()) for item in rebanada.get_items())

def extraer_duales_no_nulos(precios_duales, tol=1e-9):
    duales_no_nulos = {}
    for clave, valor in precios_duales.get("pi", {}).items():
        if abs(valor) > tol:
            duales_no_nulos[clave] = valor
    return duales_no_nulos

def calcular_reduced_cost_real(rebanada, precios_duales, w, h):
    suma_duales = 0.0
    
    if(rebanada is None):
        return 0.0, 0, 0.0
    for item in rebanada.get_items():
        x = item.get_posicion_x()
        y = item.get_posicion_y()
        rotado = item.get_rotado()

        ancho = h if rotado else w
        alto = w if rotado else h

        for dx in range(ancho):
            for dy in range(alto):
                clave = f"({x+dx},{y+dy})"
                suma_duales += precios_duales["pi"].get(clave, 0.0)

    c_r = len(rebanada.get_items())
    reduced_cost_real = c_r - suma_duales

    return reduced_cost_real, c_r, suma_duales


def agregar_no_good_cut(slave_model, variables_activas, cut_id):
    if not variables_activas:
        return

    add_constraint(
        slave_model,
        [1.0] * len(variables_activas),
        variables_activas,
        len(variables_activas) - 1,
        "L",
        f"nogood_{cut_id}"
    )

def agregar_restriccion_no_vacia(slave_model):
    nombres = []
    valores = []

    for nombre in slave_model.variables.get_names():
        if nombre.startswith("z_x_") or nombre.startswith("z_y_"):
            nombres.append(nombre)
            valores.append(1.0)

    if not nombres:
        return

    add_constraint(
        slave_model,
        valores,
        nombres,
        1.0,
        "G",
        f"non_empty_{slave_model.linear_constraints.get_num()}"
    )


def obtener_rebanadas_activas(rebanadas, variables_activas_maestro):
    ids_activos = set()

    for nombre_variable in variables_activas_maestro:
        if not nombre_variable.startswith("p_"):
            continue
        ids_activos.add(int(nombre_variable.split("_")[1]))

    return [rebanada for rebanada in rebanadas if rebanada.get_id() in ids_activos]


def exportar_layout_final(bin_width, bin_height, item_width, item_height, cota_fisica_items, rebanadas_activas):
    output_path = os.path.join("Resultados", f"{CASE_NAME}_layout.png")
    exportar_solucion_bin_a_png(bin_width, bin_height, item_width, item_height, cota_fisica_items, rebanadas_activas, output_path)
    print(f"Layout final exportado en: {output_path}")


def desnormalizar_rebanadas_para_salida(rebanadas, bin_width_original, bin_height_original, item_width_original, item_height_original, bin_normalizado, item_normalizado):
    if not bin_normalizado and not item_normalizado:
        return rebanadas

    alto_rebanada = calcular_alto_rebanada(bin_width_original, bin_height_original, item_width_original, item_height_original)
    rebanadas_desnormalizadas = []

    for rebanada in rebanadas:
        items_desnormalizados = []

        for item in rebanada.get_items():
            x = item.get_posicion_x()
            y = item.get_posicion_y()
            ancho = item.get_ancho()
            alto = item.get_alto()

            if bin_normalizado:
                x_original = bin_width_original - (y + alto)
                y_original = x
                ancho_original = alto
                alto_original = ancho
            else:
                x_original = x
                y_original = y
                ancho_original = ancho
                alto_original = alto

            item_original = Item(
                alto=alto_original,
                ancho=ancho_original,
                rotado=item.get_rotado() ^ bin_normalizado ^ item_normalizado,
                posicion_x=x_original,
                posicion_y=y_original
            )
            items_desnormalizados.append(item_original)

        rebanadas_desnormalizadas.append(
            Rebanada(
                alto=alto_rebanada,
                ancho=bin_width_original,
                items=items_desnormalizados
            )
        )

    return rebanadas_desnormalizadas


# Orquestador principal
def orquestador(queue, manual_interruption, max_time, initial_time, config_data, devolver_solucion=False):
    try:
        # Reiniciar el contador de IDs de Rebanada para cada ejecución
        Rebanada.reset_id_counter()
        iteraciones_sin_mejora = 0

        # Seteo configuraciones en base a los datos recibidos en config_data
        bin_width_original = config_data.get_bin_width()
        bin_height_original = config_data.get_bin_height()
        item_width_original = config_data.get_item_width()
        item_height_original = config_data.get_item_height()
        bin_width = bin_width_original
        bin_height = bin_height_original
        item_width = item_width_original
        item_height = item_height_original

        bin_normalizado = bin_height > bin_width
        item_normalizado = item_height > item_width

        if bin_normalizado:
            bin_width, bin_height = bin_height, bin_width

        if item_normalizado:
            item_width, item_height = item_height, item_width

        alto_rebanada = calcular_alto_rebanada(bin_width, bin_height, item_width, item_height)

        # Genero posiciones a usar en el bin
        pos_xy_x, pos_xy_y = generate_positions_xym2(bin_width, bin_height, item_width, item_height)

        max_items_fisicos = calcular_cota_fisica_items(bin_width, bin_height, item_width, item_height)

        # Genero rebanadas iniciales usando una cota fisica, no una demanda finita de items.
        rebanadas = generar_rebanadas_iniciales(bin_width, bin_height, item_width, item_height, pos_xy_x, pos_xy_y, max_items_fisicos)

        iteracion = 0

        # Construyo firma de rebanadas iniciales para evitar que se generen nuevamente en alguna iteracion
        firmas_generadas = {construir_firma_rebanada(r) for r in rebanadas}
        objective_master_anterior = None

        while True:
            #TODO: Aca podria mejorar evitando la creacion del modelo en cada vuelta.
            # En su lugar, podria crear uno y luego agregar las columnas (rebanadas) nuevas

            master_model = create_master_model(max_time, rebanadas, bin_height, bin_width, item_height, item_width, pos_xy_x, pos_xy_y)
            # Resolver modelo maestro
            objective_master, precios_duales, _ = solve_master_model(master_model, queue, manual_interruption, True, initial_time)

            if objective_master_anterior is None:
                print("FO maestro relajado anterior: None (primera iteración)")
            else:
                mejora_master = objective_master - objective_master_anterior

            slave_model = create_slave_model(max_time, pos_xy_x, pos_xy_y, precios_duales, bin_width, item_height, item_width, bin_height, alto_rebanada)
            nueva_rebanada, objective_value_slave_model, variables_activas = solve_slave_model(slave_model, queue, manual_interruption, bin_width, item_height, item_width, alto_rebanada)

            es_duplicada = False

            # validacion de duplicados solo si se genero una nueva rebanada
            if nueva_rebanada is not None:
                firma = construir_firma_rebanada(nueva_rebanada)
                es_duplicada = firma in firmas_generadas

            # Si el esclavo no devolvió una solución factible, corto el proceso
            if objective_value_slave_model is None:
                print("El esclavo no devolvió una solución factible. CORTE.")
                break

            # Si la FO del esclavo es menor o igual a EPS, se considera que no hay mejora significativa pero aun no se cierra el proceso,
            # sino que se generan algunas adicionales
            if objective_value_slave_model <= EPS:
                soluciones_excluidas = []

                # excluyo la solución actual del esclavo para forzar la generación de una nueva rebanada en la próxima iteración
                if variables_activas:
                    soluciones_excluidas.append(variables_activas)

                # inicio el proceso de generacion de nuevas rebanadas, realizado MAX_EXTRA iteraciones
                # o hasta que ocurra algun corte
                for _ in range(MAX_EXTRA):
                    slave_model = create_slave_model(
                        max_time,
                        pos_xy_x,
                        pos_xy_y,
                        precios_duales,
                        bin_width,
                        item_height,
                        item_width,
                        bin_height,
                        alto_rebanada
                    )

                    # obligo al modelo a generar rebanadas con al menos 1 item (no quiero triviales)
                    agregar_restriccion_no_vacia(slave_model)

                    # obligo al modelo a que no me devuelva la misma rebanada anterior
                    # evitando que se activen las mismas variables que en la solución anterior del esclavo
                    for i, activas in enumerate(soluciones_excluidas):
                        agregar_no_good_cut(slave_model, activas, i)

                    # resuelvo el modelo esclavo modificado
                    nueva_rebanada_extra, objective_value_extra, variables_activas_extra = solve_slave_model(
                        slave_model,
                        queue,
                        manual_interruption,
                        bin_width,
                        item_height,
                        item_width,
                        alto_rebanada
                    )

                    # Si el esclavo no devolvió una solución factible, corto la generación de rebanadas extra
                    if objective_value_extra is None:
                        break

                    # Si el valor objetivo es claramente negativo, no conviene agregar la rebanada
                    if objective_value_extra < -EPS:
                        print("[EXTRA] FO del esclavo < -EPS. No se agrega.")
                        break

                    # Si no se genero ninguna rebanda extra, corto el proceso
                    if nueva_rebanada_extra is None:
                        print("[EXTRA] No se genero ninguna rebanada. Corte.")
                        break

                    # Si no se genero ninguna variable activa en el esclavo, corto el proceso
                    if not variables_activas_extra:
                        print("[EXTRA] No hay variables activas. Corte.")
                        break

                    # Construyo firma de la nueva rebanada extra generada para validar duplicados
                    firma_extra = construir_firma_rebanada(nueva_rebanada_extra)

                    # Si la firma de la nueva rebanada extra no se ha generado antes, la agrego a la lista de rebanadas y a las firmas generadas
                    if firma_extra not in firmas_generadas:
                        rebanadas.append(nueva_rebanada_extra)
                        firmas_generadas.add(firma_extra)

                    # excluyo la solucion actual del esclavo para forzar la generación de una nueva rebanada en la próxima iteración
                    soluciones_excluidas.append(variables_activas_extra)

                break

            # Si la nueva rebanada es duplicada, corto el proceso para evitar ciclos
            if es_duplicada:
                reduced_cost_real, cantidad_items, suma_duales = calcular_reduced_cost_real(nueva_rebanada, precios_duales, item_width, item_height)
                print(
                    "Rebanada duplicada detectada. "
                    f"FO esclavo={objective_value_slave_model}, "
                    f"items={cantidad_items}, "
                    f"sumaDualesOcupacion={suma_duales}, "
                    f"costoReducidoCompleto={reduced_cost_real}"
                )
                soluciones_excluidas = []
                if variables_activas:
                    soluciones_excluidas.append(variables_activas)

                se_agrego_alternativa = False
                for _ in range(MAX_EXTRA):
                    slave_model = create_slave_model(
                        max_time,
                        pos_xy_x,
                        pos_xy_y,
                        precios_duales,
                        bin_width,
                        item_height,
                        item_width,
                        bin_height,
                        alto_rebanada
                    )

                    agregar_restriccion_no_vacia(slave_model)

                    for i, activas in enumerate(soluciones_excluidas):
                        agregar_no_good_cut(slave_model, activas, i)

                    nueva_rebanada_alternativa, objective_value_alternativa, variables_activas_alternativa = solve_slave_model(
                        slave_model,
                        queue,
                        manual_interruption,
                        bin_width,
                        item_height,
                        item_width,
                        alto_rebanada
                    )

                    if objective_value_alternativa is None:
                        break

                    if objective_value_alternativa <= EPS:
                        print("[DUPLICADA] No se encontro alternativa con mejora positiva.")
                        break

                    if nueva_rebanada_alternativa is None or not variables_activas_alternativa:
                        break

                    firma_alternativa = construir_firma_rebanada(nueva_rebanada_alternativa)
                    if firma_alternativa not in firmas_generadas:
                        rebanadas.append(nueva_rebanada_alternativa)
                        firmas_generadas.add(firma_alternativa)
                        se_agrego_alternativa = True
                        break

                    soluciones_excluidas.append(variables_activas_alternativa)

                if se_agrego_alternativa:
                    continue

                print("Rebanada duplicada detectada sin alternativa nueva. Corte de generación.")
                break

            # Si el esclavo no generó ninguna rebanada, corto el proceso
            if nueva_rebanada is None:
                print("El esclavo no generó ninguna rebanada. CORTE.")
                break

            # Agrego la nueva rebanada generada a la lista de rebanadas y su firma al conjunto de firmas generadas
            firmas_generadas.add(firma)
            rebanadas.append(nueva_rebanada)

            # Actualizo el contador de iteraciones sin mejora del maestro
            if objective_master_anterior is not None:
                mejora_master = objective_master - objective_master_anterior
                if abs(mejora_master) <= EPS_MASTER:
                    iteraciones_sin_mejora += 1
                else:
                    iteraciones_sin_mejora = 0

            # Si el maestro no mejora luego de MAX_ESTANCAMIENTO iteraciones, corto el proceso para evitar estancamiento numérico
            if iteraciones_sin_mejora >= MAX_ESTANCAMIENTO:
                print("Corte por estancamiento numerico del maestro.")
                break

            # Actualizo el valor de la FO del maestro anterior para la próxima iteración
            objective_master_anterior = objective_master
            iteracion += 1

        # Resuelvo el modelo maestro final sin relajar para obtener una solución entera factible y su valor objetivo final
        master_model = create_master_model(max_time, rebanadas, bin_height, bin_width, item_height, item_width, pos_xy_x, pos_xy_y)
        objective_value_slave_model, _, variables_activas_maestro = solve_master_model(master_model, queue, manual_interruption, False, initial_time)
        # Genero png con layout final solo con las rebanadas activas en la solución final del maestro
        rebanadas_activas = obtener_rebanadas_activas(rebanadas, variables_activas_maestro)
        rebanadas_activas_salida = desnormalizar_rebanadas_para_salida(
            rebanadas_activas,
            bin_width_original,
            bin_height_original,
            item_width_original,
            item_height_original,
            bin_normalizado,
            item_normalizado
        )
        if rebanadas_activas_salida:
            exportar_layout_final(bin_width_original, bin_height_original, item_width_original, item_height_original, max_items_fisicos, rebanadas_activas_salida)
        else:
            print("No se generó ninguna rebanada activa en la solución final del maestro. No se exporta layout.")
        # Devuelvo resultado
        if devolver_solucion:
            return objective_value_slave_model, rebanadas_activas_salida

        return objective_value_slave_model

    except CplexSolverError as e:
        solver_time = round(time.time() - initial_time, 2)
        handle_solver_error(e, queue, solver_time)
        if devolver_solucion:
            return None, []

        return None

def executeWithTimeLimit(max_time):
    global model_status, solver_status, objective_value, solver_time
    global exceding_limit_time
    exceding_limit_time = False
    initial_time = time.time()

    # Crear una cola para recibir los resultados del subproceso
    queue = multiprocessing.Queue()

    # Crear una variable compartida para manejar la interrupción manual
    manual_interruption = multiprocessing.Value('b', True)

    config_data = ConfigData(
        bin_width=BIN_WIDTH,
        bin_height=BIN_HEIGHT,
        item_width=ITEM_WIDTH,
        item_height=ITEM_HEIGHT
    )

    # Crear el subproceso que correrá la función
    process = multiprocessing.Process(target=orquestador, args=(queue, manual_interruption, max_time, initial_time, config_data))

    # Iniciar el subproceso
    process.start()

    # Monitorear la cola mientras el proceso está en ejecución
    while process.is_alive():
        if manual_interruption.value and time.time() - initial_time > max_time:
            print("Limit time reached. Aborting process.")
            model_status = "14" #valor en paver para marcar que el modelo no devolvio respuesta por error
            solver_status = "4" #el solver finalizo la ejecucion del modelo
            solver_time = max_time
            exceding_limit_time = True
            process.terminate()
            process.join()
            break
        time.sleep(0.1)  # Evitar consumir demasiados recursos

    # Imprimo resultados de la ejecucion que se guardan luego en el archivo trc para usar en paver
    while not queue.empty():
        message = queue.get()
        if isinstance(message, dict):
            objective_value = message["objectiveValue"]
            model_status = message["modelStatus"]
            solver_status = message["solverStatus"]
            solver_time = message["solverTime"]
            print(f"Optimal value: {objective_value}")
            print(message)
    if exceding_limit_time:
        print("El modelo excedió el tiempo límite de ejecución.")
        objective_value = "n/a"
        model_status = "14"

    return CASE_NAME, MODEL_NAME, model_status, solver_status, objective_value, solver_time
