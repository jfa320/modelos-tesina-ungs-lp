import time

import pytest
from Modelo_5_Orquestador import orquestador
from Objetos.ConfigData import ConfigData

class TestOrquestador:
    def test_caso_1(self, orquestador_context):
        
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=6,        # W
            bin_height=4,       # H
            item_width=2,       # w
            item_height=3       # h
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
            bin_width=5,        # W
            bin_height=5,       # H
            item_width=3,       # w
            item_height=2       # h
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

    def test_caso_nuevo_optimo_6(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=6,        # W
            bin_height=6,       # H
            item_width=3,       # w
            item_height=2       # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 6  # Valor óptimo esperado
        

    def test_caso_3(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=6,        # W
            bin_height=6,       # H
            item_width=4,       # w
            item_height=2       # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 4
        
    def test_caso_4(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=7,        # W
            bin_height=3,       # H
            item_width=3,       # w
            item_height=2       # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 3

    def test_caso_5(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=6,        # W
            bin_height=3,       # H
            item_width=3,       # w
            item_height=2       # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 3

    def test_caso_6(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=120,       # W
            bin_height=20,       # H
            item_width=12,       # w
            item_height=8        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 25
    
    # Desde acá empiezan los casos de la OR Library (grandes)

    def test_caso_7(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=50,        # W
            bin_height=20,       # H
            item_width=13,       # w
            item_height=8        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 7


    def test_caso_8(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=40,        # W
            bin_height=25,       # H
            item_width=10,       # w
            item_height=6        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 16

    def test_caso_9(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=60,        # W
            bin_height=20,       # H
            item_width=12,       # w
            item_height=7        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 13

    def test_caso_10(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=45,        # W
            bin_height=30,       # H
            item_width=9,        # w
            item_height=9        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 15
    
    def test_caso_11(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=70,        # W
            bin_height=25,       # H
            item_width=14,       # w
            item_height=8        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 15

    def test_caso_12(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=55,        # W
            bin_height=22,       # H
            item_width=11,       # w
            item_height=6        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 18

    def test_caso_13(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=20,        # W
            bin_height=20,       # H
            item_width=6,        # w
            item_height=5        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 12
        

    def test_caso_14(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=40,        # W
            bin_height=30,       # H
            item_width=10,       # w
            item_height=7        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 16

    def test_caso_15(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=60,        # W
            bin_height=25,       # H
            item_width=12,       # w
            item_height=5        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 25

    def test_caso_16(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=48,        # W
            bin_height=24,       # H
            item_width=8,        # w
            item_height=6        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 24

    def test_caso_17(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=70,        # W
            bin_height=28,       # H
            item_width=14,       # w
            item_height=7        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 20

    def test_caso_18(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            bin_width=10,        # W
            bin_height=30,       # H
            item_width=1,        # w
            item_height=6        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 50


