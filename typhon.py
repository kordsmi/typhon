import sys

from typhon.transpiler_project import Project


def main():
    source_name = sys.argv[1]
    project = Project()
    project.transpile_file(source_name)


if __name__ == '__main__':
    main()
