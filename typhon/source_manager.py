class SourceManager:
    def __init__(self, project_path: str = None):
        self.project_path = project_path or '.'

    def get_package_path(self, packaage: str):
        return self.project_path
