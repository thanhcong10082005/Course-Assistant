# PART 1 — Sửa Parser + Tokenizer

## 1. Mục tiêu

Sau bước này, hệ thống phải:

1. Tokenize đúng các cụm từ tiếng Việt trong miền môn học, đặc biệt:
   - `tín chỉ`
   - `môn học`
   - `bài tập lớn`
   - `tài liệu`, `quy định`, `thời hạn`, `nội dung`, `yêu cầu`
2. Parser thật sự dùng CFG đã khai báo, không chỉ chạy fallback.
3. Câu hợp lệ trả về cây cú pháp; câu không thuộc grammar trả về đúng `()`.
4. Fallback chỉ dùng cho một số pattern nội miền đã định nghĩa, không nhận mọi
   chuỗi ký tự.
5. `output/parse-results.txt` được sinh lại từ code cuối cùng.

## 2. Phạm vi file

| File | Vai trò |
|---|---|
| `src/preprocessing.py` | Chuẩn hóa, tokenize, POS, lexicon |
| `src/grammar.py` | CFG, sinh câu |
| `src/parser.py` | Parser, fallback, format cây |
| `src/main.py` | Gọi parser, sinh `parse-results.txt` |
| `input/sentences.txt` | Câu test đầu vào |
| `output/parse-results.txt` | Kết quả parse |
| `tests/test_parser.py` | Test mới (nên thêm) |

## 3. Hiện trạng và lỗi gốc

### 3.1 Tokenizer tách rời cụm từ

`Preprocessor.tokenize()` hiện dùng:

```python
tokens = re.findall(r'\b\w+\b', text)
```

Vì vậy:

```text
"tín chỉ"       -> ["tín", "chỉ"]
"môn học"       -> ["môn", "học"]
"bài tập lớn"   -> ["bài", "tập", "lớn"]
```

Trong khi grammar lại khai báo terminal dạng:

```text
NOUN -> tín_chỉ
NOUN -> môn_học
ASSIGNMENT_NAME -> bài_tập_lớn
```

Hai bên không khớp. Hệ quả là parser khó parse theo CFG và phải dựa vào
fallback.

### 3.2 Tokenizer làm mất dấu câu

Regex `\w+` loại bỏ `?`, `!`. Trong khi grammar có:

```text
WH_QUESTION -> WH_WORD NP VP ?
YES_NO_QUESTION -> NP VP ?
```

Vì token `?` không bao giờ xuất hiện, các rule này không bao giờ được dùng đúng.

### 3.3 Grammar có rule lỗi / dư thừa

- `QUESTION -> WH_PHRASE NP VP ?` nhưng **`WH_PHRASE` không được định nghĩa**.
- `ADJ -> nào` bị lặp 2 lần.
- `NOUN -> phần` bị lặp 2 lần.
- `LO_ID` sinh tới `l.o.3.5` trong khi dữ liệu môn học chỉ có tới `LO3.4`.
- Nhiều `WH_WORD` là từ đơn lẻ (`ở`, `đâu`, `bao`, `có`, `là`, `gì`, `nào`)
  nên sinh ra câu vô nghĩa.
- `S -> QUESTION` dùng một rule gần như không bao giờ parse được vì thiếu
  `WH_PHRASE`.
- `NUM` có `30`, `60`, `90` lẫn với `CHAPTER_NUM`/`WEEK_NUM`, dễ gây nhầm
  chapter/week với số phút.

### 3.4 Parser luôn trả cây nhờ fallback

Trong `Parser.parse()`:

```python
tree = self._parse_question()
if tree and self.current_pos == len(self.tokens):
    return tree, []

fallback_tree = self._parse_fallback(text)
if fallback_tree:
    return fallback_tree, []
```

`_parse_fallback()` phân loại token:

```python
else:
    category = 'NOUN'
```

và luôn tạo `ParseNode` nếu có ít nhất một token. Vì vậy các input sau đều
"parse thành công":

```text
Hôm nay thời tiết thế nào? -> (WH_QUESTION ...)
asdf qwerty zzz           -> (YES_NO_QUESTION ...)
1 2 3 4 5                 -> (YES_NO_QUESTION ...)
```

Điều này vi phạm yêu cầu: câu không hợp lệ phải xuất `()`.

### 3.5 Kết quả kiểm tra hiện tại

- `input/sentences.txt`: 34 câu dữ liệu.
- `output/parse-results.txt`: 34/34 câu đều có cây, **0 câu trả `()`**.
- Trong cây xuất hiện các token rời như `(NOUN tín) (NOUN chỉ)` thay vì
  `tín_chỉ`.
