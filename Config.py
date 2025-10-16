# Configuración compartida para todos los modelos
CASE_NAME="inst2" # nombre del caso a probar que se guarda en el archivo trc

# ITEMS_QUANTITY = 15
# BIN_WIDTH = 6
# BIN_HEIGHT = 4
# ITEM_WIDTH = 2
# ITEM_HEIGHT = 3
# EXECUTION_TIME = 2  # Tiempo de ejecución en segundos para cada modelo


# ITEMS_QUANTITY = 4  # constante N del modelo


# BIN_WIDTH = 4       # W en el modelo
# BIN_HEIGHT = 4      # H en el modelo
# ITEM_WIDTH = 2      # w en el modelo
# ITEM_HEIGHT = 2     # h en el modelo


# Caso 1:
# ITEMS_QUANTITY=6 # constante N del modelo

# BIN_WIDTH = 6 # W en el modelo
# BIN_HEIGHT = 4 # H en el modelo
# ITEM_WIDTH= 2 # w en el modelo
# ITEM_HEIGHT= 3 # h en el modelo

#Caso 2: este vengo probando hace meses

# ITEMS_QUANTITY=6 # constante N del modelo

# BIN_WIDTH = 5 # W en el modelo
# BIN_HEIGHT = 5 # H en el modelo
# ITEM_WIDTH= 3 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

# nuevo
# ITEMS_QUANTITY=6 # constante N del modelo

# BIN_WIDTH = 6 # W en el modelo
# BIN_HEIGHT = 6 # H en el modelo
# ITEM_WIDTH= 3 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

#Caso 3: 

# ITEMS_QUANTITY=8 # constante N del modelo

# BIN_WIDTH = 6 # W en el modelo
# BIN_HEIGHT = 6 # H en el modelo
# ITEM_WIDTH= 4 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

#Caso 4: 

# ITEMS_QUANTITY=5 # constante N del modelo

# BIN_WIDTH = 7 # W en el modelo
# BIN_HEIGHT = 3 # H en el modelo
# ITEM_WIDTH= 3 # w en el modelo
# ITEM_HEIGHT= 2 # h en el modelo

# Caso 5:  este caso es el que rompe el generador de posiciones viejas (da un item menos de los que entran, no considera todas las posiciones)

# ITEMS_QUANTITY = 6  # constante N del modelo
# BIN_WIDTH = 6  # W en el modelo
# BIN_HEIGHT = 3  # H en el modelo

# ITEM_WIDTH = 3  # w en el modelo
# ITEM_HEIGHT = 2  # h en el modelo


#Caso 6: 

ITEMS_QUANTITY = 30  # constante N del modelo

BIN_WIDTH = 120  # W en el modelo
BIN_HEIGHT = 20  # H en el modelo

ITEM_WIDTH = 12  # w en el modelo
ITEM_HEIGHT = 8  # h en el modelo

# Desde acá empiezan los casos de la OR Library (grandes)

# # Caso 7 
# ITEMS_QUANTITY = 14    # obliga a aprovechar bien el espacio
# BIN_WIDTH = 50         # W
# BIN_HEIGHT = 20        # H
# ITEM_WIDTH = 13        # w
# ITEM_HEIGHT = 8        # h

# Caso 8:
# ITEMS_QUANTITY = 18    
# BIN_WIDTH = 40         
# BIN_HEIGHT = 25        
# ITEM_WIDTH = 10        
# ITEM_HEIGHT = 6     
# Optimo 16

# Caso 9:
# ITEMS_QUANTITY = 22    
# BIN_WIDTH = 60         
# BIN_HEIGHT = 20        
# ITEM_WIDTH = 12        
# ITEM_HEIGHT = 7       

# Caso 10: -> este se resuelve rapido. TODO: Analizar por qué
# ITEMS_QUANTITY = 15    
# BIN_WIDTH = 45         
# BIN_HEIGHT = 30        
# ITEM_WIDTH = 9         
# ITEM_HEIGHT = 9  
# optimo 15


# Caso 11:
# ITEMS_QUANTITY = 28    
# BIN_WIDTH = 70         
# BIN_HEIGHT = 25        
# ITEM_WIDTH = 14        
# ITEM_HEIGHT = 8        
# optimo 15

# Caso 12
# ITEMS_QUANTITY = 20    
# BIN_WIDTH = 55         
# BIN_HEIGHT = 22        
# ITEM_WIDTH = 11        
# ITEM_HEIGHT = 6    
#optimo 18

# Caso 13

# ITEMS_QUANTITY = 20    
# BIN_WIDTH = 55         
# BIN_HEIGHT = 22        
# ITEM_WIDTH = 11        
# ITEM_HEIGHT = 6     

