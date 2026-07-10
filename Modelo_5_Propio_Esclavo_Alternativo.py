import cplex
from cplex.exceptions import CplexSolverError
from Utils.Model_Functions import *
from Config import *
from Objetos import Rebanada
from Objetos import Item

MODEL_NAME = "Model5SlaveAlternative"
DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS = True  # Cambiar a True para desactivar el control de restricciones repetidas

EPS = 1e-9  # tolerancia numérica


def construir_items(variable_names, variable_values, alto_item, ancho_item):
    items = []

    for name, value in zip(variable_names, variable_values):
        if not name.startswith("z_") or value <= 0.5:
            continue

        parts = name.split("_")
        # z_<rot>_<x>_<y>
        rot = parts[1]
        x_value = int(parts[2])
        y_value = int(parts[3])

        rotado = (rot == "y")

        alto = ancho_item if rotado else alto_item
        ancho = alto_item if rotado else ancho_item

        item = Item(
            alto=alto,
            ancho=ancho,
            rotado=rotado,
            posicion_x=x_value,
            posicion_y=y_value
        )

        if item not in items:
            items.append(item)

    return items


def construir_posiciones_ocupadas(variable_names, variable_values, alto_item, ancho_item):
    posiciones_ocupadas = set()

    for name, value in zip(variable_names, variable_values):
        if not name.startswith("z_") or value <= 0.5:
            continue

        parts = name.split("_")
        rot = parts[1]
        x0 = int(parts[2])
        y0 = int(parts[3])

        rotado = (rot == "y")
        alto = ancho_item if rotado else alto_item
        ancho = alto_item if rotado else ancho_item

        for dx in range(ancho):
            for dy in range(alto):
                posiciones_ocupadas.add((x0 + dx, y0 + dy))

    posiciones_ocupadas = list(posiciones_ocupadas)
    return posiciones_ocupadas


def obtener_y_maximo(posiciones_ocupadas, alto_item, ancho_item, items):
    # TODO: Revisar si este metodo es necesario
    if not posiciones_ocupadas:
        return None  # Manejar caso donde la lista esté vacía
    item_pos_y_max = max(items, key=lambda item: item.get_posicion_y())
    return item_pos_y_max.get_posicion_y() + item_pos_y_max.get_alto()


def rects_solapan(x1, y1, w1, h1, x2, y2, w2, h2):
    return not (
        x1 + w1 <= x2 or x2 + w2 <= x1 or
        y1 + h1 <= y2 or y2 + h2 <= y1
    )


