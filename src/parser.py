from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any

try:
    from .lexer import LexerError, Token, TokenType, tokenize
except ImportError:
    from lexer import LexerError, Token, TokenType, tokenize


class ParserError(Exception):
    def __init__(self, message: str, token: Token) -> None:
        super().__init__(
            f"Syntax Error at line {token.line}, column {token.column}: {message}"
        )
        self.message = message
        self.token = token


class AstNode:
    def to_dict(self) -> dict[str, Any]:
        return _ast_to_dict(self)


class Statement(AstNode):
    pass


class Expression(AstNode):
    pass


@dataclass(frozen=True, slots=True)
class Program(AstNode):
    statements: list[Statement]


@dataclass(frozen=True, slots=True)
class VariableDeclaration(Statement):
    type_name: str
    name: str
    initializer: Expression


@dataclass(frozen=True, slots=True)
class Assignment(Statement):
    name: str
    value: Expression


@dataclass(frozen=True, slots=True)
class OutputStatement(Statement):
    expression: Expression


@dataclass(frozen=True, slots=True)
class FunctionCallStatement(Statement):
    name: str
    arguments: list[Expression]


@dataclass(frozen=True, slots=True)
class IfStatement(Statement):
    condition: Expression
    then_branch: list[Statement]
    else_branch: list[Statement] | None = None


@dataclass(frozen=True, slots=True)
class WhileStatement(Statement):
    condition: Expression
    body: list[Statement]


@dataclass(frozen=True, slots=True)
class ForStatement(Statement):
    initializer: VariableDeclaration | Assignment
    condition: Expression
    increment: Assignment
    body: list[Statement]


@dataclass(frozen=True, slots=True)
class BinaryExpression(Expression):
    left: Expression
    operator: str
    right: Expression


@dataclass(frozen=True, slots=True)
class UnaryExpression(Expression):
    operator: str
    right: Expression


@dataclass(frozen=True, slots=True)
class GroupingExpression(Expression):
    expression: Expression


@dataclass(frozen=True, slots=True)
class LiteralExpression(Expression):
    value: int | float | str | bool
    literal_type: str


@dataclass(frozen=True, slots=True)
class VariableExpression(Expression):
    name: str


