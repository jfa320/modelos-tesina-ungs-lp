# from Modelo_5_Orquestador import * 
# numItems = 6  # Número de ítems en el problema
# altoBin = 4  # Altura total del bin
# items=generarListaItems(numItems,altoItem,anchoItem)
# rebanadas=generarRebanadasIniciales(4,6,1,items)
# print(rebanadas)
from Position_generator import *

nRot,rot=generatePositionsXY(10, 7, 3, 4)
print("Posiciones XY (no rotadas):", nRot)
print("Posiciones XY (rotadas):", rot)
print("--------------------------------------------")
nRot,rot=generatePositionsXYOriginal(10, 7, 3, 4)
print("Posiciones XY (no rotadas):", nRot)
print("Posiciones XY (rotadas):", rot)