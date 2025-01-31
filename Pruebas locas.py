from Modelo_5_Orquestador import * 
numItems = 6  # Número de ítems en el problema
altoBin = 4  # Altura total del bin
items=generarListaItems(numItems,altoItem,anchoItem)
rebanadas=generarRebanadasIniciales(4,6,1,items)
print(rebanadas)