def create_slave_model(max_time, xy_x, xy_y, dual_values, ancho_bin, alto_item_sin_rotar, ancho_item_sin_rotar, alto_bin, alto_rebanada):
    print("--------------------------------------------------------------------------------------------------------------------")
    print("IN - Create Slave Model")
    a_i = dual_values
    h = alto_item_sin_rotar
    w = ancho_item_sin_rotar
    width = ancho_bin
    height = alto_bin
    posiciones = set(xy_x).union(xy_y)
    posiciones_no_rotado = xy_x
    posiciones_rotado = xy_y
    posiciones = list(posiciones)  # Convertir a lista para iterar
    posiciones.sort()  # Ordenar los pares (a, b) para consistencia

    posiciones_x_validas = []
    for (a, b) in posiciones_no_rotado:
        if a + w <= width and b + h <= height:
            posiciones_x_validas.append((a, b))

    posiciones_y_validas = []
    for (a, b) in posiciones_rotado:
        if a + h <= width and b + w <= height:
            posiciones_y_validas.append((a, b))

    # R[(a,b,t)] = celdas cubiertas por un item que inicia en (a,b,t)
    regiones_ocupadas = {}

    for (a, b) in posiciones_x_validas:
        regiones_ocupadas[(a, b, 'x')] = [
            (x, y)
            for x in range(a, a + w)
            for y in range(b, b + h)
        ]

    for (a, b) in posiciones_y_validas:
        regiones_ocupadas[(a, b, 'y')] = [
            (x, y)
            for x in range(a, a + h)
            for y in range(b, b + w)
        ]

    try:
        # Crear el modelo
        model = cplex.Cplex()
        model.parameters.preprocessing.presolve.set(0)
        # model.set_problem_type(cplex.Cplex.problem_type.LP)
        model.objective.set_sense(model.objective.sense.maximize)

        model.parameters.timelimit.set(max_time)
        initial_time = model.get_time()
        added_constraints = set()

        # Función objetivo
        z_vars_rotadas = []
        z_vars_no_rotadas = []
        obj_coeffs = []

        # Helper para sumar los duales de las celdas cubiertas por (a,b,t)
        def calcular_suma_dual(a, b, t):
            celdas_cubiertas = regiones_ocupadas[(a, b, t)]
            return sum(a_i["pi"].get(f"({x},{y})", 0.0) for (x, y) in celdas_cubiertas)

        # Variables no rotadas
        # ---------------------------------------------------------------------
        for (a, b) in posiciones_x_validas:
            var_name = f"z_x_{a}_{b}"
            z_vars_no_rotadas.append(var_name)

            suma_dual = calcular_suma_dual(a, b, 'x')
            coeff = 1.0 - suma_dual
            obj_coeffs.append(coeff)

        add_variables(model, z_vars_no_rotadas, obj_coeffs, "B")
        obj_coeffs.clear()

        # ---------------------------------------------------------------------
        # Variables rotadas
        # ---------------------------------------------------------------------
        for (a, b) in posiciones_y_validas:
            var_name = f"z_y_{a}_{b}"
            z_vars_rotadas.append(var_name)

            suma_dual = calcular_suma_dual(a, b, 'y')
            coeff = 1.0 - suma_dual
            obj_coeffs.append(coeff)

        add_variables(model, z_vars_rotadas, obj_coeffs, "B")
        obj_coeffs.clear()

        y_bases_validos = sorted({b for (_, b) in posiciones_x_validas + posiciones_y_validas})
        y_base_vars = [f"s_{y_base}" for y_base in y_bases_validos]
        add_variables(model, y_base_vars, [0.0] * len(y_base_vars), "B")

        # Restricciones
        # Restricciones de no solapamiento
        cover_map = {}
        cons_rhs = 1

        for (a, b, t), celdas in regiones_ocupadas.items():
            var_name = f"z_{t}_{a}_{b}"
            for (x, y) in celdas:
                cover_map.setdefault((x, y), set()).add(var_name)

        for (x, y), vars_que_cubren in cover_map.items():
            coeffs = [1.0] * len(vars_que_cubren)
            add_constraint_set(
                model,
                coeffs,
                vars_que_cubren,
                cons_rhs,
                "L",
                added_constraints,
                f"consNoOverlap_{x}_{y}",
                DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
            )

        # El esclavo elige internamente una unica franja vertical de alto
        # alto_rebanada. Cada item seleccionado debe iniciar dentro de esa franja.
        if y_base_vars:
            add_constraint_set(
                model,
                [1.0] * len(y_base_vars),
                y_base_vars,
                1.0,
                "L",
                added_constraints,
                "consOneSliceWindow",
                DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
            )

        for (a, b) in posiciones_x_validas:
            var_name = f"z_x_{a}_{b}"
            ventanas_que_contienen_inicio = [
                f"s_{y_base}"
                for y_base in y_bases_validos
                if y_base <= b and b < y_base + alto_rebanada
            ]
            add_constraint_set(
                model,
                [1.0] + [-1.0] * len(ventanas_que_contienen_inicio),
                [var_name] + ventanas_que_contienen_inicio,
                0.0,
                "L",
                added_constraints,
                f"consSliceWindow_x_{a}_{b}",
                DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
            )

        for (a, b) in posiciones_y_validas:
            var_name = f"z_y_{a}_{b}"
            ventanas_que_contienen_inicio = [
                f"s_{y_base}"
                for y_base in y_bases_validos
                if y_base <= b and b < y_base + alto_rebanada
            ]
            add_constraint_set(
                model,
                [1.0] + [-1.0] * len(ventanas_que_contienen_inicio),
                [var_name] + ventanas_que_contienen_inicio,
                0.0,
                "L",
                added_constraints,
                f"consSliceWindow_y_{a}_{b}",
                DESACTIVAR_CONTROL_DE_RESTRICCIONES_REPETIDAS
            )

        print("OUT - Create Slave Model")
        return model
    except CplexSolverError:
        raise


