import os
from contextlib import contextmanager


@contextmanager
def source_file(file_name, source=''):
    try:
        with open(file_name, 'w') as f:
            f.write(source)
        yield
    finally:
        os.unlink(file_name)
