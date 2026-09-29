"""Evaluates the worked-example arithmetic ourselves: models slip on math.

Only numbers, names defined earlier, + - * / ** and a few functions are
allowed; anything else is rejected, so the model's text is never executed.
"""

import ast
import math
import operator

_BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}
_FUNCTIONS = {
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "abs": abs,
    "min": min,
    "max": max,
}
_MAX_POWER = 100


def evaluate(expression: str, names: dict[str, float]) -> float:
    tree = ast.parse(expression, mode="eval")
    return float(_eval(tree.body, names))


def _eval(node: ast.AST, names: dict[str, float]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in names:
            raise ValueError(f"Unknown name '{node.id}'.")
        return names[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
        left, right = _eval(node.left, names), _eval(node.right, names)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_POWER:
            raise ValueError("Exponent too large.")
        return _BINARY[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand, names))
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCTIONS
        and not node.keywords
    ):
        return _FUNCTIONS[node.func.id](*(_eval(arg, names) for arg in node.args))
    raise ValueError(f"Not allowed: {ast.unparse(node)}")
