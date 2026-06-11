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