def _ast_to_dict(value: Any) -> Any:
    if isinstance(value, list):
        return [_ast_to_dict(item) for item in value]

    if is_dataclass(value):
        result: dict[str, Any] = {"kind": value.__class__.__name__}
        for field in fields(value):
            result[field.name] = _ast_to_dict(getattr(value, field.name))
        return result

    return value


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        statements: list[Statement] = []

        while not self._is_at_end():
            statements.append(self._statement())

        return Program(statements)

    def _statement(self) -> Statement:
        if self._match_keyword("new"):
            return self._variable_declaration(require_terminator=True)

        if self._match_keyword("ya"):
            return self._if_statement()

        if self._match_keyword("continue"):
            return self._while_statement()

        if self._match_keyword("say"):
            return self._for_statement()

        if self._match_keyword("wput"):
            return self._output_statement()

        if self._check(TokenType.IDENTIFIER):
            if self._check_next(TokenType.OPERATOR, "→"):
                return self._assignment(require_terminator=True)
            if self._check_next(TokenType.PUNCTUATION, "{"):
                return self._function_call_statement()

        if self._check(TokenType.PUNCTUATION, "`"):
            raise self._error("Unexpected block end '`'.")

        raise self._error("Expected a statement.")

    def _variable_declaration(self, require_terminator: bool) -> VariableDeclaration:
        type_token = self._consume(TokenType.TYPE, "Expected a type after 'new'.")
        name = self._consume(
            TokenType.IDENTIFIER, "Expected a variable name after the type."
        )
        self._consume_operator("→", "Expected assignment operator '→'.")
        initializer = self._expression()

        if require_terminator:
            self._consume_terminator("Expected '|' after variable declaration.")

        return VariableDeclaration(type_token.lexeme, name.lexeme, initializer)

    def _assignment(self, require_terminator: bool) -> Assignment:
        name = self._consume(TokenType.IDENTIFIER, "Expected a variable name.")
        self._consume_operator("→", "Expected assignment operator '→'.")
        value = self._expression()

        if require_terminator:
            self._consume_terminator("Expected '|' after assignment.")

        return Assignment(name.lexeme, value)

    def _output_statement(self) -> OutputStatement:
        self._consume_punctuation("{", "Expected '{' after 'wput'.")
        expression = self._expression()
        self._consume_punctuation("}", "Expected '}' after output expression.")
        self._consume_terminator("Expected '|' after output statement.")
        return OutputStatement(expression)

    def _function_call_statement(self) -> FunctionCallStatement:
        name = self._consume(TokenType.IDENTIFIER, "Expected a function name.")
        arguments = self._argument_list()
        self._consume_terminator("Expected '|' after function call.")
        return FunctionCallStatement(name.lexeme, arguments)

    def _if_statement(self) -> IfStatement:
        condition = self._expression()
        then_branch = self._block("Expected '`' to start the 'ya' block.")
        else_branch = None

        if self._match_keyword("yoksa"):
            else_branch = self._block("Expected '`' to start the 'yoksa' block.")

        return IfStatement(condition, then_branch, else_branch)

    def _while_statement(self) -> WhileStatement:
        condition = self._expression()
        body = self._block("Expected '`' to start the 'continue' block.")
        return WhileStatement(condition, body)

    def _for_statement(self) -> ForStatement:
        if self._match_keyword("new"):
            initializer = self._variable_declaration(require_terminator=False)
        else:
            initializer = self._assignment(require_terminator=False)

        self._consume_punctuation(",", "Expected ',' after 'say' initializer.")
        condition = self._expression()
        self._consume_punctuation(",", "Expected ',' after 'say' condition.")
        increment = self._assignment(require_terminator=False)
        body = self._block("Expected '`' to start the 'say' block.")

        return ForStatement(initializer, condition, increment, body)

    def _block(self, start_message: str) -> list[Statement]:
        self._consume_punctuation("`", start_message)
        statements: list[Statement] = []

        while not self._check(TokenType.PUNCTUATION, "`") and not self._is_at_end():
            statements.append(self._statement())

        self._consume_punctuation("`", "Expected '`' to close the block.")
        return statements

    def _argument_list(self) -> list[Expression]:
        self._consume_punctuation("{", "Expected '{' after function name.")
        arguments: list[Expression] = []

        if not self._check(TokenType.PUNCTUATION, "}"):
            arguments.append(self._expression())
            while self._match_punctuation(","):
                arguments.append(self._expression())

        self._consume_punctuation("}", "Expected '}' after function arguments.")
        return arguments

    def _expression(self) -> Expression:
        return self._equality()

    def _equality(self) -> Expression:
        expression = self._comparison()

        while self._match_operator("→→", "|→"):
            operator = self._previous().lexeme
            right = self._comparison()
            expression = BinaryExpression(expression, operator, right)

        return expression

    def _comparison(self) -> Expression:
        expression = self._term()

        while self._match_operator(">", ">→", "<", "<→"):
            operator = self._previous().lexeme
            right = self._term()
            expression = BinaryExpression(expression, operator, right)

        return expression

    def _term(self) -> Expression:
        expression = self._factor()

        while self._match_operator("+", "-"):
            operator = self._previous().lexeme
            right = self._factor()
            expression = BinaryExpression(expression, operator, right)

        return expression

    def _factor(self) -> Expression:
        expression = self._unary()

        while self._match_operator("*", "/"):
            operator = self._previous().lexeme
            right = self._unary()
            expression = BinaryExpression(expression, operator, right)

        return expression

    def _unary(self) -> Expression:
        if self._match_operator("-"):
            operator = self._previous().lexeme
            right = self._unary()
            return UnaryExpression(operator, right)

        return self._primary()

    def _primary(self) -> Expression:
        if self._match(TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.MONO):
            token = self._previous()
            return LiteralExpression(token.literal, self._literal_type(token))

        if self._match(TokenType.IDENTIFIER):
            return VariableExpression(self._previous().lexeme)

        if self._match_punctuation("("):
            expression = self._expression()
            self._consume_punctuation(")", "Expected ')' after expression.")
            return GroupingExpression(expression)

        raise self._error("Expected an expression.")

    def _consume(
        self, token_type: TokenType, message: str, lexeme: str | None = None
    ) -> Token:
        if self._check(token_type, lexeme):
            return self._advance()
        raise self._error(message)

    def _consume_operator(self, operator: str, message: str) -> Token:
        return self._consume(TokenType.OPERATOR, message, operator)

    def _consume_punctuation(self, punctuation: str, message: str) -> Token:
        return self._consume(TokenType.PUNCTUATION, message, punctuation)

    def _consume_terminator(self, message: str) -> Token:
        return self._consume_punctuation("|", message)

    def _match(self, *token_types: TokenType) -> bool:
        for token_type in token_types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _match_keyword(self, keyword: str) -> bool:
        if self._check(TokenType.KEYWORD, keyword):
            self._advance()
            return True
        return False

    def _match_operator(self, *operators: str) -> bool:
        if self._check(TokenType.OPERATOR) and self._peek().lexeme in operators:
            self._advance()
            return True
        return False

    def _match_punctuation(self, punctuation: str) -> bool:
        if self._check(TokenType.PUNCTUATION, punctuation):
            self._advance()
            return True
        return False

    def _check(self, token_type: TokenType, lexeme: str | None = None) -> bool:
        if self._is_at_end():
            return False

        token = self._peek()
        if token.type != token_type:
            return False

        return lexeme is None or token.lexeme == lexeme

    def _check_next(self, token_type: TokenType, lexeme: str | None = None) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False

        token = self.tokens[self.current + 1]
        if token.type != token_type:
            return False

        return lexeme is None or token.lexeme == lexeme

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _error(self, message: str) -> ParserError:
        return ParserError(message, self._peek())

    @staticmethod
    def _literal_type(token: Token) -> str:
        if token.type == TokenType.NUMBER:
            return "nmb"
        if token.type == TokenType.STRING:
            return "str"
        if token.type == TokenType.BOOLEAN:
            return "tf"
        if token.type == TokenType.MONO:
            return "mono"
        raise ValueError(f"Unsupported literal token type: {token.type}")


def parse(source: str) -> Program:
    return Parser(tokenize(source)).parse()


def _configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _configure_output()

    parser = argparse.ArgumentParser(description="Parse Knly source code into an AST.")
    parser.add_argument("file", nargs="?", help="Path to a .knly source file.")
    parser.add_argument("-c", "--code", help="Parse this source string instead of a file.")
    parser.add_argument("--json", action="store_true", help="Print the AST as JSON.")
    args = parser.parse_args(argv)

    if args.code is not None:
        source = args.code
    elif args.file:
        source = Path(args.file).read_text(encoding="utf-8")
    else:
        parser.error("provide a source file or --code")

    try:
        program = parse(source)
    except (LexerError, ParserError) as error:
        print(error, file=sys.stderr)
        return 1

    print(json.dumps(program.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