def solve_slave_model(model, queue, manual_interruption, bin_width, item_height, item_width, alto_rebanada):
    print("IN - Solve Slave Model")

    eps_second_phase = 1e-8

    def extraer_solucion_actual(modelo):
        nombres = modelo.variables.get_names()
        valores = modelo.solution.get_values()

        items_construidos = []
        variables_activas = []

        for nombre, valor in zip(nombres, valores):
            if valor <= 0.5:
                continue

            if nombre.startswith("z_x_") or nombre.startswith("z_y_"):
                variables_activas.append(nombre)

            parts = nombre.split("_")
            if len(parts) != 4:
                continue

            _, tipo, a, b = parts
            a = int(a)
            b = int(b)

            if tipo == "x":
                item = Item(
                    alto=item_height,
                    ancho=item_width,
                    rotado=False
                )
            else:
                item = Item(
                    alto=item_width,
                    ancho=item_height,
                    rotado=True
                )

            item.set_posicion_x(a)
            item.set_posicion_y(b)
            items_construidos.append(item)

        if not items_construidos:
            return None, [], [], None

        posiciones_ocupadas = construir_posiciones_ocupadas(
            nombres,
            valores,
            item_height,
            item_width
        )

        rebanada = Rebanada(
            alto=alto_rebanada,
            ancho=bin_width,
            items=items_construidos
        )

        return rebanada, items_construidos, variables_activas, (nombres, valores)

    def calcular_fo_original_de_solucion(nombres, valores, coeficientes_originales):
        fo = 0.0
        for nombre, valor in zip(nombres, valores):
            if valor > 0.5:
                fo += coeficientes_originales.get(nombre, 0.0)
        return fo

    def imprimir_resumen(etiqueta, fo_original, items_construidos):
        rotados = sum(1 for item in items_construidos if item.get_rotado())
        no_rotados = len(items_construidos) - rotados
        resumen = sorted(
            (item.get_posicion_x(), item.get_posicion_y(), item.get_rotado())
            for item in items_construidos
        )
        print(f"{etiqueta}")
        print(f"  FO original: {fo_original}")
        print(f"  Cantidad items: {len(items_construidos)}")
        print(f"  Rotados: {rotados} | No rotados: {no_rotados}")
        print(f"  Items: {resumen}")

    # =========================================================
    # FASE 1: resolver exactamente como hoy
    # =========================================================
    model.solve()

    status_string = model.solution.get_status_string()
    if "optimal" not in status_string.lower() and "feasible" not in status_string.lower():
        print("No hay solución factible en el esclavo")
        print("OUT - Solve Slave Model")
        return None, None, []

    objective_value_phase_1 = model.solution.get_objective_value()
    print(f"FO esclavo fase 1: {objective_value_phase_1}")

    nombres_vars = model.variables.get_names()
    obj_lineal = model.objective.get_linear()
    coef_originales = {nombre: coef for nombre, coef in zip(nombres_vars, obj_lineal)}

    rebanada_fase_1, items_fase_1, variables_activas_fase_1, solucion_raw_fase_1 = extraer_solucion_actual(model)

    if rebanada_fase_1 is None:
        print("No se reconstruyó ningún item en fase 1")
        print("OUT - Solve Slave Model")
        return None, objective_value_phase_1, []

    imprimir_resumen("Resumen fase 1", objective_value_phase_1, items_fase_1)

    # =========================================================
    # FASE 2: intento opcional de mejora estructural
    # Mantengo FO original casi igual y maximizo cantidad de items
    # =========================================================
    try:
        rhs = objective_value_phase_1 - eps_second_phase

        model.linear_constraints.add(
            lin_expr=[cplex.SparsePair(ind=nombres_vars, val=obj_lineal)],
            senses=["G"],
            rhs=[rhs],
            names=["consMaintainOriginalObjective"]
        )

        # Reseteo FO
        model.objective.set_linear([(nombre, 0.0) for nombre in nombres_vars])

        # Nueva FO: maximizar cantidad de z activas
        model.objective.set_linear([
            (nombre, 1.0)
            for nombre in nombres_vars
            if nombre.startswith("z_x_") or nombre.startswith("z_y_")
        ])
        model.objective.set_sense(model.objective.sense.maximize)

        model.solve()

        status_string_fase_2 = model.solution.get_status_string()
        if "optimal" in status_string_fase_2.lower() or "feasible" in status_string_fase_2.lower():
            rebanada_fase_2, items_fase_2, variables_activas_fase_2, solucion_raw_fase_2 = extraer_solucion_actual(model)

            if rebanada_fase_2 is not None:
                nombres_fase_2, valores_fase_2 = solucion_raw_fase_2
                fo_original_fase_2 = calcular_fo_original_de_solucion(
                    nombres_fase_2,
                    valores_fase_2,
                    coef_originales
                )

                imprimir_resumen("Resumen fase 2", fo_original_fase_2, items_fase_2)

                usar_fase_2 = (
                    fo_original_fase_2 >= objective_value_phase_1 - eps_second_phase
                    and len(items_fase_2) > len(items_fase_1)
                )

                if usar_fase_2:
                    print("Se adopta la solución de fase 2")
                    print("OUT - Solve Slave Model")
                    return rebanada_fase_2, objective_value_phase_1, variables_activas_fase_2
                else:
                    print("Se conserva la solución de fase 1")
            else:
                print("Fase 2 no reconstruyó items válidos. Se conserva fase 1.")
        else:
            print("Fase 2 sin solución factible. Se conserva fase 1.")

    except Exception as e:
        print(f"Fase 2 falló: {e}. Se conserva fase 1.")

    print("OUT - Solve Slave Model")
    return rebanada_fase_1, objective_value_phase_1, variables_activas_fase_1
