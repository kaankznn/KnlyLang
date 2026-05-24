# Knly Language 

Knly, Programlama Dilleri ve Prensipleri dönem ödevi için tasarlanan bir yorumlanan programlama dilidir.
Bu aşamada proje Lexer, Parser ve Evaluator modullerini içerir.

## Dil Özellikleri 🔧

- Değişken tanımlama: `new`
- Koşul: `ya`, `yoksa`
- For döngüsü: `say`
- While döngüsü: `continue`
- Çikti: `wput`
- Satir bitirme: `|`
- Blok başlatma ve bitirme: backtick, yani `` ` ``
- Veri tipleri: `nmb`, `str`, `tf`, `mono`
- Boolean değerleri: `yes`, `nope`

## Gramer 📄

```ebnf
program        ::= statement* EOF ;

statement      ::= variableDecl
                 | assignment
                 | outputStmt
                 | functionCall
                 | ifStmt
                 | whileStmt
                 | forStmt ;

variableDecl   ::= "new" type IDENTIFIER "→" expression "|" ;
assignment     ::= IDENTIFIER "→" expression "|" ;
outputStmt     ::= "wput" "{" expression "}" "|" ;
functionCall   ::= IDENTIFIER "{" arguments? "}" "|" ;

ifStmt         ::= "ya" expression block ("yoksa" block)? ;
whileStmt      ::= "continue" expression block ;
forStmt        ::= "say" forInit "," expression "," assignmentNoEnd block ;
forInit        ::= variableDeclNoEnd | assignmentNoEnd ;

block          ::= "`" statement* "`" ;
arguments      ::= expression ("," expression)* ;

type           ::= "nmb" | "str" | "tf" | "mono" ;

expression     ::= equality ;
equality       ::= comparison (("→→" | "|→") comparison)* ;
comparison     ::= term ((">" | ">→" | "<" | "<→") term)* ;
term           ::= factor (("+" | "-") factor)* ;
factor         ::= unary (("*" | "/") unary)* ;
unary          ::= "-" unary | primary ;
primary        ::= NUMBER | STRING | BOOLEAN | MONO | IDENTIFIER | "(" expression ")" ;
```

For döngüsü şu formu kullanir:

```knly
say i → 0, i < 5, i → i + 1 `
    wput{i}|
`
```

## Klasör Yapısı 📁

- `src/lexer.py`: Kaynak kodu token dizisine çevirir.
- `src/parser.py`: Token dizisini gramer kurallarina göre AST'ye çevirir.
- `src/evaluator.py`: AST'yi semantic kontrollere göre çalıştırır.
- `examples/`: Knly dilinde yazilmis örnek kodlar.
- `tests/`: Lexer, Parser ve Evaluator birim testleri.
- `ai_prompts.md`: Yapay zeka kullanim kaydi.

## Çalıstırma ⚙️

Lexer için:

```powershell
python src\lexer.py examples\lexer_test.knly
python src\lexer.py examples\lexer_test.knly --json
```

Parser için:

```powershell
python src\parser.py examples\parser_test.knly
python src\parser.py --code "new nmb x → 5|"
```

Evaluator için:

```powershell
python src\evaluator.py examples\lexer_test.knly
python src\evaluator.py examples\parser_test.knly
python src\evaluator.py examples\control_akisi.knly
python src\evaluator.py examples\control_akisi.knly --json
```

Testler:

```powershell
python -B -m unittest
```

Ayrıca tasarladığım dil python kütüphanelerini barındıran herhangi bir OS üzerinde de çalışacaktır. Örnek olarak Powershell kullandım ben. Ancak cross-platform sorun çıkarmayacağını varsayıyorum.
