from __future__ import annotations

import ast
import json
import operator
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time. 用于回答现在几点、当前时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone, default Asia/Shanghai.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate a math expression. 用于计算数学表达式。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression, such as 123*456.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
]


def get_current_time(timezone: str = "Asia/Shanghai") -> dict:
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        timezone = "Asia/Shanghai"
        tz = timezone_utc8()

    now = datetime.now(tz)
    return {
        "timezone": timezone,
        "datetime": now.isoformat(timespec="seconds"),
        "text": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


def timezone_utc8():
    return timezone(timedelta(hours=8), name="CST")


def calculator(expression: str) -> dict:
    result = _eval_math(ast.parse(expression, mode="eval").body)
    return {"expression": expression, "result": result}


def execute_tool(name: str, arguments: str | dict | None) -> str:
    try:
        args = arguments if isinstance(arguments, dict) else json.loads(arguments or "{}")
        if name == "get_current_time":
            result = get_current_time(**args)
        elif name == "calculator":
            result = calculator(**args)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as error:
        result = {"error": str(error)}

    return json.dumps(result, ensure_ascii=False)


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_math(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        return _BINARY_OPERATORS[type(node.op)](_eval_math(node.left), _eval_math(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_eval_math(node.operand))
    raise ValueError("Only numeric expressions are supported")
