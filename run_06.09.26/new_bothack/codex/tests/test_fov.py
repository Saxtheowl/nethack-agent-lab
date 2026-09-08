import random
import pytest
from dataclasses import asdict
from bothack.fov import calculate_fov
from bothack.position import Position


@pytest.mark.oracle
def test_fov_against_original_java(oracle):
    rng = random.Random(343)
    for opacity in (0, 0.1, 0.5, 0.9, 1):
        for pos in (Position(1, 1), Position(1, 21), Position(78, 21), Position(78, 1), Position(40, 12)):
            grid = [[rng.random() >= opacity for _ in range(80)] for _ in range(21)]
            assert calculate_fov(pos, grid) == oracle.call("fov", asdict(pos), grid)
