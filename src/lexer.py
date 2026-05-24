from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class TokenType(str, Enum):
    KEYWORD = "KEYWORD"
    TYPE = "TYPE"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    MONO = "MONO"
    OPERATOR = "OPERATOR"
    PUNCTUATION = "PUNCTUATION"
    EOF = "EOF"


@dataclass(frozen=True, slots=True)
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    line: int
    column: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = self.type.value
        return data


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"Lexer error at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column


class Lexer:
    KEYWORDS = {"new", "ya", "yoksa", "say", "continue", "wput"}
    TYPES = {"nmb", "str", "tf", "mono"}
    BOOLEANS = {"yes": True, "nope": False}

    MULTI_CHAR_OPERATORS = {"→→", "|→", ">→", "<→"}
    SINGLE_CHAR_OPERATORS = {"→", "<", ">", "+", "-", "*", "/"}
    PUNCTUATION = {"|", "`", "(", ")", "{", "}", ","}

    def __init__(self, source: str) -> None:
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.start_line = 1
        self.start_column = 1

    def scan_tokens(self, include_eof: bool = True) -> list[Token]:
        while not self._is_at_end():
            self.start = self.current
            self.start_line = self.line
            self.start_column = self.column
            self._scan_token()

        if include_eof:
            self.tokens.append(Token(TokenType.EOF, "", None, self.line, self.column))

        return self.tokens

    def _scan_token(self) -> None:
        char = self._advance()

        if char in {" ", "\t", "\r", "\n"}:
            return

        pair = char + self._peek()
        if pair in self.MULTI_CHAR_OPERATORS:
            self._advance()
            self._add_token(TokenType.OPERATOR)
            return

        if char in self.SINGLE_CHAR_OPERATORS:
            self._add_token(TokenType.OPERATOR)
            return

        if char in self.PUNCTUATION:
            self._add_token(TokenType.PUNCTUATION)
            return

        if char == '"':
            self._string()
            return

        if char == "'":
            self._mono()
            return

        if char.isdigit():
            self._number()
            return

        if self._is_identifier_start(char):
            self._identifier()
            return

        raise self._error(f"Unexpected character {char!r}.")

    def _identifier(self) -> None:
        while self._is_identifier_part(self._peek()):
            self._advance()

        text = self._current_lexeme()

        if text in self.KEYWORDS:
            self._add_token(TokenType.KEYWORD)
        elif text in self.TYPES:
            self._add_token(TokenType.TYPE)
        elif text in self.BOOLEANS:
            self._add_token(TokenType.BOOLEAN, self.BOOLEANS[text])
        else:
            self._add_token(TokenType.IDENTIFIER)

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()

        is_float = False
        if self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()

        if self._is_identifier_start(self._peek()):
            raise self._error("Numbers cannot be followed directly by letters or underscores.")

        text = self._current_lexeme()
        literal: int | float = float(text) if is_float else int(text)
        self._add_token(TokenType.NUMBER, literal)

    def _string(self) -> None:
        value_start = self.current

        while self._peek() != '"' and not self._is_at_end():
            if self._peek() == "\n":
                raise self._error("String literals must end before a new line.")
            self._advance()

        if self._is_at_end():
            raise self._error("Unterminated string literal.")

        value = self.source[value_start:self.current]
        self._advance()
        self._add_token(TokenType.STRING, value)

    def _mono(self) -> None:
        if self._is_at_end() or self._peek() in {"\n", "\r"}:
            raise self._error("Unterminated mono literal.")

        value = self._advance()

        if self._peek() != "'":
            while not self._is_at_end() and self._peek() not in {"'", "\n", "\r"}:
                self._advance()
            if self._peek() == "'":
                self._advance()
            raise self._error("Mono literals must contain exactly one character.")

        self._advance()
        self._add_token(TokenType.MONO, value)

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _add_token(self, token_type: TokenType, literal: Any = None) -> None:
        self.tokens.append(
            Token(
                type=token_type,
                lexeme=self._current_lexeme(),
                literal=literal,
                line=self.start_line,
                column=self.start_column,
            )
        )

    def _current_lexeme(self) -> str:
        return self.source[self.start:self.current]

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _error(self, message: str) -> LexerError:
        return LexerError(message, self.start_line, self.start_column)

    @staticmethod
    def _is_identifier_start(char: str) -> bool:
        return char == "_" or char.isalpha()

    @classmethod
    def _is_identifier_part(cls, char: str) -> bool:
        return cls._is_identifier_start(char) or char.isdigit()


def tokenize(source: str, include_eof: bool = True) -> list[Token]:
    return Lexer(source).scan_tokens(include_eof=include_eof)


def _format_literal(value: Any) -> str:
    if value is None:
        return ""
    return repr(value)


def _print_table(tokens: list[Token]) -> None:
    rows = [
        (
            token.type.value,
            repr(token.lexeme),
            _format_literal(token.literal),
            str(token.line),
            str(token.column),
        )
        for token in tokens
    ]
    headers = ("TYPE", "LEXEME", "LITERAL", "LINE", "COLUMN")
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def _configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _configure_output()

    parser = argparse.ArgumentParser(description="Tokenize Knly source code.")
    parser.add_argument("file", nargs="?", help="Path to a .knly source file.")
    parser.add_argument("-c", "--code", help="Tokenize this source string instead of a file.")
    parser.add_argument("--json", action="store_true", help="Print tokens as JSON.")
    parser.add_argument("--no-eof", action="store_true", help="Do not print the EOF token.")
    args = parser.parse_args(argv)

    if args.code is not None:
        source = args.code
    elif args.file:
        source = Path(args.file).read_text(encoding="utf-8")
    else:
        parser.error("provide a source file or --code")

    try:
        tokens = tokenize(source, include_eof=not args.no_eof)
    except LexerError as error:
        print(error, file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps([token.to_dict() for token in tokens], ensure_ascii=False, indent=2))
    else:
        _print_table(tokens)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
