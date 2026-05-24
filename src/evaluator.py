from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    from .lexer import LexerError
    from .parser import (
        Assignment,
        BinaryExpression,
        ForStatement,
        FunctionCallStatement,
        GroupingExpression,
        IfStatement,
        LiteralExpression,
        OutputStatement,
        ParserError,
        Program,
        UnaryExpression,
        VariableDeclaration,
        VariableExpression,
        WhileStatement,
        parse,
    )
except ImportError:
    from lexer import LexerError
    from parser import (
        Assignment,
        BinaryExpression,
        ForStatement,
        FunctionCallStatement,
        GroupingExpression,
        IfStatement,
        LiteralExpression,
        OutputStatement,
        ParserError,
        Program,
        UnaryExpression,
        VariableDeclaration,
        VariableExpression,
        WhileStatement,
        parse,
    )


class SemanticError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class RuntimeValue:
    type_name: str
    value: int | float | str | bool

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "value": self.value}


@dataclass(slots=True)
class RuntimeVariable:
    type_name: str
    value: int | float | str | bool

    def to_runtime_value(self) -> RuntimeValue:
        return RuntimeValue(self.type_name, self.value)

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type_name, "value": self.value}


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    output: list[str]
    environment: dict[str, RuntimeVariable]

    def to_dict(self) -> dict[str, Any]:
        return {
            "output": self.output,
            "environment": {
                name: variable.to_dict()
                for name, variable in sorted(self.environment.items())
            },
        }


BuiltinFunction = Callable[[list[RuntimeValue]], None]