# Óptimo: 18 ítems (5 de ancho x 3 de alto = 15 sin rotar, 
# más 3 rotados en el espacio sobrante)

# # Caso 14
# ITEMS_QUANTITY = 25    
# BIN_WIDTH = 40         
# BIN_HEIGHT = 30        
# ITEM_WIDTH = 10        
# ITEM_HEIGHT = 7     
# # Óptimo: 16 ítems (4 de ancho x 2 de alto = 8 sin rotar,
# # más 8 rotados 7x10 en los espacios libres arriba)

# # Caso 15
# ITEMS_QUANTITY = 30    
# BIN_WIDTH = 60         
# BIN_HEIGHT = 25        
# ITEM_WIDTH = 12        
# ITEM_HEIGHT = 5     
# # Óptimo: 25 ítems (5 de ancho x 5 de alto)

# # Caso 16
# ITEMS_QUANTITY = 18    
# BIN_WIDTH = 48         
# BIN_HEIGHT = 24        
# ITEM_WIDTH = 8         
# ITEM_HEIGHT = 6     
# # Óptimo: 24 ítems (6 de ancho x 4 de alto, 
# # entran todos los 18 disponibles)

# # Caso 17
# ITEMS_QUANTITY = 40    
# BIN_WIDTH = 70         
# BIN_HEIGHT = 28        
# ITEM_WIDTH = 14        
# ITEM_HEIGHT = 7     
# # Óptimo: 20 ítems (5 de ancho x 4 de alto)

# ITEMS_QUANTITY = 25     # muchos ítems
# BIN_WIDTH = 20          # ancho del bin
# BIN_HEIGHT = 20         # alto del bin
# ITEM_WIDTH = 6          # ancho de cada ítem
# ITEM_HEIGHT = 5         # alto de cada ítem
# # Óptimo: 12

# # OR Library test
# # Caso 3
# ITEMS_QUANTITY = 100     # muchos ítems
# BIN_WIDTH = 20          # ancho del bin
# BIN_HEIGHT = 20         # alto del bin
# ITEM_WIDTH = 1         # ancho de cada ítem
# ITEM_HEIGHT = 6         # alto de cada ítem

# # Caso 2
# ITEMS_QUANTITY = 100     # muchos ítems
# BIN_WIDTH = 20          # ancho del bin
# BIN_HEIGHT = 20         # alto del bin
# ITEM_WIDTH = 2         # ancho de cada ítem
# ITEM_HEIGHT = 8         # alto de cada ítem

# # Caso 3
# ITEMS_QUANTITY = 100     # ítems
# BIN_WIDTH = 20          # ancho del bin
# BIN_HEIGHT = 20         # alto del bin
# ITEM_WIDTH = 6         # ancho de cada ítem
# ITEM_HEIGHT = 5         # alto de cada ítem

# # Caso 4
# ITEMS_QUANTITY = 100     # ítems
# BIN_WIDTH = 20          # ancho del bin
# BIN_HEIGHT = 20         # alto del bin
# ITEM_WIDTH = 4         # ancho de cada ítem
# ITEM_HEIGHT = 9         # alto de cada ítem

# # Caso 5
# ITEMS_QUANTITY = 100     # ítems
# BIN_WIDTH = 20          # ancho del bin
# BIN_HEIGHT = 20         # alto del bin
# ITEM_WIDTH = 8         # ancho de cada ítem
# ITEM_HEIGHT = 7         # alto de cada ítem

# # Caso 6
# ITEMS_QUANTITY = 100     # ítems
# BIN_WIDTH = 20          # ancho del bin
# BIN_HEIGHT = 20         # alto del bin
# ITEM_WIDTH = 7         # ancho de cada ítem
# ITEM_HEIGHT = 5         # alto de cada ítem
# #optimo: 10

# # Caso 7
# ITEMS_QUANTITY = 100     # ítems
# BIN_WIDTH = 10          # ancho del bin
# BIN_HEIGHT = 30         # alto del bin
# ITEM_WIDTH = 1         # ancho de cada ítem
# ITEM_HEIGHT = 6         # alto de cada ítem
# # optimo: 50

# # Caso 8
# ITEMS_QUANTITY = 100     # ítems
# BIN_WIDTH = 10          # ancho del bin
# BIN_HEIGHT = 30         # alto del bin
# ITEM_WIDTH = 2         # ancho de cada ítem
# ITEM_HEIGHT = 8         # alto de cada ítem
# optimo: 

ITEMS = list(range(1, ITEMS_QUANTITY + 1)) 