- Các câu vô nghĩa vẫn có cây.

## 4. Grammar hiện tại

Phần này ghi lại **nguyên văn** grammar đang có trong
`output/grammar.txt` / `src/grammar.py` để làm baseline trước khi sửa.

### 4.1 Tóm tắt cấu trúc

```text
S -> QUESTION | WH_QUESTION | YES_NO_QUESTION
QUESTION -> WH_PHRASE NP VP ?          # WH_PHRASE chưa định nghĩa
WH_QUESTION -> WH_WORD NP VP ?
YES_NO_QUESTION -> NP VP ?
NP -> COURSE_NAME | CHAPTER_NUM | WEEK_NUM | TOPIC_NAME
    | ASSIGNMENT_NAME | LO_ID | PRONOUN
    | DET NOMINAL | DET | NOMINAL
VP -> VERB | VERB NP | VERB PP | VERB ADJ | VERB ADV
    | VERB NUM | VERB ADJ NP | VERB NUM NOUN
```

### 4.2 Nguyên văn `output/grammar.txt`

```text
! -> !
? -> ?
ADJ -> gì
ADJ -> nào
ADJ -> nào
ADV -> bao
ADV -> nhiêu
ADV -> không
ADV -> có
ADV -> được
ADV -> gì
ASSIGNMENT_NAME -> btl
ASSIGNMENT_NAME -> bài_tập_lớn
ASSIGNMENT_NAME -> assignment
CHAPTER_NUM -> 1
CHAPTER_NUM -> 2
CHAPTER_NUM -> 3
CHAPTER_NUM -> 4
CHAPTER_NUM -> 5
CHAPTER_NUM -> 6
CHAPTER_NUM -> 7
CHAPTER_NUM -> 8
CHAPTER_NUM -> 9
CHAPTER_NUM -> 10
CHAPTER_NUM -> 11
CHAPTER_NUM -> 12
COURSE_NAME -> nlp
COURSE_NAME -> co3085
COURSE_NAME -> xử_lý_ngôn_ngữ_tự_nhiên
DET -> các
DET -> những
DET -> nào
DET -> gì
DET -> bao
DET -> mấy
DET -> này
DET -> đó
LO_ID -> l.o.1.1
LO_ID -> l.o.1.2
LO_ID -> l.o.1.3
LO_ID -> l.o.1.4
LO_ID -> l.o.1.5
LO_ID -> l.o.2.1
LO_ID -> l.o.2.2
LO_ID -> l.o.2.3
LO_ID -> l.o.2.4
LO_ID -> l.o.2.5
LO_ID -> l.o.3.1
LO_ID -> l.o.3.2
LO_ID -> l.o.3.3
LO_ID -> l.o.3.4
LO_ID -> l.o.3.5
LO_ID -> l.o.4.1
LO_ID -> l.o.4.2
NOMINAL -> NOUN
NOMINAL -> NOUN NOUN
NOMINAL -> ADJ NOUN
NOMINAL -> NOUN ADJ
NOUN -> tín_chỉ
NOUN -> môn_học
NOUN -> chương
NOUN -> tuần
NOUN -> bài
NOUN -> nội_dung
NOUN -> tài_liệu
NOUN -> quy_định
NOUN -> deadline
NOUN -> thời_hạn
NOUN -> phần
NOUN -> phần
NOUN -> thông_tin
NOUN -> yêu_cầu
NOUN -> file
NOUN -> output
NP -> COURSE_NAME
NP -> CHAPTER_NUM
NP -> WEEK_NUM
NP -> TOPIC_NAME
NP -> ASSIGNMENT_NAME
NP -> LO_ID
NP -> PRONOUN
NP -> DET NOMINAL
NP -> DET
NP -> NOMINAL
NUM -> 1
NUM -> 2
NUM -> 3
NUM -> 4
NUM -> 5
NUM -> 6
NUM -> 7
NUM -> 8
NUM -> 9
NUM -> 10
NUM -> 11
NUM -> 12
NUM -> 13
NUM -> 14
NUM -> 15
NUM -> 30
NUM -> 60
NUM -> 90
PP -> PREP NP
PP -> PREP NOUN
PREP -> ở
PREP -> về
PREP -> của
PREP -> với
PREP -> cho
PRONOUN -> tôi
PRONOUN -> tớ
PRONOUN -> mình
PRONOUN -> nó
PRONOUN -> phần_này
PRONOUN -> chương_này
QUESTION -> WH_PHRASE NP VP ?
S -> QUESTION
S -> WH_QUESTION
S -> YES_NO_QUESTION
TOPIC_NAME -> cfg
TOPIC_NAME -> pcfg
TOPIC_NAME -> parsing
TOPIC_NAME -> semantic
TOPIC_NAME -> syntax
TOPIC_NAME -> pos
TOPIC_NAME -> feature
TOPIC_NAME -> grammar
VERB -> học
VERB -> nói
VERB -> có
VERB -> xuất
VERB -> liên_quan
VERB -> ở
VERB -> là
VERB -> cần
VERB -> muốn
VERB -> biết
VERB -> hỏi
VERB -> tra
VERB -> xem
VERB -> tìm
VERB -> yêu_cầu
VERB -> sử_dụng
VERB -> được
VP -> VERB
VP -> VERB NP
VP -> VERB PP
VP -> VERB ADJ
VP -> VERB ADV
VP -> VERB NUM
VP -> VERB ADJ NP
VP -> VERB NUM NOUN
WEEK_NUM -> 1
WEEK_NUM -> 2
WEEK_NUM -> 3
WEEK_NUM -> 4
WEEK_NUM -> 5
WEEK_NUM -> 6
WEEK_NUM -> 7
WEEK_NUM -> 8
WEEK_NUM -> 9
WEEK_NUM -> 10
WEEK_NUM -> 11
WEEK_NUM -> 12
WEEK_NUM -> 13
WEEK_NUM -> 14
WEEK_NUM -> 15
WH_QUESTION -> WH_WORD NP VP ?
WH_WORD -> môn
WH_WORD -> tuần
WH_WORD -> chương
WH_WORD -> bài
WH_WORD -> tài
WH_WORD -> quy
WH_WORD -> thời
WH_WORD -> deadline
WH_WORD -> ai
WH_WORD -> ở
WH_WORD -> đâu
WH_WORD -> bao
WH_WORD -> có
WH_WORD -> là
WH_WORD -> gì
WH_WORD -> nào
YES_NO_QUESTION -> NP VP ?
```

