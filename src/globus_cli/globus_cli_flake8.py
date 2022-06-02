# type: ignore
"""
A Flake8 Plugin for use in globus-cli
"""

import ast

CODEMAP = {
    "CLI001": "CLI001 import from globus_sdk module, defeats lazy importer",
}


class Plugin:
    name = "globus-cli-flake8"
    version = "0.0.1"

    # args to init determine plugin behavior. see:
    # https://flake8.pycqa.org/en/latest/internal/utils.html#flake8.utils.parameters_for
    def __init__(self, tree):
        self.tree = tree

    # Plugin.run() is how checks will run. For detail, see implementation of:
    # https://flake8.pycqa.org/en/latest/internal/checker.html#flake8.checker.FileChecker.run_ast_checks
    def run(self):
        visitor = ImportVisitor()
        visitor.visit(self.tree)
        for lineno, col, code in visitor.collect:
            yield lineno, col, CODEMAP[code], type(self)


class ErrorRecordingVisitor(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.collect = []

    def _record(self, node, code):
        self.collect.append((node.lineno, node.col_offset, code))


class ImportVisitor(ErrorRecordingVisitor):
    def visit_ImportFrom(self, node):  # a `from globus_sdk import ...` clause
        if node.module == "globus_sdk":
            self._record(node, "CLI001")
