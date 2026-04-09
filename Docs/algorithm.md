# Bin Packing Bidimensional resuelto con generación de columnas

El programa en detalle funciona de la siguiente manera:

1. Se define la configuración del caso (ancho y alto del bin, dimensiones de los ítems, cantidad de ítems)
2. Se generan posiciones válidas (rotadas y no rotadas) dentro del bin en función de la configuración
3. Se genera un conjunto inicial de rebanadas para inicializar el modelo maestro
4. Se construye el modelo maestro relajado utilizando las rebanadas actuales, las posiciones y la configuración
5. Se resuelve el modelo maestro y se obtienen los valores duales asociados a las restricciones de ocupación (evitan colisiones)
6. Se construye el modelo esclavo utilizando los duales del maestro, las posiciones y la configuración
7. Se resuelve el modelo esclavo, se obtiene una nueva rebanada y, si es válida, la agrego al maestro. Luego vuelvo al paso 4

## Condiciones de corte:

8. Si el modelo esclavo no genera una rebanada válida o no mejora la solución actual, se detiene el proceso
9. Si el modelo esclavo devuelve una rebanada ya generada previamente, se detiene el proceso
10. Si el modelo maestro no mejora luego de N iteraciones, se detiene el proceso (posible estancamiento)
11. Si el modelo esclavo encuentra rebanadas con mejora muy pequeña (costo reducido cercano a cero), se permite continuar la generación durante algunas iteraciones adicionales para explorar soluciones alternativas. Esto evita cortar prematuramente en casos donde podrían existir rebanadas mejores. Este proceso se limita a M iteraciones.
12. El proceso iterativo continúa desde el paso 4 hasta que se cumple alguna condición de corte

13. Finalmente, se resuelve el modelo maestro en su versión entera con todas las rebanadas generadas para obtener la solución final

---
## En cada iteración:

1. Se resuelve el modelo maestro relajado
2. Se obtienen duales
3. Se resuelve el modelo esclavo con esos duales
4. Se obtiene una nueva rebanada
5. Se decide si agregarla al maestro o finalizar el proceso en base a las condiciones de corte

---

## Rol de cada modelo

### Maestro

- selecciona rebanadas que maximicen la cantidad items
- asegura que no haya colisiones entre items


### Esclavo

- genera nuevas rebanadas que potencialmente mejoran la solución actual
- determina la ubicación de los ítems dentro de cada rebanada

---

## Definición de rebanada
- una rebanada es un conjunto de items ubicados a lo largo del ancho del bin, con la posibilidad de exceder hacia arriba el alto de la rebanada (no necesariamente forma un rectangulo) 

---

## Condiciones de finalización

- el esclavo no genera una rebanada que mejore
- la rebanada generada ya existía
- el algoritmo se estanca (repite rebanadas)
- se alcanza un límite de iteraciones

---
## Detalles importantes:

- el modelo maestro no posiciona rebanadas ni items. Simplemente elige las rebanadas cuyos items no colisionan entre sí
- en línea a lo anterior, la rebanada viene armada desde el esclavo con sus items y con ellos su ubicación en el bin