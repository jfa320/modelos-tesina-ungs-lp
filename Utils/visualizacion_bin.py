import os
from PIL import Image, ImageDraw, ImageFont


COLOR_FONDO = "white"
COLOR_BIN = "black"
COLOR_REBANADA_BORDE = "green"
COLOR_REBANADA_RELLENO = (200, 255, 200, 140)
COLOR_REBANADA_TEXTO = (0, 100, 0)
COLOR_ITEM = "blue"
COLOR_ITEM_TEXTO = (0, 0, 180)
COLOR_EJE = (80, 80, 80)
COLOR_LEYENDA = (30, 30, 30)


def _medir_texto(draw, font, texto):
    izquierda, arriba, derecha, abajo = draw.textbbox((0, 0), texto, font=font)
    return derecha - izquierda, abajo - arriba


def _obtener_rectangulo_item(item, escala, origen_x, origen_y, alto_bin):
    x1 = origen_x + int(item.getPosicionX() * escala)
    y_modelo = item.getPosicionY() + item.getAlto()
    y1 = origen_y + int((alto_bin - y_modelo) * escala)
    x2 = x1 + int(item.getAncho() * escala)
    y2 = y1 + int(item.getAlto() * escala)
    return x1, y1, x2, y2


def _ajustar_rectangulo(rectangulo, delta):
    x1, y1, x2, y2 = rectangulo
    return x1 + delta, y1 + delta, x2 - delta, y2 - delta


def _obtener_rectangulo_rebanada(rebanada, escala, origen_x, origen_y, alto_bin):
    if not rebanada.getItems():
        return None

    min_x = min(item.getPosicionX() for item in rebanada.getItems())
    min_y = min(item.getPosicionY() for item in rebanada.getItems())
    max_x = max(item.getPosicionX() + item.getAncho() for item in rebanada.getItems())
    max_y = max(item.getPosicionY() + item.getAlto() for item in rebanada.getItems())

    x1 = origen_x + int(min_x * escala)
    y1 = origen_y + int((alto_bin - max_y) * escala)
    x2 = origen_x + int(max_x * escala)
    y2 = origen_y + int((alto_bin - min_y) * escala)
    return x1, y1, x2, y2