### 4.3 Các nhóm rule cần giữ / sửa / xóa

| Nhóm | Giữ | Sửa | Xóa |
|---|---|---|---|
| Câu hỏi | `WH_QUESTION`, `YES_NO_QUESTION` | Thêm `WH_PHRASE`, `QMARK?` | `QUESTION` nếu không dùng |
| NP | `COURSE_NAME`, `CHAPTER_NUM`, `WEEK_NUM` | Thêm `PART`, `LO_ID`, `ASSIGNMENT_NAME` | `DET` đứng một mình nếu không cần |
| VP | `VERB NP`, `VERB PP`, `VERB ADJ` | Thêm `VERB NP PP`, `VERB NP NP` có kiểm soát | Các tổ hợp sinh câu vô nghĩa |
| WH | `bao_nhiêu`, `ở_đâu`, `khi_nào` | Gộp thành `WH_PHRASE` | `WH_WORD -> ở`, `-> đâu`, `-> bao`, `-> có`, `-> là`, `-> gì`, `-> nào` |
| Số | `CHAPTER_NUM`, `WEEK_NUM` | Tách `DURATION_NUM` cho 30/60/90 | `NUM` dùng lẫn cho mọi loại |

## 5. Thiết kế đích

### 5.1 Lexicon + tokenizer theo cụm từ

Tạo `src/lexicon.py` hoặc thêm vào `preprocessing.py`:

```python
DOMAIN_LEXICON = {
    # surface form -> canonical token
    "tín chỉ": "tín_chỉ",
    "môn học": "môn_học",
    "bài tập lớn": "bài_tập_lớn",
    "bài tập": "bài_tập",
    "tài liệu": "tài_liệu",
    "quy định": "quy_định",
    "thời hạn": "thời_hạn",
    "nội dung": "nội_dung",
    "yêu cầu": "yêu_cầu",
    "liên quan": "liên_quan",
    "sử dụng": "sử_dụng",
    "bao nhiêu": "bao_nhiêu",
    "khi nào": "khi_nào",
    "ở đâu": "ở_đâu",
    "chương này": "chương_này",
    "phần này": "phần_này",
    "l.o.2.5": "lo_2_5",
    "l.o.4.2": "lo_4_2",
}
```

Yêu cầu triển khai:

1. Chuẩn hóa NFC, lowercase, gộp khoảng trắng.
2. **Longest-match** trên chuỗi ký tự, không chỉ split theo whitespace:
   - `"bài tập lớn"` phải thành 1 token, không thành 3.
   - `"bao nhiêu"` phải thành 1 token.
