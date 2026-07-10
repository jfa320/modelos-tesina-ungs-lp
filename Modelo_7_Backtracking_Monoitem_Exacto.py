import math
import multiprocessing
import time
from functools import lru_cache

from Config import *


MODEL_NAME = "BacktrackingMonoitemExacto"


def _validar_dimensiones(bin_width, bin_height, item_width, item_height):
    dimensiones = [bin_width, bin_height, item_width, item_height]
    if not all(isinstance(valor, int) and valor > 0 for valor in dimensiones):
        raise ValueError("Todas las dimensiones deben ser enteros positivos.")
    if item_width > bin_width and item_width > bin_height:
        raise ValueError("El item no entra en el bin en ninguna orientacion.")
    if item_height > bin_width and item_height > bin_height:
        raise ValueError("El item no entra en el bin en ninguna orientacion.")


def _normalizar_por_mcd(bin_width, bin_height, item_width, item_height):
    divisor = math.gcd(math.gcd(bin_width, bin_height), math.gcd(item_width, item_height))
    if divisor <= 1:
        return bin_width, bin_height, item_width, item_height, divisor
    return bin_width // divisor, bin_height // divisor, item_width // divisor, item_height // divisor, divisor


def _orientaciones(item_width, item_height, allow_rotation):
    orientaciones = [(item_width, item_height, False)]
    if allow_rotation and item_width != item_height:
        orientaciones.append((item_height, item_width, True))
    return orientaciones


def _se_solapan(rect_a, rect_b):
    ax, ay, aw, ah, _ = rect_a
    bx, by, bw, bh, _ = rect_b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def _generar_grilla_regular(bin_width, bin_height, orientacion, cantidad):
    item_width, item_height, rotado = orientacion
    ubicaciones = []
    for y in range(0, bin_height - item_height + 1, item_height):
        for x in range(0, bin_width - item_width + 1, item_width):
            ubicaciones.append((x, y, item_width, item_height, rotado))
            if len(ubicaciones) == cantidad:
                return ubicaciones
    return ubicaciones


def _puede_colocar(rectangulo, colocados, bin_width, bin_height):
    x, y, ancho, alto, _ = rectangulo
    if x < 0 or y < 0 or x + ancho > bin_width or y + alto > bin_height:
        return False
    return all(not _se_solapan(rectangulo, existente) for existente in colocados)


def _puntos_candidatos(colocados, bin_width, bin_height):
    xs = {0}
    ys = {0}
    for x, y, ancho, alto, _ in colocados:
        if x + ancho < bin_width:
            xs.add(x + ancho)
        if y + alto < bin_height:
            ys.add(y + alto)
    return sorted((x, y) for y in ys for x in xs)


