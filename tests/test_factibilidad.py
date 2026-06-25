import time

import pytest

from Modelo_5_Orquestador import orquestador
from Objetos.ConfigData import ConfigData
from auxiliar_methods import validar_factibilidad


class ItemDummy:
    def __init__(self, x, y, ancho, alto):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto

    def getPosicionX(self):
        return self.x

    def getPosicionY(self):
        return self.y

    def getAncho(self):
        return self.ancho

    def getAlto(self):
        return self.alto


class RebanadaDummy:
    def __init__(self, items):
        self.items = items

    def getItems(self):
        return self.items


class TestFactibilidadOrquestador:
    def ejecutar_y_validar_factibilidad(self, orquestador_context, configData, valor_esperado):
        queue, manualInterruption, EXECUTION_TIME = orquestador_context

        objectiveValue, rebanadasActivas = orquestador(
            queue,
            manualInterruption,
            EXECUTION_TIME,
            time.time(),
            configData,
            devolver_solucion=True
        )

        assert objectiveValue is not None
        assert objectiveValue == valor_esperado

        validar_factibilidad(
            rebanadasActivas,
            configData.getBinWidth(),
            configData.getBinHeight(),
            objectiveValue
        )

    def test_factibilidad_caso_1(self, orquestador_context):
        configData = ConfigData(
            binWidth=6,
            binHeight=4,
            itemWidth=2,
            itemHeight=3
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=4)

    def test_factibilidad_caso_2(self, orquestador_context):
        configData = ConfigData(
            binWidth=5,
            binHeight=5,
            itemWidth=3,
            itemHeight=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=4)

    def test_factibilidad_caso_nuevo_optimo_6(self, orquestador_context):
        configData = ConfigData(
            binWidth=6,
            binHeight=6,
            itemWidth=3,
            itemHeight=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=6)

    def test_factibilidad_caso_3(self, orquestador_context):
        configData = ConfigData(
            binWidth=6,
            binHeight=6,
            itemWidth=4,
            itemHeight=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=4)

    def test_factibilidad_caso_4(self, orquestador_context):
        configData = ConfigData(
            binWidth=7,
            binHeight=3,
            itemWidth=3,
            itemHeight=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=3)

    def test_factibilidad_caso_5(self, orquestador_context):
        configData = ConfigData(
            binWidth=6,
            binHeight=3,
            itemWidth=3,
            itemHeight=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=3)

    def test_factibilidad_caso_6(self, orquestador_context):
        configData = ConfigData(
            binWidth=120,
            binHeight=20,
            itemWidth=12,
            itemHeight=8
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=25)

    def test_factibilidad_caso_7(self, orquestador_context):
        configData = ConfigData(
            binWidth=50,
            binHeight=20,
            itemWidth=13,
            itemHeight=8
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=7)

    def test_factibilidad_caso_8(self, orquestador_context):
        configData = ConfigData(
            binWidth=40,
            binHeight=25,
            itemWidth=10,
            itemHeight=6
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=16)

    def test_factibilidad_caso_9(self, orquestador_context):
        configData = ConfigData(
            binWidth=60,
            binHeight=20,
            itemWidth=12,
            itemHeight=7
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=13)

    def test_factibilidad_caso_10(self, orquestador_context):
        configData = ConfigData(
            binWidth=45,
            binHeight=30,
            itemWidth=9,
            itemHeight=9
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=15)

    def test_factibilidad_caso_11(self, orquestador_context):
        configData = ConfigData(
            binWidth=70,
            binHeight=25,
            itemWidth=14,
            itemHeight=8
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=15)

    def test_factibilidad_caso_12(self, orquestador_context):
        configData = ConfigData(
            binWidth=55,
            binHeight=22,
            itemWidth=11,
            itemHeight=6
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=18)

    def test_factibilidad_caso_13(self, orquestador_context):
        configData = ConfigData(
            binWidth=20,
            binHeight=20,
            itemWidth=6,
            itemHeight=5
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=12)

    def test_factibilidad_caso_14(self, orquestador_context):
        configData = ConfigData(
            binWidth=40,
            binHeight=30,
            itemWidth=10,
            itemHeight=7
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=16)

    def test_factibilidad_caso_15(self, orquestador_context):
        configData = ConfigData(
            binWidth=60,
            binHeight=25,
            itemWidth=12,
            itemHeight=5
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=25)

    def test_factibilidad_caso_16(self, orquestador_context):
        configData = ConfigData(
            binWidth=48,
            binHeight=24,
            itemWidth=8,
            itemHeight=6
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=24)

    def test_factibilidad_caso_17(self, orquestador_context):
        configData = ConfigData(
            binWidth=70,
            binHeight=28,
            itemWidth=14,
            itemHeight=7
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=20)

    def test_factibilidad_caso_18(self, orquestador_context):
        configData = ConfigData(
            binWidth=10,
            binHeight=30,
            itemWidth=1,
            itemHeight=6
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=50)

    def test_factibilidad_rompe_por_superposicion(self):
        rebanadas = [
            RebanadaDummy([
                ItemDummy(x=0, y=0, ancho=2, alto=2),
                ItemDummy(x=1, y=1, ancho=2, alto=2),
            ])
        ]

        with pytest.raises(AssertionError):
            validar_factibilidad(
                rebanadas,
                bin_width=5,
                bin_height=5,
                objective_value=2
            )