def _dibujar_ejes(draw, font, origen_x, origen_y, ancho_bin_px, alto_bin_px, bin_width, bin_height):
    x0 = origen_x
    y0 = origen_y + alto_bin_px

    for x in range(bin_width + 1):
        x_px = origen_x + int(x * (ancho_bin_px / bin_width))
        draw.line([(x_px, y0), (x_px, y0 + 6)], fill=COLOR_EJE, width=1)
        texto_x = str(x)
        ancho_texto_x, _ = _medir_texto(draw, font, texto_x)
        draw.text((x_px - ancho_texto_x // 2, y0 + 8), texto_x, fill=COLOR_EJE, font=font)

    for y in range(bin_height + 1):
        y_px = origen_y + int(alto_bin_px - y * (alto_bin_px / bin_height))
        draw.line([(x0 - 6, y_px), (x0, y_px)], fill=COLOR_EJE, width=1)
        texto_y = str(y)
        ancho_texto_y, alto_texto_y = _medir_texto(draw, font, texto_y)
        draw.text((x0 - 10 - ancho_texto_y, y_px - alto_texto_y // 2), texto_y, fill=COLOR_EJE, font=font)

    draw.text((origen_x + ancho_bin_px + 10, y0 - 12), "x", fill=COLOR_EJE, font=font)
    draw.text((x0 - 14, origen_y - 16), "y", fill=COLOR_EJE, font=font)


def _construir_lineas_leyenda(bin_width, bin_height, item_width, item_height, total_items, total_items_disponibles):
    return [
        f"Bin: {bin_width} x {bin_height} | Item base: {item_width} x {item_height}",
        f"Cantidad de items colocados: {total_items}",
        f"Cantidad total de items disponibles: {total_items_disponibles}",
        "Bordes: bin negro, rebanada verde, item azul",
        "Labels: Rk = rebanada k | Ij.i-NR = item no rotado | Ij.i-R = item rotado"
    ]


def _dibujar_leyenda(draw, font, margen, inicio_y, line_spacing, lineas):

    for indice, linea in enumerate(lineas):
        draw.text(
            (margen, inicio_y + indice * line_spacing),
            linea,
            fill=COLOR_LEYENDA,
            font=font
        )


def exportar_solucion_bin_a_png(bin_width, bin_height, item_width, item_height, total_items_disponibles, rebanadas_activas, output_path, escala=40, margen=32):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ancho_bin_px = int(bin_width * escala)
    alto_bin_px = int(bin_height * escala)
    font = ImageFont.load_default()
    total_items = sum(len(rebanada.getItems()) for rebanada in rebanadas_activas)

    lineas_leyenda = _construir_lineas_leyenda(
        bin_width,
        bin_height,
        item_width,
        item_height,
        total_items,
        total_items_disponibles
    )

    imagen_aux = Image.new("RGBA", (1, 1), COLOR_FONDO)
    draw_aux = ImageDraw.Draw(imagen_aux)

    max_y_label = str(bin_height)
    ancho_y_label, _ = _medir_texto(draw_aux, font, max_y_label)
    _, alto_x_label = _medir_texto(draw_aux, font, str(bin_width))
    ancho_leyenda = max(_medir_texto(draw_aux, font, linea)[0] for linea in lineas_leyenda)
    alto_linea = max(_medir_texto(draw_aux, font, linea)[1] for linea in lineas_leyenda)
    line_spacing = alto_linea + 6

    margen_izquierdo = max(margen, ancho_y_label + 18)
    margen_superior = max(margen, 20)
    margen_derecho = max(margen, 24)
    margen_inferior_ejes = 8 + alto_x_label + 12
    footer_height = len(lineas_leyenda) * line_spacing + 12

    image_width = max(ancho_bin_px + margen_izquierdo + margen_derecho, ancho_leyenda + 2 * margen)
    image_height = alto_bin_px + margen_superior + margen_inferior_ejes + footer_height

    image = Image.new("RGBA", (image_width, image_height), COLOR_FONDO)
    draw = ImageDraw.Draw(image)

    origen_x = margen_izquierdo
    origen_y = margen_superior

    rect_bin = [
        origen_x,
        origen_y,
        origen_x + ancho_bin_px,
        origen_y + alto_bin_px
    ]
    draw.rectangle(rect_bin, outline=COLOR_BIN, width=3)
    _dibujar_ejes(draw, font, origen_x, origen_y, ancho_bin_px, alto_bin_px, bin_width, bin_height)

    for indice_rebanada, rebanada in enumerate(rebanadas_activas, start=1):
        rect_rebanada = _obtener_rectangulo_rebanada(rebanada, escala, origen_x, origen_y, bin_height)
        if rect_rebanada is not None:
            rect_rebanada_expandida = _ajustar_rectangulo(rect_rebanada, -2)
            draw.rectangle(rect_rebanada_expandida, fill=COLOR_REBANADA_RELLENO, outline=COLOR_REBANADA_BORDE, width=2)
            draw.text(
                (rect_rebanada_expandida[0] + 4, rect_rebanada_expandida[1] + 4),
                f"R{indice_rebanada}",
                fill=COLOR_REBANADA_TEXTO,
                font=font
            )

        for indice_item, item in enumerate(rebanada.getItems(), start=1):
            rect_item = _obtener_rectangulo_item(item, escala, origen_x, origen_y, bin_height)
            rect_item_interno = _ajustar_rectangulo(rect_item, 0)
            draw.rectangle(rect_item_interno, outline=COLOR_ITEM, width=2)
            estado_rotacion = "R" if item.getRotado() else "NR"
            draw.text(
                (rect_item_interno[0] + 4, rect_item_interno[1] + 16),
                f"I{indice_rebanada}.{indice_item}-{estado_rotacion}",
                fill=COLOR_ITEM_TEXTO,
                font=font
            )

    _dibujar_leyenda(draw, font, margen, origen_y + alto_bin_px + margen_inferior_ejes, line_spacing, lineas_leyenda)

    image.convert("RGB").save(output_path, format="PNG")
