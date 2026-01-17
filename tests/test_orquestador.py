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

    def test_caso_nuevo_optimo_6(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=6,   # N
            binWidth=6,        # W
            binHeight=6,       # H
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
        assert objectiveValue == 6  # Valor óptimo esperado
        

    def test_caso_3(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=8,   # N
            binWidth=6,        # W
            binHeight=6,       # H
            itemWidth=4,       # w
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
        assert objectiveValue == 4
        
    def test_caso_4(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=5,   # N
            binWidth=7,        # W
            binHeight=3,       # H
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
        assert objectiveValue == 3

    def test_caso_5(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=6,   # N
            binWidth=6,        # W
            binHeight=3,       # H
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
        assert objectiveValue == 3

    def test_caso_6(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=10,   # N
            binWidth=120,       # W
            binHeight=20,       # H
            itemWidth=12,       # w
            itemHeight=8        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        assert objectiveValue == 10
    
    # Desde acá empiezan los casos de la OR Library (grandes)

    def test_caso_7(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=14,   # N
            binWidth=50,        # W
            binHeight=20,       # H
            itemWidth=13,       # w
            itemHeight=8        # h
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
            itemsQuantity=18,   # N
            binWidth=40,        # W
            binHeight=25,       # H
            itemWidth=10,       # w
            itemHeight=6        # h
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
            itemsQuantity=22,   # N
            binWidth=60,        # W
            binHeight=20,       # H
            itemWidth=12,       # w
            itemHeight=7        # h
        )

        objectiveValue = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData
        )

        assert objectiveValue is not None
        #TODO: Agregar el assert con el valor objetivo

    def test_caso_10(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=15,   # N
            binWidth=45,        # W
            binHeight=30,       # H
            itemWidth=9,        # w
            itemHeight=9        # h
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
            itemsQuantity=28,   # N
            binWidth=70,        # W
            binHeight=25,       # H
            itemWidth=14,       # w
            itemHeight=8        # h
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
            itemsQuantity=20,   # N
            binWidth=55,        # W
            binHeight=22,       # H
            itemWidth=11,       # w
            itemHeight=6        # h
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
            itemsQuantity=25,   # N
            binWidth=20,        # W
            binHeight=20,       # H
            itemWidth=6,        # w
            itemHeight=5        # h
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
            itemsQuantity=25,   # N
            binWidth=40,        # W
            binHeight=30,       # H
            itemWidth=10,       # w
            itemHeight=7        # h
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
            itemsQuantity=30,   # N
            binWidth=60,        # W
            binHeight=25,       # H
            itemWidth=12,       # w
            itemHeight=5        # h
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
            itemsQuantity=18,   # N
            binWidth=48,        # W
            binHeight=24,       # H
            itemWidth=8,        # w
            itemHeight=6        # h
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

    def test_caso_17(self, orquestador_context):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        configData = ConfigData(
            itemsQuantity=40,   # N
            binWidth=70,        # W
            binHeight=28,       # H
            itemWidth=14,       # w
            itemHeight=7        # h
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
            itemsQuantity=100,  # N
            binWidth=10,        # W
            binHeight=30,       # H
            itemWidth=1,        # w
            itemHeight=6        # h
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