3. Giữ `?` và `!` thành token riêng.
4. Trả về cả dạng canonical và dạng hiển thị:

```python
@dataclass
class Token:
    text: str          # "tín chỉ"
    canonical: str     # "tín_chỉ"
    start: int
    end: int
```

5. Có hàm `detokenize(canonical_tokens)` để sinh câu tự nhiên:
   - `tín_chỉ` -> `tín chỉ`
   - `lo_2_5` -> `L.O.2.5`
   - `bài_tập_lớn` -> `bài tập lớn`
6. Không dùng `_` trong câu xuất ra `samples.txt`.

**Quan trọng:** grammar dùng canonical token (`tín_chỉ`) để parse; output câu
dùng `detokenize()` để hiển thị. Đây là cách tách "biểu diễn nội bộ" khỏi
"hình thức tự nhiên".

### 5.2 Grammar sau khi sửa

Thiết kế tối thiểu:

```text
S -> WH_QUESTION | YES_NO_QUESTION

WH_QUESTION -> WH_PHRASE NP VP QMARK?
WH_QUESTION -> WH_PHRASE VP QMARK?
YES_NO_QUESTION -> NP VP QMARK?

QMARK -> ?

WH_PHRASE -> bao_nhiêu | ở_đâu | khi_nào | gì | nào

NP -> COURSE
    | CHAPTER
    | WEEK
    | TOPIC
    | ASSIGNMENT
    | PART
    | LO
    | PRONOUN
    | DET NOMINAL
    | NOMINAL

NOMINAL -> NOUN
NOMINAL -> NOUN NOUN
NOMINAL -> ADJ NOUN

VP -> VERB
    | VERB NP
    | VERB PP
    | VERB ADJ
    | VERB NP PP
```

Quy tắc:

- Mỗi nonterminal phải có ít nhất một production.
- Không để terminal `WH_WORD` là từ đơn vô nghĩa.
- Tách `CHAPTER_NUM`, `WEEK_NUM`, `DURATION_NUM`.
- `LO` chỉ sinh các mã LO có trong dữ liệu (đọc từ KB/lexicon, không hard-code
  sai).
- `TOPIC` lấy từ danh sách topic trong KB.
- Nếu muốn giữ grammar hiện tại để so sánh, đặt nó vào
  `docs/grammar-baseline.txt`, không dùng để parse.

### 5.3 Parser thật sự dùng CFG

Có hai lựa chọn:

**Lựa chọn A — Recursive descent có backtracking (khuyến nghị cho thời gian
ngắn):**

- Mỗi nonterminal có hàm `_parse_X()`.
- Lưu `current_pos`, thử từng production, nếu fail thì `rollback`.
- Khi parse xong phải kiểm tra `current_pos == len(tokens)`.
- Không gọi fallback nếu strict parse fail, trừ khi câu khớp pattern nội miền.

**Lựa chọn B — Earley parser (khuyến nghị nếu muốn chứng minh xử lý CFG đầy
đủ):**

- Cài đặt bảng Earley cho CFG nhỏ.
- Phù hợp với grammar có đệ quy và nhập nhằng.
- Có thể thay thế recursive descent mà không đổi interface `Parser.parse()`.

Dù chọn cách nào, interface phải giữ:

```python
def parse(self, text: str) -> tuple[ParseNode | None, list[str]]:
    ...
```

và:

```python
def get_parse_result(self, text: str) -> str:
    tree, errors = self.parse(text)
    return str(tree) if tree else "()"
```

### 5.4 Fallback có kiểm soát

Fallback chỉ được dùng khi:

1. Câu khớp một pattern nội miền đã khai báo, ví dụ:
   - `^(môn|course)?\s*...\s*tín chỉ`
   - `^tuần\s+\d+\s+học`
   - `^chương\s+\d+\s+(nói|học|về)`
   - `^deadline|thời hạn`
   - `^tài liệu`
   - `^quy định`
2. Pattern đó ánh xạ được sang `intent` + `entity`.
3. Không có token lạ ngoài lexicon/stopword.

Nếu không thỏa: trả `None` -> `()`.

Fallback **không được**:

- Gán `NOUN` cho mọi token lạ.
- Tạo cây từ danh sách số.
- Nhận câu ngoài miền như "thời tiết", "asdf".
- Che giấu lỗi grammar bằng cách luôn trả cây.

### 5.5 Format cây

Giữ format hiện tại:

