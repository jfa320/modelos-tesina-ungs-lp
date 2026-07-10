
def posiciones_ocupadas(item):
    x = item.get_posicion_x()
    y = item.get_posicion_y()

    return {
        (x + dx, y + dy)
        for dx in range(item.get_ancho())
        for dy in range(item.get_alto())
    }

def validar_factibilidad(rebanadas, bin_width, bin_height, objective_value):
    ocupadas = set()
    total_items = 0
    for rebanada in rebanadas:
        for item in rebanada.get_items():
            celdas_item = posiciones_ocupadas(item)
            assert all(0 <= x < bin_width for x, y in celdas_item)
            assert all(0 <= y < bin_height for x, y in celdas_item)
            assert ocupadas.isdisjoint(celdas_item)
            ocupadas.update(celdas_item)
            total_items += 1
    assert total_items == objective_value
