import os
import pytest


@pytest.fixture(scope="session")
def oracle():
    if os.environ.get("BOTHACK_ORACLE") != "1":
        pytest.skip("Set BOTHACK_ORACLE=1 after tools/bootstrap.py --oracle")
    from tools.oracle import Oracle
    with Oracle() as instance:
        yield instance