```text
(WH_QUESTION
  (WH_PHRASE bao_nhiêu)
  (NP (COURSE nlp))
  (VP (VERB có) (NP (NOUN tín_chỉ)))
  (QMARK ?))
```

hoặc format indent đẹp hơn, miễn:

- Có đủ nonterminal/terminal.
- Token terminal dùng canonical hoặc display nhất quán.
- Câu invalid là `()`.

## 6. Test plan

Thêm `tests/test_parser.py` (pytest) với các case:

| # | Input | Kỳ vọng |
|---|---|---|
| 1 | `Môn NLP có bao nhiêu tín chỉ?` | Có cây, có `tín_chỉ` |
| 2 | `CO3085 có mấy tín chỉ?` | Có cây |
| 3 | `Môn học gồm những phần nào?` | Có cây |
| 4 | `Tuần 3 học gì?` | Có cây, `WEEK_NUM` |
| 5 | `Chương 4 nói về gì?` | Có cây, `CHAPTER_NUM` |
| 6 | `Tài liệu về PCFG ở đâu?` | Có cây, `TOPIC pcfg` |
| 7 | `Deadline BTL là khi nào?` | Có cây |
| 8 | `Phần I của BTL là gì?` | Có cây, `PART` |
| 9 | `L.O.2.5 là gì?` | Có cây, `LO` |
| 10 | `Hôm nay thời tiết thế nào?` | `()` |
| 11 | `asdf qwerty zzz` | `()` |
| 12 | `1 2 3 4 5` | `()` |
| 13 | `Giải bài toán này giúp tôi` | `()` |
| 14 | Chuỗi rỗng | `()` |
| 15 | `Tuần 3 học gì` (không dấu `?`) | Có cây nếu `QMARK?` optional |

Ngoài ra:

- Chạy toàn bộ `input/sentences.txt`: 34/34 câu hợp lệ phải có cây.
- Tạo thêm 20 câu ngoài miền, tất cả phải `()`.
- Đảm bảo `output/parse-results.txt` không còn cây cho câu invalid.

## 7. Các bước triển khai

| Bước | Việc làm | Kết quả |
|---|---|---|
| 1 | Viết `DOMAIN_LEXICON`, tokenizer longest-match, giữ `?` | Token đúng cụm |
| 2 | Viết `detokenize()` | Câu sinh ra không có `_` |
| 3 | Sửa grammar: bỏ rule lỗi, thêm `WH_PHRASE`, `QMARK?` | Grammar hợp lệ |
| 4 | Sửa parser strict, bỏ fallback mặc định | Parse theo CFG |
| 5 | Viết fallback pattern nội miền | Chỉ nhận câu hợp lệ |
| 6 | Sửa `get_parse_result()` trả `()` | Đúng output contract |
| 7 | Thêm test, chạy `input/sentences.txt` | Pass acceptance |
| 8 | Sinh lại `output/parse-results.txt` | Output mới |

Ước lượng: **4–5 ngày** cho một người đã quen code.

## 8. Acceptance criteria

- [ ] `tín chỉ`, `môn học`, `bài tập lớn` là một token canonical.
- [ ] Tokenizer giữ được `?`/`!`.
- [ ] Grammar không còn nonterminal chưa định nghĩa.
- [ ] Parser strict parse được ít nhất 34/34 câu trong `input/sentences.txt`.
- [ ] Câu ngoài miền trả `()` (test 5 câu trở lên).
- [ ] Fallback chỉ nhận pattern nội miền; không nhận chuỗi ngẫu nhiên.
- [ ] `output/parse-results.txt` được sinh lại, không chỉnh tay.
- [ ] `pytest tests/test_parser.py` pass.

## 9. Rủi ro và lưu ý

- **Tiếng Việt không có khoảng trắng giữa từ ghép:** longest-match lexicon là
  cách đơn giản nhưng cần danh sách cụm đủ tốt. Nếu lexicon thiếu, câu đúng có
  thể bị `()`.
- **Grammar quá rộng:** dễ sinh câu đúng cú pháp nhưng sai ngữ nghĩa. Part 2 sẽ
  xử lý bằng semantic validation.
- **Grammar quá hẹp:** parser bỏ sót câu đúng. Nên giữ danh sách câu test đa
  dạng và bổ sung dần.
- **Không được dùng fallback để "chữa cháy":** nếu strict parser fail, phải
  sửa grammar/lexicon, không mở rộng fallback vô hạn.
- **Ảnh hưởng downstream:** Part 2, 3, 4, 5 đều dùng parser. Cần chốt interface
  `parse()`/`get_parse_result()` trước khi làm các part sau.
