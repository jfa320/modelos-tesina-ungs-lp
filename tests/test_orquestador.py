import time

import pytest
from Modelo_5_Orquestador import orquestador
from Objetos.ConfigData import ConfigData

class TestOrquestador:
    def test_caso_1(self, orquestador_context):
        
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=6,   # N
            binWidth=6,        # W
            binHeight=4,       # H
            itemWidth=2,       # w
            itemHeight=3       # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 4  # Valor óptimo esperado para el Caso 1

   
    def test_caso_2(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=6,   # N
            binWidth=5,        # W
            binHeight=5,       # H
            itemWidth=3,       # w
            itemHeight=2       # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 4  # Valor óptimo esperado para el Caso 2