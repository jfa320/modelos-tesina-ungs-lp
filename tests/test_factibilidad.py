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

    def get_posicion_x(self):
        return self.x

    def get_posicion_y(self):
        return self.y

    def get_ancho(self):
        return self.ancho

    def get_alto(self):
        return self.alto


class RebanadaDummy:
    def __init__(self, items):
        self.items = items

    def get_items(self):
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
            configData.get_bin_width(),
            configData.get_bin_height(),
            objectiveValue
        )

    def test_factibilidad_caso_1(self, orquestador_context):
        configData = ConfigData(
            bin_width=6,
            bin_height=4,
            item_width=2,
            item_height=3
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=4)

    def test_factibilidad_caso_2(self, orquestador_context):
        configData = ConfigData(
            bin_width=5,
            bin_height=5,
            item_width=3,
            item_height=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=4)

    def test_factibilidad_caso_nuevo_optimo_6(self, orquestador_context):
        configData = ConfigData(
            bin_width=6,
            bin_height=6,
            item_width=3,
            item_height=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=6)

    def test_factibilidad_caso_3(self, orquestador_context):
        configData = ConfigData(
            bin_width=6,
            bin_height=6,
            item_width=4,
            item_height=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=4)

    def test_factibilidad_caso_4(self, orquestador_context):
        configData = ConfigData(
            bin_width=7,
            bin_height=3,
            item_width=3,
            item_height=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=3)

    def test_factibilidad_caso_5(self, orquestador_context):
        configData = ConfigData(
            bin_width=6,
            bin_height=3,
            item_width=3,
            item_height=2
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=3)

    def test_factibilidad_caso_6(self, orquestador_context):
        configData = ConfigData(
            bin_width=120,
            bin_height=20,
            item_width=12,
            item_height=8
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=25)

    def test_factibilidad_caso_7(self, orquestador_context):
        configData = ConfigData(
            bin_width=50,
            bin_height=20,
            item_width=13,
            item_height=8
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=7)

    def test_factibilidad_caso_8(self, orquestador_context):
        configData = ConfigData(
            bin_width=40,
            bin_height=25,
            item_width=10,
            item_height=6
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=16)

    def test_factibilidad_caso_9(self, orquestador_context):
        configData = ConfigData(
            bin_width=60,
            bin_height=20,
            item_width=12,
            item_height=7
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=13)

    def test_factibilidad_caso_10(self, orquestador_context):
        configData = ConfigData(
            bin_width=45,
            bin_height=30,
            item_width=9,
            item_height=9
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=15)

    def test_factibilidad_caso_11(self, orquestador_context):
        configData = ConfigData(
            bin_width=70,
            bin_height=25,
            item_width=14,
            item_height=8
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=15)

    def test_factibilidad_caso_12(self, orquestador_context):
        configData = ConfigData(
            bin_width=55,
            bin_height=22,
            item_width=11,
            item_height=6
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=18)

    def test_factibilidad_caso_13(self, orquestador_context):
        configData = ConfigData(
            bin_width=20,
            bin_height=20,
            item_width=6,
            item_height=5
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=12)

    def test_factibilidad_caso_14(self, orquestador_context):
        configData = ConfigData(
            bin_width=40,
            bin_height=30,
            item_width=10,
            item_height=7
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=16)

    def test_factibilidad_caso_15(self, orquestador_context):
        configData = ConfigData(
            bin_width=60,
            bin_height=25,
            item_width=12,
            item_height=5
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=25)

    def test_factibilidad_caso_16(self, orquestador_context):
        configData = ConfigData(
            bin_width=48,
            bin_height=24,
            item_width=8,
            item_height=6
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=24)

    def test_factibilidad_caso_17(self, orquestador_context):
        configData = ConfigData(
            bin_width=70,
            bin_height=28,
            item_width=14,
            item_height=7
        )

        self.ejecutar_y_validar_factibilidad(orquestador_context, configData, valor_esperado=20)

    def test_factibilidad_caso_18(self, orquestador_context):
        configData = ConfigData(
            bin_width=10,
            bin_height=30,
            item_width=1,
            item_height=6
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
