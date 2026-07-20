# Catalogo compartido de instancias para los modelos y PAVER.

DEFAULT_CASE_NAME = "caso7"

INSTANCES = {
    "caso1": {
        "bin_width": 6,
        "bin_height": 4,
        "item_width": 2,
        "item_height": 3,
        "optimum": 4,
    },
    "caso2": {
        "bin_width": 5,
        "bin_height": 5,
        "item_width": 3,
        "item_height": 2,
        "optimum": 4,
    },
    "caso3": {
        "bin_width": 6,
        "bin_height": 6,
        "item_width": 4,
        "item_height": 2,
        "optimum": 4,
    },
    "caso4": {
        "bin_width": 7,
        "bin_height": 3,
        "item_width": 3,
        "item_height": 2,
        "optimum": 3,
    },
    "caso5": {
        "bin_width": 6,
        "bin_height": 3,
        "item_width": 3,
        "item_height": 2,
        "optimum": 3,
    },
    "caso6": {
        "bin_width": 120,
        "bin_height": 20,
        "item_width": 12,
        "item_height": 8,
        "optimum": 25,
    },
    "caso7": {
        "bin_width": 50,
        "bin_height": 20,
        "item_width": 13,
        "item_height": 8,
        "optimum": 7,
    },
    "caso8": {
        "bin_width": 40,
        "bin_height": 25,
        "item_width": 10,
        "item_height": 6,
        "optimum": 16,
    },
    "caso9": {
        "bin_width": 60,
        "bin_height": 20,
        "item_width": 12,
        "item_height": 7,
        "optimum": 13,
    },
    "caso10": {
        "bin_width": 45,
        "bin_height": 30,
        "item_width": 9,
        "item_height": 9,
        "optimum": 15,
    },
    "caso11": {
        "bin_width": 70,
        "bin_height": 25,
        "item_width": 14,
        "item_height": 8,
        "optimum": 15,
    },
    "caso12": {
        "bin_width": 55,
        "bin_height": 22,
        "item_width": 11,
        "item_height": 6,
        "optimum": 18,
    },
    "caso13": {
        "bin_width": 20,
        "bin_height": 20,
        "item_width": 6,
        "item_height": 5,
        "optimum": 12,
    },
    "caso14": {
        "bin_width": 40,
        "bin_height": 30,
        "item_width": 10,
        "item_height": 7,
        "optimum": 16,
    },
    "caso15": {
        "bin_width": 60,
        "bin_height": 25,
        "item_width": 12,
        "item_height": 5,
        "optimum": 25,
    },
    "caso16": {
        "bin_width": 48,
        "bin_height": 24,
        "item_width": 8,
        "item_height": 6,
        "optimum": 24,
    },
    "caso17": {
        "bin_width": 70,
        "bin_height": 28,
        "item_width": 14,
        "item_height": 7,
        "optimum": 20,
    },
    "caso18": {
        "bin_width": 10,
        "bin_height": 30,
        "item_width": 1,
        "item_height": 6,
        "optimum": 50,
    },
}


def _normalize_instance(case_name, instance):
    return {
        "case_name": case_name,
        "bin_width": instance["bin_width"],
        "bin_height": instance["bin_height"],
        "item_width": instance["item_width"],
        "item_height": instance["item_height"],
        "optimum": instance.get("optimum"),
    }


def get_instance(case_name):
    if case_name not in INSTANCES:
        available = ", ".join(sorted(INSTANCES))
        raise ValueError(f"Instancia desconocida '{case_name}'. Disponibles: {available}")
    return _normalize_instance(case_name, INSTANCES[case_name])


def list_instance_names():
    return sorted(INSTANCES)


def set_current_instance(case_name):
    global CASE_NAME, BIN_WIDTH, BIN_HEIGHT, ITEM_WIDTH, ITEM_HEIGHT

    instance = get_instance(case_name)
    CASE_NAME = instance["case_name"]
    BIN_WIDTH = instance["bin_width"]
    BIN_HEIGHT = instance["bin_height"]
    ITEM_WIDTH = instance["item_width"]
    ITEM_HEIGHT = instance["item_height"]
    return instance


# Variables historicas para compatibilidad con scripts que todavia importan Config.*
set_current_instance(DEFAULT_CASE_NAME)