def _buscar_empaquetamiento(bin_width, bin_height, item_width, item_height, cantidad, allow_rotation, deadline=None):
    orientaciones = _orientaciones(item_width, item_height, allow_rotation)
    area_bin = bin_width * bin_height
    area_item = item_width * item_height

    for orientacion in orientaciones:
        if (bin_width // orientacion[0]) * (bin_height // orientacion[1]) >= cantidad:
            return _generar_grilla_regular(bin_width, bin_height, orientacion, cantidad)

    @lru_cache(maxsize=None)
    def backtracking(estado):
        if deadline is not None and time.time() > deadline:
            raise TimeoutError("Tiempo limite alcanzado durante el backtracking.")

        colocados = list(estado)
        if len(colocados) == cantidad:
            return colocados

        restantes = cantidad - len(colocados)
        area_libre = area_bin - len(colocados) * area_item
        if area_libre // area_item < restantes:
            return None

        for x, y in _puntos_candidatos(colocados, bin_width, bin_height):
            for ancho, alto, rotado in orientaciones:
                rectangulo = (x, y, ancho, alto, rotado)
                if not _puede_colocar(rectangulo, colocados, bin_width, bin_height):
                    continue

                nuevo_estado = tuple(sorted(colocados + [rectangulo]))
                resultado = backtracking(nuevo_estado)
                if resultado is not None:
                    return resultado

        return None

    # En una solucion compactada abajo-izquierda siempre puede fijarse un item en el origen.
    for ancho, alto, rotado in orientaciones:
        primer_rectangulo = (0, 0, ancho, alto, rotado)
        if _puede_colocar(primer_rectangulo, [], bin_width, bin_height):
            resultado = backtracking((primer_rectangulo,))
            if resultado is not None:
                return resultado

    return [] if cantidad == 0 else None


def resolver_2dbpp_monoitem_exacto(bin_width, bin_height, item_width, item_height, allow_rotation=True, max_time=None):
    _validar_dimensiones(bin_width, bin_height, item_width, item_height)

    original = (bin_width, bin_height, item_width, item_height)
    bin_width, bin_height, item_width, item_height, escala = _normalizar_por_mcd(
        bin_width,
        bin_height,
        item_width,
        item_height
    )

    cota_area = (bin_width * bin_height) // (item_width * item_height)
    deadline = None if max_time is None else time.time() + max_time

    for cantidad in range(cota_area, 0, -1):
        solucion = _buscar_empaquetamiento(
            bin_width,
            bin_height,
            item_width,
            item_height,
            cantidad,
            allow_rotation,
            deadline
        )
        if solucion is not None:
            solucion_escalada = [
                {
                    "x": x * escala,
                    "y": y * escala,
                    "width": ancho * escala,
                    "height": alto * escala,
                    "rotated": rotado,
                }
                for x, y, ancho, alto, rotado in solucion
            ]
            return {
                "bin_width": original[0],
                "bin_height": original[1],
                "item_width": original[2],
                "item_height": original[3],
                "allow_rotation": allow_rotation,
                "capacity": cantidad,
                "area_upper_bound": cota_area,
                "placements": solucion_escalada,
            }

    return {
        "bin_width": original[0],
        "bin_height": original[1],
        "item_width": original[2],
        "item_height": original[3],
        "allow_rotation": allow_rotation,
        "capacity": 0,
        "area_upper_bound": cota_area,
        "placements": [],
    }


def _resolver_en_proceso(queue, max_time):
    inicio = time.time()
    try:
        resultado = resolver_2dbpp_monoitem_exacto(
            BIN_WIDTH,
            BIN_HEIGHT,
            ITEM_WIDTH,
            ITEM_HEIGHT,
            allow_rotation=True,
            max_time=max_time
        )
        solver_time = time.time() - inicio
        print("-------------------------------------------")
        print("Backtracking exacto monoitem sin PL")
        print(f"Cota por area: {resultado['area_upper_bound']}")
        print(f"Optimo por bin: {resultado['capacity']}")
        print(f"Tiempo de resolucion: {solver_time:.2f} segundos")
        for indice, item in enumerate(resultado["placements"], start=1):
            estado_rotacion = "R" if item["rotated"] else "NR"
            print(
                f"item {indice}: x={item['x']}, y={item['y']}, "
                f"w={item['width']}, h={item['height']}, {estado_rotacion}"
            )

        queue.put({
            "modelStatus": "1",
            "solverStatus": "1",
            "objectiveValue": resultado["capacity"],
            "solverTime": solver_time,
        })
    except TimeoutError:
        queue.put({
            "modelStatus": "2",
            "solverStatus": "4",
            "objectiveValue": "n/a",
            "solverTime": time.time() - inicio,
        })
    except Exception as exc:
        print(f"Error en backtracking exacto monoitem: {exc}")
        queue.put({
            "modelStatus": "14",
            "solverStatus": "4",
            "objectiveValue": "n/a",
            "solverTime": time.time() - inicio,
        })


def execute_with_time_limit(maxTime):
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_resolver_en_proceso, args=(queue, maxTime))
    process.start()
    process.join(maxTime)

    if process.is_alive():
        process.terminate()
        process.join()
        print("El modelo excedio el tiempo limite de ejecucion.")
        return CASE_NAME, MODEL_NAME, "14", "4", "n/a", maxTime

    if queue.empty():
        return CASE_NAME, MODEL_NAME, "14", "4", "n/a", maxTime

    message = queue.get()
    return (
        CASE_NAME,
        MODEL_NAME,
        message["modelStatus"],
        message["solverStatus"],
        message["objectiveValue"],
        message["solverTime"],
    )


if __name__ == "__main__":
    print(execute_with_time_limit(1200))
