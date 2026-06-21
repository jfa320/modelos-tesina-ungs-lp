# Algoritmo

El programa en detalle funciona de la siguiente manera:

1. Se define la configuración del caso (ancho y alto del bin, dimensiones del item, cantidad de ítems a empaquetar)
2. Se generan posiciones válidas (rotadas y no rotadas) dentro del bin en función de la configuración
3. Se genera un conjunto inicial de rebanadas para inicializar el modelo maestro
4. Se construye el modelo maestro relajado utilizando las rebanadas actuales, las posiciones y la configuración
5. Se resuelve el modelo maestro y se obtienen los valores duales asociados a las restricciones de ocupación (evitan colisiones)
6. Se construye el modelo esclavo utilizando los duales del maestro, las posiciones y la configuración
7. Se resuelve el modelo esclavo y se obtiene una rebanada candidata. Si la rebanada es nueva y tiene potencial de mejora, se agrega al maestro. Luego vuelvo al paso 4

## Condiciones de corte:

8. Si el modelo esclavo no genera una rebanada válida, se detiene el proceso.
9. Si el modelo esclavo devuelve una rebanada ya generada previamente, la rebanada no se agrega. En su lugar, se agrega una restricción de exclusión (no-good cut) para excluir esa solución del esclavo y se intenta buscar una alternativa durante un número acotado de iteraciones. Si no se encuentra una alternativa nueva mejorante, se detiene la generación.
10. Si el costo reducido es cercano a cero, se permite una fase adicional de exploración para buscar rebanadas alternativas. Esta fase está acotada por un máximo de M iteraciones.
11. Si el modelo maestro no mejora luego de N iteraciones, se detiene el proceso por posible estancamiento.
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

- selecciona rebanadas que maximizan la cantidad items
- asegura que no haya colisiones entre los items de las rebanadas elegidas


### Esclavo

- genera nuevas rebanadas que potencialmente mejoran la solución actual
- determina la ubicación de los ítems dentro del bin
- Nota: puede devolver una rebanada ya generada en casos de degeneración o empates; en ese caso la implementación la descarta y fuerza la búsqueda de una alternativa

---

## Definición de rebanada
Una rebanada es un espacio dentro del bin que se extiende de un extremo al otro de su ancho, de forma análoga a un corte guillotina horizontal, donde se ubica un conjunto de ítems. Cada ítem posee una posición `(x, y)` correspondiente a la esquina inferior izquierda desde donde es ubicado.

La rebanada tiene asociados un ancho `W` (igual al ancho del bin) y un alto `hr`. Sin embargo, los ítems que la componen pueden exceder hacia arriba dicho alto, por lo que el contorno ocupado por la rebanada no necesariamente coincide con un rectángulo de dimensiones `W x hr`. 

Como condición de pertenencia, la esquina inferior izquierda de cada ítem debe ubicarse dentro de la región de ancho `W` y alto `hr - ε`, donde ε es un valor positivo pequeño utilizado para evitar que un ítem quede exactamente sobre el borde superior de la rebanada.

### Representación interna

Cada rebanada almacena:

- `id`: identificador único.
- `ancho`: ancho de la rebanada.
- `alto`: alto de la rebanada.
- `items`: lista de ítems contenidos en la rebanada.
- `puntosDeInicioItems`: lista de posiciones `(x, y)` correspondientes a los puntos de inicio de los ítems.

### Relación con los ítems

Cada ítem contenido en una rebanada posee una posición `(x, y)` expresada en el sistema de coordenadas del bin. Esta posicion corresponde a la esquina inferior izquierda de cada ítem y no es relativa a la rebanada, sino que lo es al bin.

La combinación de la lista de ítems y sus posiciones permite reconstruir completamente la disposición representada por la rebanada dentro del bin.

---

## Rebanadas repetidas

Una rebanada se considera repetida si coincide con una rebanada ya generada previamente según la posición y orientación de sus ítems.

La implementación construye una firma de cada rebanada a partir de las tuplas `(x, y, rotado)` de sus ítems. Si la firma de una rebanada candidata ya pertenece al conjunto de firmas generadas, la rebanada no se agrega al maestro.

Desde el punto de vista de generación de columnas, una columna ya presente en el maestro no aporta una mejora nueva. Sin embargo, debido a degeneración, empates o tolerancias numéricas, el esclavo puede volver a devolver una rebanada conocida.

---

## No-good cuts

Un no-good cut es una restricción agregada al modelo esclavo para impedir que vuelva a devolver exactamente la misma solución.

Si una solución del esclavo activa las variables `z_1, z_2, ..., z_k`, se agrega la restricción `z_1 + z_2 + ... + z_k <= k - 1`.

De esta forma, al menos una de esas variables debe cambiar en la siguiente solución. En la implementación, esto se usa para excluir rebanadas repetidas o soluciones ya exploradas durante la fase de búsqueda adicional.

---

## Condiciones de finalización

- el esclavo no genera una rebanada válida
- no se encuentra una rebanada nueva con costo reducido positivo
- se detectan rebanadas repetidas y no se logra obtener una alternativa nueva luego de aplicar no-good cuts
- el maestro se estanca luego de varias iteraciones sin mejora significativa
- se alcanza el límite de intentos adicionales o de tiempo

---
## Detalles importantes:

- el modelo maestro no posiciona rebanadas ni items. Simplemente elige las rebanadas cuyos items no colisionan entre sí
- en línea a lo anterior, la rebanada viene armada desde el esclavo con sus items y con ellos su ubicación en el bin
