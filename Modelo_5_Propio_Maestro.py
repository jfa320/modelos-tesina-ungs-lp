import cplex
from cplex.exceptions import CplexSolverError
import multiprocessing
import time
from Position_generator import generatePositionsCidGarcia, createCMatrix
from Utils.Model_Functions import *
from Config import *


# Constantes del problema
H = 10  # Alto del bin (ejemplo)
W = 10  # Ancho del bin (ejemplo)
I = []  # Lista de ítems disponibles
R = []  # Lista de rebanadas disponibles
I_r = {}  # Diccionario con ítems en cada rebanada
C_r = {}  # Cantidad de ítems en cada rebanada
H_r = {}  # Alto de cada rebanada
H_ab= {} # subconjunto de posiciones que inician en (a, b) para items en orientacion horizontal
V_ab= {} # subconjunto de posiciones que inician en (a, b) para items en orientacion vertical

# Crear instancia del problema
model = cplex.Cplex()
model.set_problem_type(cplex.Cplex.problem_type.LP) 


# Variables
# Variables p_r (binarias)
p_r_names = [f"p_{r}" for r in R]
model.variables.add(names=p_r_names, types=[model.variables.type.binary] * len(R))

# Variables y_r (enteras)
y_r_names = [f"y_{r}" for r in R]
model.variables.add(names=y_r_names, types=[model.variables.type.integer] * len(R))


# Función objetivo
coef_obj = [C_r[r] for r in R]  # Coeficientes de p_r en la función objetivo
model.objective.set_sense(model.objective.sense.maximize)
model.objective.set_linear(list(zip(p_r_names, coef_obj)))


# Restricción 1: Un ítem no puede estar en más de una rebanada activa
for i in I:
    indexes = [p_r_names[r] for r in R if i in I_r[r]]
    coefs = [1] * len(indexes)
    consRhs=1.0
    consSense="L"
    addConstraint(model,coefs,indexes,consRhs,consSense)

model.solve()

# (2), (3), (4): No solapamiento
for r in R:
        for (a, b) in r.getPosicionesOcupadas(): #TODO
            H_ab_positions = H_ab.get((a, b), [])
            V_ab_positions = V_ab.get((a, b), [])

            if H_ab_positions:
                model.linear_constraints.add(
                    lin_expr=[[H_ab_positions + [f"p_{r}"],
                                   [1] * len(H_ab_positions) + [-1]]],
                    senses="L",
                    rhs=[0]
                )

            if V_ab_positions:
                model.linear_constraints.add(
                    lin_expr=[[V_ab_positions + [f"p_{r}"],
                               [1] * len(V_ab_positions) + [-1]]],
                    senses="L",
                    rhs=[0]
                )

# Obtener resultados
estado = model.solution.get_status_string()
print(f"Estado de la solución: {estado}")
if model.solution.get_status() in [1, 101, 102]:  # Solución óptima o factible encontrada
    valores_p = model.solution.get_values(p_r_names)
    valores_y = model.solution.get_values(y_r_names)
    print("Valores de p_r:", valores_p)
    print("Valores de y_r:", valores_y)
