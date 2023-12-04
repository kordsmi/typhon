from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as tmp_dir:
        yield tmp_dir
