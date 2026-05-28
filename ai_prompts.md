# AI Prompts

Bu dosyada Programlama Dilleri ve Prensipleri (BIL206) dönem ödevi kapsamında yapay zeka araçlarından alınan destekler, kullanılan promptların özetleri ve projeye nasıl entegre edildikleri listelenmiştir.

---

## 2026-05-01 — Ödev Gereksinimlerini Anlama ve Başlangıç Planı

### Kullanılan Araç
ChatGPT 5.5

### Prompt Özeti
PDF'i incelenerek projeye nereden başlanması gerektiği sordum. Kendi programlama dilimi ve yorumlayıcısını tasarlamanın hangi aşamalardan oluştuğu hakkında destek aldım.

### Alınan Destek
Projenin dört ana aşamadan oluştuğu açıklandı Chat-GPT 5.5 tarafından:

- Dil tasarımı
- Lexer
- Parser
- Evaluator / Semantic analysis

### Entegrasyon
Bu açıklamalara göre proje adımlara böldüm ve önce Knly dilinin tasarımına bir `Interpreter.txt` dosyasına aldığım notlarla başladım. 

Bu dosya ayrıca proje iöerisinde bulunuyor, bu dilin kurallarının belirlendiği ilk taslak dosyasıdır.

---

## 2026-05-02 — Knly Dilinin Temel Yapısını Belirleme

### Kullanılan Araç
ChatGPT 5.5 

### Prompt Özeti
Knly adlı programlama dili için hangi yapıların belirlenmesi gerektiği sordum. Keyword, veri tipi, operatör, blok yapısı ve statement sonlandırma gibi temel dil kurallarının nasıl tasarlanacağı hakkında yardım aldım.

### Alınan Destek
Dilin lexer ve parser aşamalarında sorun çıkarmaması için aşağıdaki yapıların netleştirilmesi önerildi:

- Keyword listesi
- Primitive type listesi (Hangi temel değişken türleri olacağını belirledim.)
- Boolean değerleri (yes, nope olarak ayarladım.)
- Operatörler (mono, ya, say)
- Değişken isimlendirme kuralları
- String ve character yazım biçimi
- Blok başlangıç ve bitiş yapısı
- Satır sonlandırma sembolü
- If / else (ya, yoksa) ve loop syntax yapısı

### Entegrasyon
Knly dili için aşağıdaki temel tasarım kurallarını verdim:

- `new` değişken tanımlama için kullanılacak.
- `ya` koşul yapısı için kullanılacak.
- `yoksa` else yapısı için kullanılacak.
- `say` for benzeri döngü için kullanılacak.
- `continue` while benzeri döngü için kullanılacak.
- `wput` çıktı almak için kullanılacak.
- `nmb`, `str`, `tf`, `mono` primitive type olarak kullanılacak.
- `yes` ve `nope` boolean değerleri olarak kullanılacak.
- `→` atama operatörü olarak kullanılacak.
- `|` statement sonlandırıcı olarak kullanılacak.
- Backtick karakteri blok başlangıcı ve bitişi için kullanılacak.

---

## 2026-05-05 — Syntax ve EBNF Yapısının Oluşturulması

### Kullanılan Araç
ChatGPT 5.5

### Prompt Özeti
Knly dili için syntax kısmında nasıl ilerlenmesi gerektiğini ve EBNF / CFG tablosunun nasıl hazırlanacağını sordum.

### Alınan Destek
EBNF yapısının, dildeki statement kurallarını resmi grammar formatında göstermek için kullanıldığını açıkladım. Knly dilindeki değişken tanımlama, atama, çıktı alma, koşul, döngü, fonksiyon çağrısı ve expression yapıları EBNF formatına çevirdim.

### Entegrasyon
Knly için aşağıdaki grammar yapıları oluşturdum:

- `program`
- `statement`
- `variable_declaration`
- `assignment`
- `print_statement`
- `function_call`
- `if_statement`
- `for_statement`
- `while_statement`
- `block`
- `condition`
- `expression`
- `term`
- `factor`