class Evaluator:
    def __init__(self, max_loop_iterations: int = 10_000) -> None:
        self.environment: dict[str, RuntimeVariable] = {}
        self.output: list[str] = []
        self.max_loop_iterations = max_loop_iterations
        self.builtins: dict[str, BuiltinFunction] = {
            "log": self._builtin_output,
            "rapor": self._builtin_output,
        }

    def execute(self, program: Program) -> ExecutionResult:
        for statement in program.statements:
            self._execute_statement(statement)

        return ExecutionResult(self.output.copy(), self.environment.copy())

    def _execute_statement(self, statement: Any) -> None:
        if isinstance(statement, VariableDeclaration):
            self._execute_variable_declaration(statement)
            return

        if isinstance(statement, Assignment):
            self._execute_assignment(statement)
            return

        if isinstance(statement, OutputStatement):
            value = self._evaluate(statement.expression)
            self.output.append(self._format_value(value))
            return

        if isinstance(statement, FunctionCallStatement):
            self._execute_function_call(statement)
            return

        if isinstance(statement, IfStatement):
            self._execute_if(statement)
            return

        if isinstance(statement, WhileStatement):
            self._execute_while(statement)
            return

        if isinstance(statement, ForStatement):
            self._execute_for(statement)
            return

        raise SemanticError(f"Unsupported statement: {statement.__class__.__name__}")

    def _execute_variable_declaration(self, statement: VariableDeclaration) -> None:
        if statement.name in self.environment:
            raise SemanticError(f"Variable '{statement.name}' is already declared.")

        value = self._evaluate(statement.initializer)
        self._ensure_assignable(statement.type_name, value)
        self.environment[statement.name] = RuntimeVariable(
            statement.type_name, value.value
        )

    def _execute_assignment(self, statement: Assignment) -> None:
        if statement.name not in self.environment:
            raise SemanticError(f"Variable '{statement.name}' is not declared.")

        variable = self.environment[statement.name]
        value = self._evaluate(statement.value)
        self._ensure_assignable(variable.type_name, value)
        variable.value = value.value

    def _execute_function_call(self, statement: FunctionCallStatement) -> None:
        function = self.builtins.get(statement.name)
        if function is None:
            raise SemanticError(f"Function '{statement.name}' is not defined.")

        arguments = [self._evaluate(argument) for argument in statement.arguments]
        function(arguments)

    def _execute_if(self, statement: IfStatement) -> None:
        condition = self._evaluate(statement.condition)
        self._ensure_type(condition, "tf", "If condition must be a boolean value.")

        branch = statement.then_branch if condition.value else statement.else_branch
        if branch is None:
            return

        self._execute_block(branch)

    def _execute_while(self, statement: WhileStatement) -> None:
        iterations = 0

        while True:
            condition = self._evaluate(statement.condition)
            self._ensure_type(
                condition, "tf", "While condition must be a boolean value."
            )
            if not condition.value:
                break

            self._guard_loop(iterations)
            self._execute_block(statement.body)
            iterations += 1

    def _execute_for(self, statement: ForStatement) -> None:
        if isinstance(statement.initializer, VariableDeclaration):
            self._execute_variable_declaration(statement.initializer)
        else:
            self._execute_assignment(statement.initializer)

        iterations = 0
        while True:
            condition = self._evaluate(statement.condition)
            self._ensure_type(condition, "tf", "For condition must be a boolean value.")
            if not condition.value:
                break

            self._guard_loop(iterations)
            self._execute_block(statement.body)
            self._execute_assignment(statement.increment)
            iterations += 1

    def _execute_block(self, statements: list[Any]) -> None:
        for statement in statements:
            self._execute_statement(statement)

    def _evaluate(self, expression: Any) -> RuntimeValue:
        if isinstance(expression, LiteralExpression):
            return RuntimeValue(expression.literal_type, expression.value)

        if isinstance(expression, VariableExpression):
            variable = self.environment.get(expression.name)
            if variable is None:
                raise SemanticError(f"Variable '{expression.name}' is not declared.")
            return variable.to_runtime_value()

        if isinstance(expression, GroupingExpression):
            return self._evaluate(expression.expression)

        if isinstance(expression, UnaryExpression):
            return self._evaluate_unary(expression)

        if isinstance(expression, BinaryExpression):
            return self._evaluate_binary(expression)

        raise SemanticError(f"Unsupported expression: {expression.__class__.__name__}")

    def _evaluate_unary(self, expression: UnaryExpression) -> RuntimeValue:
        right = self._evaluate(expression.right)

        if expression.operator == "-":
            self._ensure_type(right, "nmb", "Unary '-' can only be used with numbers.")
            return RuntimeValue("nmb", -right.value)

        raise SemanticError(f"Unsupported unary operator '{expression.operator}'.")

    def _evaluate_binary(self, expression: BinaryExpression) -> RuntimeValue:
        left = self._evaluate(expression.left)
        right = self._evaluate(expression.right)
        operator = expression.operator

        if operator in {"+", "-", "*", "/"}:
            return self._evaluate_math(left, operator, right)

        if operator in {"<", ">", "<→", ">→"}:
            return self._evaluate_comparison(left, operator, right)

        if operator in {"→→", "|→"}:
            return self._evaluate_equality(left, operator, right)

        raise SemanticError(f"Unsupported binary operator '{operator}'.")

    def _evaluate_math(
        self, left: RuntimeValue, operator: str, right: RuntimeValue
    ) -> RuntimeValue:
        self._ensure_type(left, "nmb", f"Operator '{operator}' requires numbers.")
        self._ensure_type(right, "nmb", f"Operator '{operator}' requires numbers.")

        if operator == "+":
            return RuntimeValue("nmb", left.value + right.value)
        if operator == "-":
            return RuntimeValue("nmb", left.value - right.value)
        if operator == "*":
            return RuntimeValue("nmb", left.value * right.value)
        if operator == "/":
            if right.value == 0:
                raise SemanticError("Division by zero.")
            return RuntimeValue("nmb", left.value / right.value)

        raise SemanticError(f"Unsupported math operator '{operator}'.")

    def _evaluate_comparison(
        self, left: RuntimeValue, operator: str, right: RuntimeValue
    ) -> RuntimeValue:
        self._ensure_type(left, "nmb", f"Operator '{operator}' requires numbers.")
        self._ensure_type(right, "nmb", f"Operator '{operator}' requires numbers.")

        if operator == "<":
            result = left.value < right.value
        elif operator == ">":
            result = left.value > right.value
        elif operator == "<→":
            result = left.value <= right.value
        elif operator == ">→":
            result = left.value >= right.value
        else:
            raise SemanticError(f"Unsupported comparison operator '{operator}'.")

        return RuntimeValue("tf", result)

    def _evaluate_equality(
        self, left: RuntimeValue, operator: str, right: RuntimeValue
    ) -> RuntimeValue:
        if left.type_name != right.type_name:
            raise SemanticError(
                f"Cannot compare '{left.type_name}' with '{right.type_name}'."
            )

        if operator == "→→":
            return RuntimeValue("tf", left.value == right.value)
        if operator == "|→":
            return RuntimeValue("tf", left.value != right.value)

        raise SemanticError(f"Unsupported equality operator '{operator}'.")

    def _ensure_assignable(self, target_type: str, value: RuntimeValue) -> None:
        if target_type == "nmb" and value.type_name == "nmb":
            return
        if target_type == "str" and value.type_name == "str":
            return
        if target_type == "tf" and value.type_name == "tf":
            return
        if target_type == "mono" and value.type_name == "mono":
            if isinstance(value.value, str) and len(value.value) == 1:
                return
            raise SemanticError("Type 'mono' requires exactly one character.")

        raise SemanticError(
            f"Cannot assign value of type '{value.type_name}' to '{target_type}'."
        )

    @staticmethod
    def _ensure_type(value: RuntimeValue, expected_type: str, message: str) -> None:
        if value.type_name != expected_type:
            raise SemanticError(message)

    def _guard_loop(self, iterations: int) -> None:
        if iterations >= self.max_loop_iterations:
            raise SemanticError(
                f"Loop exceeded {self.max_loop_iterations} iterations."
            )

    def _builtin_output(self, arguments: list[RuntimeValue]) -> None:
        self.output.append(" ".join(self._format_value(argument) for argument in arguments))

    @staticmethod
    def _format_value(value: RuntimeValue) -> str:
        if value.type_name == "tf":
            return "yes" if value.value else "nope"
        if value.type_name == "nmb" and isinstance(value.value, float):
            if value.value.is_integer():
                return str(int(value.value))
        return str(value.value)


def run(source: str) -> ExecutionResult:
    return Evaluator().execute(parse(source))


def _configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _configure_output()

    parser = argparse.ArgumentParser(description="Run Knly source code.")
    parser.add_argument("file", nargs="?", help="Path to a .knly source file.")
    parser.add_argument("-c", "--code", help="Run this source string instead of a file.")
    parser.add_argument("--json", action="store_true", help="Print output and environment as JSON.")
    args = parser.parse_args(argv)

    if args.code is not None:
        source = args.code
    elif args.file:
        source = Path(args.file).read_text(encoding="utf-8")
    else:
        parser.error("provide a source file or --code")

    try:
        result = run(source)
    except (LexerError, ParserError, SemanticError) as error:
        print(error, file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        for line in result.output:
            print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

