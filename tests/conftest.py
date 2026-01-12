import multiprocessing
import pytest

@pytest.fixture(scope="class")
def orquestador_context():
    queue = multiprocessing.Queue()
    manual_interruption = multiprocessing.Value('b', True)
    execution_time = 1200

    return queue, manual_interruption, execution_time
