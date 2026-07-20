# Bin Packing Bidimensional resuelto con generación de columnas

Este proyecto aborda el problema de Bin Packing Bidimensional (2D-BPP), donde se busca ubicar un conjunto de items rectangulares dentro de un bin rectangular evitando solapamientos entre ellos y respetando las dimensiones del bin. El objetivo es construir una disposicion factible que empaquete la mayor cantidad posible de items, considerando posiciones validas y, segun el modelo utilizado, rotación de los items.

## Enfoque del proyecto actual

La resolucion se basa en generacion de columnas. El problema se descompone en un modelo maestro y un modelo esclavo:

- El modelo maestro selecciona rebanadas ya generadas y controla que no haya colisiones entre los items elegidos.
- El modelo esclavo usa la informacion dual del maestro para generar nuevas rebanadas candidatas que puedan mejorar la solucion actual.
- El proceso se repite mientras aparezcan rebanadas nuevas con potencial de mejora. Al finalizar, el maestro se resuelve en version entera con las columnas generadas.

Para evitar ciclos o repeticiones, la implementacion detecta rebanadas ya generadas y puede agregar restricciones de exclusion al modelo esclavo.

## Algoritmo

La descripcion detallada del algoritmo, las condiciones de corte y el rol de cada modelo estan documentados en [`Docs/algorithm.md`](Docs/algorithm.md).

## Ejecucion de instancias

Las instancias se configuran en [`Config.py`](Config.py). Cada instancia tiene un nombre propio (`caso2`, `caso7`, etc.) que se usa como `InputFileName` en el archivo `.trc` de PAVER.

Para ejecutar el caso por defecto, alcanza con correr `Main.py` directamente:

```bash
python Main.py
```

El caso por defecto se define en `Config.py` mediante `DEFAULT_CASE_NAME`.

Para ejecutar una instancia puntual:

```bash
python Main.py --case caso7
```

Para ejecutar varias instancias en una misma corrida:

```bash
python Main.py --cases caso2 caso4 caso7
```

Para ejecutar todas las instancias cargadas en el catalogo:

```bash
python Main.py --all
```

Tambien se puede cambiar el tiempo limite por modelo:

```bash
python Main.py --cases caso2 caso4 caso7 --time 1200
```

La salida se guarda por defecto en `Resultados/output.trc`. Se puede cambiar el nombre del archivo con:

```bash
python Main.py --case caso7 --output output_caso7.trc
```

La estructura esperada para PAVER es una fila por combinacion de instancia y modelo, por ejemplo:

```text
caso2,Model5Orchestrator,...
caso2,BacktrackingMonoitemExacto,...
caso4,Model5Orchestrator,...
caso4,BacktrackingMonoitemExacto,...
```
