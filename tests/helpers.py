import os
from contextlib import contextmanager


@contextmanager
def source_file(file_name, source='', directory: str = None):
    if directory:
        file_name = os.path.join(directory, file_name)

    try:
        with open(file_name, 'w') as f:
            f.write(source)
        yield
    finally:
        os.unlink(file_name)


@contextmanager
def make_package(package_name: str, direcotry: str = None):
    if direcotry:
        package_name = os.path.join(direcotry, package_name)
    os.mkdir(package_name)
    yield package_name