Bu grammar yapısını README dosyasında kullanılmak üzere projeye ekledim.

---

## 2026-05-16 — Lexer Aşaması İçin Kod Desteği

### Kullanılan Araç
ChatGPT 5.5

### Prompt Özeti
Knly dili için PDF'teki Aşama 2'ye uygun bir lexer yazılmasını istedim. Lexer'ın mevcut dil tasarımına uygun olması, token üretmesi ve parser aşamasında kullanılabilecek şekilde düzenli olmasını istedim.

### Alınan Destek
Knly dili için lexer kodu oluşturdu benim için. Lexer'ın kaynak kodu karakter karakter okuyarak token listesi üretmesini sağladı yapay zeka.

Desteklenen token türleri:

- Keyword
- Type
- Identifier
- Number
- String
- Character
- Boolean
- Operator
- Punctuation
- EOF

### Entegrasyon
Aşağıdaki dosyaları projeye ekledim:

- `src/lexer.py`
- `examples/lexer_demo.knly`
- `tests/test_lexer.py`

Lexer yapısını, Knly dilindeki özel operatörleri destekleyecek şekilde düzenlendim:

- `→`
- `→→`
- `|→`
- `>→`
- `<→`

Ayrıca satır ve kolon bilgisi içeren hata mesajları ekledim.

---

## 2026-05-17 — Lexer Kodunun Test Edilmesi ve Düzenlenmesi

### Kullanılan Araç
ChatGPT Codex 5.5 Extra High

### Prompt Özeti
Lexer kodunun Knly dilinin kurallarına uygun çalışıp çalışmadığını kontrol etmek için test edilmesini istedim.

### Alınan Destek
Codex, Lexer için örnek Knly kodları ve test senaryoları hazırladı.

### Entegrasyon
Aşağıdaki yapıların doğru token üretip üretmediği test ettim:

- `new nmb x → 5|`
- `new str mesaj → "merhaba"|`
- `new tf aktif → yes|`
- `new mono harf → 'K'|`
- `wput{x}|`
- `ya x < y`
- `x → x + 1|`

Lexer çıktısının parser aşaması için uygun hale gelmesini sağladım.

---

## 2026-05-17 — Parser Aşaması İçin Kod Desteği

### Kullanılan Araç
ChatGPT Codex 5.5 Extra High

### Prompt Özeti
PDF'teki Aşama 3'e göre Knly dili için parser yazılması istendi. Parser'ın önceki lexer yapısıyla uyumlu çalışması, token listesini alarak AST üretmesi ve syntax hatalarını anlamlı şekilde göstermesini istedim.

### Alınan Destek
Parser kodunun ana taslağı Codex tarafından oluşturuldu. Recursive descent parser yaklaşımını kullandı.

Parser'ın desteklemesi istenen yapılar:

- Değişken tanımlama
- Atama
- Print statement
- If / else
- Loop yapıları
- Function call
- Expression parsing
- Operator precedence
- Syntax error handling

### Entegrasyon
Aşağıdaki dosyaları projeye ekledim:

- `src/parser.py`
- `src/ast_nodes.py`
- `examples/parser_demo.knly`
- `tests/test_parser.py`

Parser kodu Knly EBNF yapısına göre kontrol ettim ve lexer çıktısıyla uyumlu hale getirdim.

---

## 2026-05-18 — Parser Kodunu Anlama ve Projeye Uygulama

### Kullanılan Araç
ChatGPT Codex 5.5 Extra High

### Prompt Özeti
Parser kodunun nasıl çalıştığını ve projede nasıl anlatılması gerektiğini anlamak için destek alındı Codex'den.

### Alınan Destek
Parser'ın lexer'dan gelen tokenları gramer kurallarına göre nasıl kontrol ettiği ve AST oluşturduğu açıkladı bana. Recursive descent parser mantığı ve AST node yapıları hakkında özet aldım.

### Entegrasyon
Parser kısmı için proje açıklamasında şu mantığın kullandım:

Lexer kaynak kodu tokenlara ayırır. Parser bu tokenları Knly dilinin grammar kurallarına göre kontrol eder ve AST üretir. Hatalı syntax durumunda syntax error döndürür.

---

## 2026-05-19 — Evaluator ve Semantic Analysis Aşaması İçin Kod Desteği

### Kullanılan Araç
ChatGPT Codex 5.5 Extra High

### Prompt Özeti
PDF'teki Aşama 4'e göre Knly dili için semantic analysis ve evaluator kodu yazılması istendi Codex'den. Kodun önceki lexer ve parser yapısına uygun çalışması, AST'yi çalıştırması, değişkenleri bellekte tutması ve semantic hata kontrolleri yapmasını istedim prompt'da.

### Alınan Destek
Evaluator kodunun ana taslağı Codex tarafından oluşturuldu.

Evaluator'ın desteklemesi istenen yapılar:

- Environment / symbol table
- Variable declaration
- Assignment
- Arithmetic operations
- Print output
- If / else execution
- Loop execution
- Type checking
- Undefined variable error
- Type mismatch error

### Entegrasyon
Aşağıdaki dosyalar projeye eklendi:

- `src/evaluator.py`
- `tests/test_evaluator.py`

Evaluator, parser tarafından üretilen AST yapısını çalıştıracak şekilde projeye dahil eklendi, ancak sonra test edildi. Küçük bazı düzenlemeler yapıldı.

---

## 2026-05-22 — Parser ve Evaluator Kodlarının Genel Entegrasyonu

### Kullanılan Araç
ChatGPT Codex 5.5 Extra High

### Prompt Özeti
Parser ve evaluator kodlarının birlikte çalışması, lexer çıktısından başlayıp program çıktısı üretmesine kadar tüm akışın doğrulanmasını istedim.

### Alınan Destek
Lexer → Parser → Evaluator akışının tek bir çalışma düzeninde bağlanması için kontrol istedim.

### Entegrasyon
Projedeki genel çalışma akışı şu şekilde düzenlendi:

1. Knly kaynak kodu okunur.
2. Lexer kaynak kodu tokenlara ayırır.
3. Parser tokenları AST yapısına çevirir.
4. Evaluator AST'yi çalıştırır.
5. Program çıktısı terminale yazdırılır.

Bu akışın test edilmesi için örnek Knly dosyaları hazırlandı. Onlar da projede bulunuyor zaten.

---

## 2026-05-23 — AI Kullanımı ve ai_prompts.md Dosyasının Düzenlenmesi

### Kullanılan Araç
ChatGPT 5.5

### Prompt Özeti
Projede ChatGPT ve Codex kullanıldığı için ai_prompts.md dosyasının nasıl hazırlanması gerektiği soruldu. Özellikle parser ve evaluator aşamalarında Codex'ten kod desteği alındığı için bunun nasıl düzgün ve dürüst şekilde yazılacağı hakkında destek alındı.

### Alınan Destek
AI kullanımının gizlenmemesi, ancak dosyanın sadece "AI kod yazdı" şeklinde değil; prompt, alınan destek, entegrasyon ve test süreci şeklinde düzenlenmemi önerdi ChatGPT burada.

### Entegrasyon
ai_prompts.md dosyasında her destek ayrı başlık altında yazıldı tarafımca en son. Yapay zeka bana taslağı ve nasıl yazmam gerektiğini verdi. Ben de düzenledim ve adım adım yazdım. Her başlıkta:

- kullanılan araç,
- prompt özeti,
- alınan destek,
- entegrasyon

alanları kullandım.

Parser ve evaluator kodlarının ana taslağında Codex desteği alındığı açıkladım böylelikle. Ancak her adımda test, düzenlemeler, kontroller yaptım ve genel akışı aklıma anlamaya çalıştım. 

Bunun yanında proje kurallarına göre uyarlama, test etme ve entegrasyon adımlarını da ayrıca yazdım. Yapay zeka bu projede hem iskeleti kuran, hem de yaptığım projede "multiplier" görevi gören bir araçtı.
