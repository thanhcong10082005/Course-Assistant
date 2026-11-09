# BÁO CÁO BÀI TẬP LỚN XỬ LÝ NGÔN NGỮ TỰ NHIÊN (CO3085)

## Trợ lý hỗ trợ học tập thông minh — Course Assistant

**Lựa chọn hướng thực hiện:** Lựa chọn 1 — Classical / Statistical NLP
(dựa trên luật, không dùng LLM thay thế các thành phần NLP cốt lõi)

**Môn học:** CO3085 — Xử lý Ngôn ngữ Tự nhiên
**Kỳ học:** HK261

## 1. Giới thiệu đề tài

### 1.1 Bối cảnh

Xử lý ngôn ngữ tự nhiên (Natural Language Processing — NLP) là lĩnh vực nghiên cứu
và xây dựng các hệ thống để máy tính có thể xử lý và hiểu ngôn ngữ của con người.
Trong các hệ thống tương tác người — máy (Human-Computer Interaction), NLP cho
phép người dùng giao tiếp bằng ngôn ngữ tự nhiên thay vì các giao diện hay câu
lệnh có cấu trúc cố định.

Bài tập lớn này xây dựng một hệ thống **Trợ lý hỗ trợ học tập (Course Assistant)**
trong một miền ngữ nghĩa hẹp: sinh viên tra cứu và hỏi đáp về thông tin của
môn **Xử lý Ngôn ngữ Tự nhiên (CO3085)**.

### 1.2 Mục tiêu

Hệ thống phải thể hiện được chuỗi xử lý NLP hoàn chỉnh:

```
Ngôn ngữ tự nhiên
  → Văn phạm / Parser  → Biểu diễn cú pháp
  → Diễn giải ngữ nghĩa → Intent / Entity
  → Knowledge Base / Truy vấn
  → Câu trả lời
```

Các nội dung kỹ thuật được kỳ vọng:


| #   | Nội dung                                       | Phần bài tập |
| --- | ---------------------------------------------- | ------------ |
| 1   | Văn phạm và phân tích cú pháp                  | Phần I       |
| 2   | Biểu diễn và diễn giải ngữ nghĩa               | Phần II      |
| 3   | Nhận diện ý định (intent) và thực thể (entity) | Phần II      |
| 4   | Truy xuất thông tin và hỏi đáp                 | Phần II      |
| 5   | Xử lý ngữ cảnh hội thoại cục bộ                | Phần III     |
| 6   | Phương pháp dựa trên luật / học máy thống kê   | Phần II      |
| 7   | Đánh giá hệ thống                              | Phần IV      |




### 1.3 Phạm vi Knowledge Base


| Nhóm thông tin          | Nội dung                                         | Nguồn trong `data/` |
| ----------------------- | ------------------------------------------------ | ------------------- |
| Thông tin chung môn học | Tên, mã, số tín chỉ, mô tả, mục tiêu             | `course_data.txt`   |
| Đề cương                | 12 chương, nội dung và chủ đề từng chương        | `course_data.txt`   |
| Lịch học                | 15 tuần, ánh xạ tuần ↔ chương                    | `course_data.txt`   |
| Bài tập lớn             | 4 phần (PART_I…PART_IV), yêu cầu, file phải xuất | `course_data.txt`   |
| Quy định                | Quy định dùng AI/LLM, chính sách bản quyền       | `course_data.txt`   |
| Tài liệu tham khảo      | Danh mục sách, slide, tài liệu                   | `course_data.txt`   |




### 1.4 Tập Intent được hỗ trợ


| Intent            | Mô tả                               | Ví dụ câu hỏi                      |
| ----------------- | ----------------------------------- | ---------------------------------- |
| `GET_COURSE_INFO` | Thông tin chung của môn học         | "Môn NLP có bao nhiêu tín chỉ?"    |
| `GET_SCHEDULE`    | Lịch học theo tuần                  | "Tuần 5 học những gì?"             |
| `GET_TOPIC`       | Nội dung / chủ đề của chương        | "Chương nào học về CFG?"           |
| `GET_ASSIGNMENT`  | Thông tin bài tập lớn               | "Bài tập lớn có những yêu cầu gì?" |
| `GET_DEADLINE`    | Mốc thời gian nộp bài               | "Deadline BTL là khi nào?"         |
| `GET_RESOURCE`    | Tài liệu tham khảo                  | "Tài liệu về PCFG ở đâu?"          |
| `GET_RULE`        | Quy định môn học                    | "Có được dùng LLM không?"          |
| `GET_INSTRUCTOR`  | Giảng viên phụ trách                | "Ai dạy môn NLP?"                  |
| `GET_LO`          | Mục tiêu học tập (Learning Outcome) | "L.O.4.2 là gì?"                   |
| `UNKNOWN`         | Ngoài phạm vi hệ thống              | "Hôm nay thời tiết thế nào?"       |


---



## 2. Bộ văn phạm và cây phân tích cú pháp

Phần I của bài tập xây dựng hai thành phần nền tảng: **một bộ văn phạm** mô tả
miền câu hỏi, và **một bộ phân tích cú pháp** sử dụng chính văn phạm đó.

### 2.1 Luật và bộ văn phạm



#### 2.1.1 Văn phạm thực tế của miền Course Assistant

Quan sát tập câu hỏi mẫu cho thấy cấu trúc câu hỏi tiếng Việt trong miền này
luôn theo khuôn:

```
Câu hỏi  =  [từ hỏi] + Danh ngữ chủ thể + Vị ngữ + dấu câu
```

Trong đó:

- **Danh ngữ chủ thể** là nơi chứa *định danh miền* — tên môn, số chương, số tuần,
tên chủ đề, tên bài tập, mã mục tiêu học tập.
- **Từ hỏi** (`gì`, `nào`, `bao nhiêu`, `ở đâu`, `khi nào`) nằm **bên trong vị ngữ**,
không đứng trước danh ngữ.

Điểm này quyết định toàn bộ hình dạng của văn phạm. Nếu đặt từ hỏi ở vị trí đầu
(cách làm phổ biến trong các ví dụ CFG tiếng Anh), bộ sinh câu sẽ sinh ra các
câu vô nghĩa kiểu *"Tuần tuần 15 cần gì?"* hoặc *"Chương muốn gì?"*. Bằng cách
đặt từ hỏi vào vị ngữ, những lỗi này **bị loại ngay từ cấu trúc văn phạm** thay
vì phải xử lý hậu kỳ bằng bộ lọc.

#### 2.1.2 Văn phạm được cài đặt

Văn phạm nằm trong `src/grammar.py` (lớp `CFG`), được sinh ra file
`output/grammar.txt` (254 dòng, 28 non-terminal, 119 terminal). Cấu trúc cốt lõi:

```
# Cấp câu
S              → WH_QUESTION | YES_NO_QUESTION

# Câu hỏi có từ hỏi
WH_QUESTION    → WH_QWORD NP VP PUNCT
WH_QUESTION    → NP VP PUNCT
YES_NO_QUESTION→ NP VP PUNCT

# Từ hỏi (nằm trong vị ngữ)
WH_QWORD       → "gì" | "nào" | "bao_nhiêu" | "ở_đâu" | "khi_nào" | "thế_nào" | "ai"

# Danh ngữ chủ thể
NP             → COURSE_NAME | CHAPTER_REF | WEEK_REF | TOPIC_NAME
               | ASSIGNMENT_NAME | LO_ID | DET NOMINAL | NOMINAL | PRONOUN

# Định danh chương / tuần (head noun luôn đi kèm)
CHAPTER_REF    → "chương" | "chương" CHAPTER_NUM | "chương" WH_QWORD
WEEK_REF       → "tuần"  | "tuần" WEEK_NUM      | "tuần"  WH_QWORD

# Vị ngữ
VP             → VERB | VERB NP | VERB PP | VERB WH_QWORD
               | VERB WH_QWORD NP | AUX VERB NP | AUX VERB NP PP
PP             → PREP NP | PREP NOUN

# Danh từ / tính từ / định từ / trợ động từ
NOMINAL        → NOUN | NOUN NOUN | ADJ NOUN | NOUN ADJ
DET            → "các" | "những" | "nào" | "gì" | "bao" | "mấy" | "này" | "đó"
VERB           → "học" | "nói" | "có" | "là" | "xuất" | "liên_quan" | "biết"
                | "hỏi" | "tra" | "xem" | "tìm" | "yêu_cầu" | "sử_dụng"
                | "bao_gồm" | "trình_bày" | "học_về" | "nói_về"
AUX            → "cần" | "muốn" | "phải" | "nên"
PREP           → "ở" | "về" | "của" | "với" | "cho"

# Định danh miền
COURSE_NAME    → "nlp" | "co3085" | "xử_lý_ngôn_ngữ_tự_nhiên"
CHAPTER_NUM    → "1" | "2" | … | "12"
WEEK_NUM       → "1" | "2" | … | "15"
TOPIC_NAME     → "cfg" | "pcfg" | "parsing" | "semantic" | "syntax" | "pos"
               | "feature" | "grammar" | "tagging" | "disambiguation"
ASSIGNMENT_NAME→ "btl" | "bài_tập_lớn" | "assignment"
LO_ID          → "l.o.1.1" | "l.o.1.2" | … | "l.o.4.2"

# Dấu câu
PUNCT          → "?" | "!"
```



#### 2.1.3 Văn phạm có trọng số (PCFG-lite)

Mỗi luật mang thêm hai thuộc tính, lưu trong `GrammarRule`:

```python
@dataclass
class GrammarRule:
    lhs: str          # Non-terminal bên trái
    rhs: List[str]    # Chuỗi bên phải
    weight: float = 1.0   # Trọng số — điều khiển xác suất sinh câu
    comment: str = ""     # Chú thích tiếng Việt, ghi ra output/grammar.txt
```

Trọng số biến văn phạm ngữ pháp thành **PCFG nhẹ**: động từ `học` (3.0) được
sinh ra nhiều hơn `tra` (0.3), `chương` (4.0) nhiều hơn `quy` (0.8). Nhờ vậy
câu sinh ra nghe tự nhiên thay vì ngẫu nhiên.

Mỗi luật đều có `comment` tiếng Việt, nên `output/grammar.txt` **tự giải thích
được** và có thể đưa thẳng vào báo cáo:

```
# --- NP ---
NP -> COURSE_NAME    # tên môn học
NP -> CHAPTER_REF    # chương + (số | nào)
NP -> WEEK_REF       # tuần + (số | nào)
```



#### 2.1.4 Các lỗi văn phạm đã phát hiện và sửa


| Lỗi                                           | Biểu hiện                                                | Cách sửa                                                     |
| --------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------ |
| Non-terminal `WH_PHRASE` chưa được định nghĩa | `QUESTION → WH_PHRASE NP VP ?` không bao giờ dẫn đến câu | Tách `S → WH_QUESTION                                        |
| `?` vừa là terminal vừa là non-terminal       | `self._add_rule("?", ["?"])`                             | Bỏ hẳn luật đó; `?` chỉ là terminal                          |
| Luật trùng lặp                                | `ADJ → nào` xuất hiện 2 lần                              | Bỏ hết, bổ sung test chống trùng                             |
| Câu sinh vô nghĩa                             | `10 nói nào?`, `Tuần tuần 15`, `Môn 12 có có?`           | Tái thiết kế văn phạm (mục 2.1.1) + bộ ràng buộc (mục 2.2.3) |




### 2.2 Giải thuật sinh câu



#### 2.2.1 Thuật toán

Sinh câu là **mở rộng đệ quy theo trọng số** (weighted recursive expansion):

```
generate_parts(symbol):
    rules ← productions của symbol
    rule  ← chọn ngẫu nhiên theo trọng số (rng.choices)
    parts ← []
    for sym in rule.rhs:
        if sym là terminal:  parts.append(sym)
        else:                parts.extend(generate_parts(sym))
    return parts
```

Sau khi có chuỗi terminal, ba bước kiểm tra và làm đẹp được áp dụng:

```
generate_all_sentences(max_sentences, seed):
    rng ← Random(seed)                     # cố định để tái lập kết quả
    repeat:
        parts ← generate_parts("S")
        if vi phạm ràng buộc cấu trúc:  bỏ qua
        if không kết thúc bằng "?"/"!":  bỏ qua
        sentence ← detokenize(parts)
        if không tự nhiên:              bỏ qua
        thêm vào tập kết quả
    until đủ max_sentences câu
    return tập câu đã sắp xếp
```



#### 2.2.2 Hàm `detokenize()`

Các terminal nội bộ dùng dấu gạch dưới để làm định danh
(`bài_tập_lớn`, `tín_chỉ`, `xử_lý_ngôn_ngữ_tự_nhiên`). Hàm `detokenize()`
chuyển chúng về dạng văn xuôi:

```python
TOKEN_GLUE = {
    "bài_tập_lớn": "bài tập lớn",
    "tín_chỉ": "tín chỉ",
    "giữa_kỳ": "giữa kỳ",
    "xử_lý_ngôn_ngữ_tự_nhiên": "xử lý ngôn ngữ tự nhiên",
    ...
}
```

Ngoài ra hàm còn: viết hoa chuẩn cho các proper noun (`NLP`, `CO3085`, `PCFG`,
`CFG`, `POS`, `BTL`), khôi phục dạng `L.O.2.5`, bỏ khoảng trắng trước dấu câu,
và viết hoa chữ đầu câu.

#### 2.2.3 Bộ ràng buộc sinh câu

Để câu sinh ra luôn có nghĩa, hàm `_violates_constraints()` kiểm tra 8 luật trên
chuỗi terminal:


| #   | Ràng buộc                                       | Ví dụ bị loại                       |
| --- | ----------------------------------------------- | ----------------------------------- |
| 1   | Không mở câu bằng động từ / lượng từ yếu        | `Tra với chương 4?`, `Mấy bài học?` |
| 2   | Không có hai từ chỉ định / hai từ hỏi liền nhau | `Gì nào học?`                       |
| 3   | Số trần không được đứng, phải có head noun      | `10 nói nào?`                       |
| 4   | Số chương ∈ [1,12], số tuần ∈ [1,15]            | `Chương 13 học gì?`                 |
| 5   | Không lặp lại chủ thể                           | `Chương này … chương 10?`           |
| 6   | Từ hỏi không được mở câu                        | `Gì chương 6 sử dụng?`              |
| 7   | Bắt buộc có ≥ 1 định danh miền                  | `Môn có bao nhiêu?`                 |
| 8   | Bắt buộc kết thúc bằng `?` hoặc `!`             | `Chương 4 học gì`                   |




#### 2.2.4 Kết quả

`output/samples.txt` chứa **10 000 câu** do bộ sinh tạo ra (tối đa theo yêu cầu
đề bài), cộng phần template thủ công có nhãn intent. Kết quả so sánh trước và
sau khi tái thiết kế văn phạm:


| Chỉ số                             | Trước | Sau   |
| ---------------------------------- | ----- | ----- |
| Câu chứa dấu `_` (chưa detokenize) | 6 278 | **0** |
| Câu rò non-terminal (`WH_PHRASE`)  | 3 239 | **0** |
| Câu mở bằng động từ                | 727   | **0** |
| Câu thiếu dấu câu kết thúc         | —     | **0** |


Ví dụ câu sinh ra (trích từ `output/samples.txt`):

```
Chương 4 yêu cầu gì?
BTL muốn nói assignment?
L.O.2.3 học gì?
AI được phép dùng trong bài tập lớn không?
Tuần 15 học những gì?
```



#### 2.2.5 Tính tất định

Bộ sinh dùng `seed=42` cố định. Chạy lại hai lần cho ra **danh sách câu giống
hệt nhau** (byte-identical), đảm bảo `output/samples.txt` tái lập được — điều
kiện cần để video demo và báo cáo luôn khớp với code.

### 2.3 Bộ phân tích cú pháp



#### 2.3.1 Thuật toán: recursive descent có backtracking

Bộ phân tích cú pháp nằm trong `src/parser.py`, là **recursive-descent parser**
(top-down) đọc trực tiếp văn phạm từ `CFG`:

```
parse(text):
    tokens ← tokenize_input(text)
    tree   ← _parse_question()
    if tree != null and đã tiêu thụ hết tokens:
        return tree                          # phân tích thành công
    fallback ← _parse_fallback(text)          # phân tích theo mẫu
    if fallback != null:
        return fallback
    return null, errors                      # không thuộc văn phạm
```

Cấu trúc các hàm đệ quy tương ứng từng non-terminal:

```
_parse_question()      → _parse_wh_question() | _parse_yes_no_question()
_parse_wh_question()   → _parse_wh_word() + _parse_np() + _parse_vp() + _parse_question_mark()
_parse_np()            → định danh miền | DET NOMINAL | NOMINAL | PRONOUN
_parse_vp()            → VERB [NP | PP | WH_QWORD | AUX ...]
```

Bảng tra cứu (`_build_lookup_tables()`) được xây tự động từ văn phạm: danh sách
terminal của mỗi non-terminal, danh sách course name / topic / assignment /
learning outcome. Nhờ vậy **chỉ có một nguồn sự thật duy nhất** cho ngôn ngữ —
tránh tình trạng văn phạm và parser lệch nhau.

#### 2.3.2 Cơ chế dự phòng (fallback)

Không phải câu nào trong tự nhiên cũng khớp văn phạm nghiêm ngặt. Để hệ thống
vẫn trả lời được, khi recursive descent thất bại, parser chuyển sang
`_parse_fallback()`: phân loại từng token theo bảng từ khoá rồi dựng cây theo
mẫu (`WH_WORD` | `NP` | `VP` | `PUNCT`).

Cơ chế này giữ cho **intent accuracy cao** ngay cả khi strict parse thấp — vì
tầng semantic làm việc trên văn bản, không phụ thuộc cây cú pháp.

#### 2.3.3 Kết quả trên tập kiểm thử chính thức

Trên 34 câu hỏi trong `tests/data/sample_queries.txt`:


| Chế độ                   | Số câu | Tỉ lệ   |
| ------------------------ | ------ | ------- |
| Strict recursive descent | 4      | 11.76 % |
| Pattern fallback         | 30     | 88.24 % |
| Thất bại                 | 0      | 0 %     |


> Strict parse chỉ 11.76 % là **hạn chế đã biết** của phiên bản hiện tại — đây
> chính là nội dung của Work Package WP3 (xem mục 6.1). Nguyên nhân: văn phạm
> được thiết kế để *sinh câu* một cách tự nhiên, trong khi câu hỏi thực tế của
> người dùng có nhiều biến thể mà văn phạm chưa bao phủ hết.



#### 2.3.4 Định dạng cây cú pháp

Kết quả được ghi ra `output/parse-results.txt` theo dạng cây lồng:

```
(WH_QUESTION (WH_WORD chương) (NP (COURSE_NAME nlp)) (VP (VERB có) (ADJ bao) (ADJ nhiêu) (NP (NOUN tín))))
```

Câu không thuộc văn phạm được xuất `()` theo yêu cầu đề bài.

---



## 3. Phân tích ngữ nghĩa và Course Assistant



### 3.1 Phân tích ngữ nghĩa (intent, entity)



#### 3.1.1 Biểu diễn ngữ nghĩa

Mỗi câu hỏi được ánh xạ thành một **dạng logic (logic form)** có cấu trúc:

```
GET_INTENT(entity₁=value₁, entity₂=value₂, …)
```

Cấu trúc dữ liệu (`src/semantic.py`):

```python
@dataclass
class SemanticRepresentation:
    intent: IntentType                  # Ý định của câu hỏi
    entities: Dict[str, Any]            # Các thực thể đã nhận diện
    attributes: Dict[str, bool]         # Thuộc tính cần truy vấn
    query_type: str                     # Loại truy vấn
    raw_query: str                      # Câu gốc

    def to_logical_form(self) -> str:
        entity_str = ", ".join(f"{k}={v}" for k, v in self.entities.items())
        return f"{self.intent.value}({entity_str})"
```

Ví dụ thực tế từ hệ thống:


| Câu hỏi                         | Dạng logic                                       |
| ------------------------------- | ------------------------------------------------ |
| "Môn NLP có bao nhiêu tín chỉ?" | `GET_COURSE_INFO(course=NLP, attribute=credits)` |
| "Tuần 3 học gì?"                | `GET_SCHEDULE(week=WEEK_03)`                     |
| "Chương 4 nói về gì?"           | `GET_TOPIC(chapter=CH04)`                        |
| "Chương nào học về CFG?"        | `GET_TOPIC(topic=CFG)`                           |
| "Deadline BTL là khi nào?"      | `GET_DEADLINE(assignment=BTL01)`                 |
| "Có được dùng LLM không?"       | `GET_RULE()`                                     |
| "L.O.4.2 là gì?"                | `GET_LO(lo=LO4.2)`                               |




#### 3.1.2 Nhận diện Intent — phương pháp dựa trên luật

**Phương pháp:** khớp từ khoá + biểu thức chính quy (regex), theo thứ tự ưu
tiên từ cụ thể đến chung.

*Pseudocode:*

```
function extract_intent(text, tokens):
    normalized ← lowercase(text); bảo vệ pattern "l.o.X.Y" → "lo_X_Y"

    # Bước 1: phát hiện ngoài phạm vi trước tiên
    for pattern in OUT_OF_SCOPE_PATTERNS:          # thời tiết, bóng đá, giá vàng, …
        if re.search(pattern, normalized):
            return UNKNOWN

    # Bước 2: các intent có mẫu đặc biệt, kiểm tra theo thứ tự ưu tiên
    if re.search(r"(deadline|thời hạn|hạn nộp|nộp|khi nào nộp)", normalized):
        return GET_DEADLINE
    if re.search(r"lo_\d", normalized) or "learning outcome" in normalized:
        return GET_LO
    if re.search(r"(ai dạy|giảng viên|thầy|cô giáo)", normalized):
        return GET_INSTRUCTOR
    if re.search(r"\b(quy định|được phép dùng|sử dụng llm|dùng ai|chính sách)\b", normalized):
        return GET_RULE
    if re.search(r"(tài liệu|sách|giáo trình|tham khảo|resource)", normalized):
        return GET_RESOURCE
    if re.search(r"(bài tập lớn|btl|assignment)", normalized):
        return GET_ASSIGNMENT
    if re.search(r"tuần\s*\d+", normalized):              return GET_SCHEDULE
    if re.search(r"(chương|ch).*tuần nào", normalized):  return GET_SCHEDULE
    if re.search(r"(chương nào|chương \d+|nói về|nội dung gì)", normalized):
        return GET_TOPIC

    # Bước 3: chấm điểm theo từ khoá / pattern cho từng intent
    for intent, config in INTENT_PATTERNS:
        score(intent) ← số từ khoá xuất hiện + 2 × số pattern khớp
    return intent có điểm cao nhất, nếu điểm > 0; ngược lại UNKNOWN
```

**Vì sao cần thứ tự ưu tiên?** Nhiều từ khoá xung đột. Ví dụ *"Tài liệu nào liên
quan đến PCFG?"* chứa cả `tài liệu` (→ GET_RESOURCE) lẫn `pcfg` (→ GET_TOPIC).
Đặt GET_RESOURCE trước GET_TOPIC giải quyết mâu thuẫn này.

#### 3.1.3 Nhận diện Entity

*Pseudocode:*

```
function extract_entities(text, intent):
    normalized ← normalize_text(text)
    entities ← {}

    # Định danh miền
    if "nlp" in tokens or "co3085" in tokens:
        entities["course"] ← "CO3085" nếu có co3085, ngược lại "NLP"

    if re.search(r"chương\s*(\d+)", normalized):
        entities["chapter"] ← "CH" + số.zfill(2)

    if re.search(r"tuần\s*(\d+)", normalized):
        entities["week"] ← "WEEK_" + số.zfill(2)

    for keyword, topic in TOPIC_KEYWORDS:            # cfg, pcfg, parsing, semantic, …
        if keyword in normalized:
            entities["topic"] ← topic; break

    if "btl" in tokens or "bài tập lớn" in normalized:
        entities["assignment"] ← "BTL01"

    if intent = GET_ASSIGNMENT:
        if re.search(r"phần\s*(i{1,3}|iv|v|\d+)", normalized):
            entities["part"] ← "PART_" + số La Mã viết hoa
        if "phần nào" in normalized or "những phần" in normalized:
            entities["list_parts"] ← true

    if re.search(r"lo_(\d)(?:_(\d+))?", normalized):
        entities["lo"] ← "LO" + phần chính + "." + phần phụ (mặc định ".1")

    # Thuộc tính theo intent
    if intent = GET_COURSE_INFO:
        if có "tín"/"credit":            entities["attribute"] ← "credits"
        elif có "midterm"/"giữa kỳ":    entities["attribute"] ← "midterm_duration"
        elif có "final"/"cuối kỳ":       entities["attribute"] ← "final_duration"
        elif có "phần"/"gồm những":     entities["attribute"] ← "parts"
        elif có "mô tả"/"giới thiệu":    entities["attribute"] ← "description"
        elif có "mục tiêu":              entities["attribute"] ← "learning_outcomes"

    return entities
```



#### 3.1.4 Bảng lexicon chuẩn hoá

Ngoài các quy tắc trên, hệ thống dùng file `models/lexicon.json` làm bảng tra
cứu **surface form → canonical value** cho từng nhóm thực thể:


| Nhóm               | Ví dụ surface form        | Canonical value            |
| ------------------ | ------------------------- | -------------------------- |
| `course`           | `xử lý ngôn ngữ tự nhiên` | `CO3085`                   |
| `chapter`          | `chương 4`                | `CH04`                     |
| `week`             | `tuần 12`                 | `WEEK_12`                  |
| `topic`            | `semantic grammar`        | `SEMANTIC_GRAMMAR`         |
| `topic`            | `selectional restriction` | `SELECTIONAL_RESTRICTION`  |
| `assignment_part`  | `phần ii`                 | `PART_II`                  |
| `rule`             | `llm/rag`                 | `LLM_RAG`                  |
| `resource`         | `sách tham khảo`          | `REFERENCE_BOOK`           |
| `learning_outcome` | `l.o.2.5`                 | `LO2.5`                    |
| `out_of_scope`     | `dự báo thời tiết`        | — (đánh dấu ngoài phạm vi) |


Bảng này ghi rõ nguồn gốc và được kiểm thử tự động bằng `tests/test_lexicon.py`
(11 test) — bao gồm kiểm tra mọi surface form đều ở dạng chữ thường để tra cứu
không phân biệt hoa thường.

### 3.2 Đặc tả pipeline và kiến trúc hệ thống



#### 3.2.1 Đặc tả pipeline

```
Input (câu hỏi tiếng Việt)
  │
  ▼
[1] PREPROCESSING
      normalize  : Unicode NFC → lowercase → chuẩn hoá dấu → gộp khoảng trắng
      tokenize   : tách từ, bảo vệ mã L.O.X.Y
      spans      : nhận diện thực thể nhiều từ ("bài tập lớn", "tín chỉ")
      pos_tag    : gán nhãn từ loại theo luật
      keywords   : loại stopword, GIỮ từ hỏi (nào/gì/bao nhiêu…)
  │
  ▼
[2] PARSING
      recursive descent theo văn phạm CFG → cây cú pháp
      (fallback: dựng cây theo mẫu nếu không khớp văn phạm)
  │
  ▼
[3] SEMANTIC REPRESENTATION
      cây cú pháp / văn bản → dạng logic  GET_INTENT(...)
  │
  ▼
[4] INTENT / ENTITY
      intent  : khớp luật theo thứ tự ưu tiên + chấm điểm từ khoá
      entity  : nhận diện & chuẩn hoá qua lexicon
  │
  ▼
[5] QUERY
      (intent, entities) → truy vấn có tham số lên knowledge base
  │
  ▼
[6] KNOWLEDGE BASE
      tra cứu thông tin môn học theo intent + thực thể
  │
  ▼
[7] ANSWER
      sinh câu trả lời tiếng Việt
      nếu không có thông tin → thông báo lỗi, KHÔNG bịa thông tin
```



#### 3.2.2 Kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────────────────┐
│                      NGÔN NGỮ TỰ NHIÊN (INPUT)                       │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│  TẦNG 1 — PREPROCESSING          │  src/preprocessing.py             │
│  ┌────────────┬────────────┬────────────┬─────────────────────────┐  │
│  │ Normalize  │  Tokenize  │  POS Tag   │  Multi-word Spans       │  │
│  └────────────┴────────────┴────────────┴─────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│  TẦNG 2 — PARSING                │  src/grammar.py + src/parser.py   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │   CFG Grammar ──► Recursive Descent Parser ──► Parse Tree    │  │
│  │   (28 non-terminal, 119 terminal)      (fallback: pattern)     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│  TẦNG 3 — SEMANTIC               │  src/semantic.py                  │
│  ┌────────────────────────┬────────────────────────┬──────────────┐  │
│  │ Semantic Representation│  Intent Classification │   Entity     │  │
│  │  GET_X(entity=value)   │  (rule + ưu tiên)      │  Extraction  │  │
│  └────────────────────────┴────────────────────────┴──────────────┘  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Lexicon: models/lexicon.json  (surface form → canonical)     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│  TẦNG 4 — QUERY & KNOWLEDGE BASE │  src/knowledge_base.py            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Query Engine ──► Course │ Schedule │ Topics │ Assignment │   │  │
│  │                      │ Regulations │ Resources │ FAQ │ LO       │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│  TẦNG 5 — ANSWER GENERATION                                        │
│  ┌────────────┬─────────────────┬──────────────────┐                 │
│  │  Retrieve  │  Template Answer │  Fallback Message│                │
│  └────────────┴─────────────────┴──────────────────┘                 │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
┌──────────────────────────────────▼───────────────────────────────────┐
│  TẦNG 6 — NGỮ CẢNH HỘI THOẠI     │  src/dialogue.py                 │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Dialogue State ◄──► Reference Resolution ──► Rewrite Query  │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                              ┌────▼────┐
                              │ ANSWER  │
                              └─────────┘
```



#### 3.2.3 Cấu trúc mã nguồn

```
src/
├── preprocessing.py   # Normalize, Tokenize, POS tag, multi-word entity spans
├── grammar.py         # CFG + WeightedRule + detokenize + bộ sinh câu
├── parser.py          # Recursive-descent parser + fallback pattern parser
├── semantic.py        # IntentType, SemanticRepresentation, Intent/Entity
├── knowledge_base.py  # Dữ liệu môn học + query engine + sinh câu trả lời
├── dialogue.py        # DialogueState, DialogueManager, reference resolution
└── main.py            # CourseAssistant — điều phối pipeline + CLI
```

Đặc điểm thiết kế đáng chú ý: `grammar.py` **là nguồn sự thật duy nhất cho
ngôn ngữ**. `parser.py` đọc productions, terminal classes và tập FIRST/FOLLOW
từ đó, thay vì hard-code một bản sao. Nhờ vậy khi văn phạm thay đổi, parser
tự động đồng bộ.

---



## 4. Quản lý ngữ cảnh hội thoại



### 4.1 Bài toán ngữ cảnh cục bộ

Khi người dùng hỏi *"Tài liệu của phần này ở đâu?"*, hệ thống phải hiểu
*"phần này"* chỉ nội dung vừa được trao đổi ở lượt trước. Đây là bài toán
**ngữ cảnh hội thoại cục bộ** (local discourse context).

### 4.2 Mô hình trạng thái

`src/dialogue.py` định nghĩa trạng thái hội thoại:

```python
@dataclass
class DialogueState:
    turn: int                       # số lượt đã xử lý
    last_intent: str                # intent của lượt gần nhất
    last_topic: Optional[str]       # chủ đề vừa đề cập
    last_chapter: Optional[str]     # chương vừa đề cập
    last_week: Optional[str]        # tuần vừa đề cập
    entities: Dict[str, DiscourseEntity]   # các thực thể đang "nổi bật"
    history: List[Dict]             # lịch sử các lượt

@dataclass
class DiscourseEntity:
    entity_type: str
    value: str
    mention: str                    # cách được nhắc tới
    introduced_at: int              # lượt giới thiệu
    last_mentioned_at: int          # lượt nhắc lại gần nhất
    salience: float = 1.0           # độ nổi bật
```



### 4.3 Giải quyết tham chiếu

`DialogueManager.resolve_reference()` xử lý ba loại tham chiếu:


| Loại                 | Mẫu                                                             | Xử lý                                                 |
| -------------------- | --------------------------------------------------------------- | ----------------------------------------------------- |
| Định danh mơ hồ      | `phần này`, `chương này`, `tuần này`, `bài này`, `nội dung này` | Thay bằng giá trị `last_*` tương ứng trong trạng thái |
| Đại từ               | `nó`                                                            | Thay bằng `last_topic`                                |
| Lược giản (ellipsis) | `Còn chương sau?`                                               | Bổ sung ngữ cảnh từ lượt trước                        |


*Pseudocode:*

```
function resolve_reference(query):
    resolved_query ← query
    resolved_entities ← {}

    # 1. Tham chiếu tân ngữ ("phần này", "chương này", "tuần này")
    for pattern in REFERENCE_PATTERNS["definite_phrase"]:
        if pattern in query:
            if pattern chứa "phần":
                nếu state.last_topic tồn tại:
                    thay pattern bằng state.last_topic
                    resolved_entities["topic"] ← state.last_topic
                ngược lại nếu state.last_intent = GET_ASSIGNMENT:
                    thay bằng "bài tập lớn"
                    resolved_entities["assignment"] ← "BTL01"
            nếu pattern chứa "chương" và state.last_chapter tồn tại:
                thay bằng state.last_chapter
                resolved_entities["chapter"] ← state.last_chapter
            nếu pattern chứa "tuần" và state.last_week tồn tại:
                thay bằng state.last_week
                resolved_entities["week"] ← state.last_week

    # 2. Đại từ ("nó")
    for pronoun in REFERENCE_PATTERNS["pronoun"]:
        if pronoun in query và state.last_topic tồn tại:
            thay pronoun bằng state.last_topic
            resolved_entities["topic"] ← state.last_topic

    return resolved_query, resolved_entities
```



### 4.4 Luồng xử lý một lượt hội thoại

```
người dùng: "Chương 4 nói về gì?"
    │
    ├─► process_query()  → intent=GET_TOPIC, entity={chapter: CH04}
    │   └─► update_context()  → state.last_chapter = "CH04", state.turn = 1
    │
    └─► trả lời: "Chương 04 - Features and Augmented Grammar ..."

người dùng: "Nó có liên quan đến parsing không?"
    │
    ├─► resolve_reference()  → "nó" → "CH04" (lấy từ state.last_chapter)
    │   → câu được viết lại: "CH04 có liên quan đến parsing không?"
    ├─► process_query()  → intent=GET_TOPIC, entity={chapter: CH04}
    └─► trả lời: thông tin về chương 4
```



### 4.5 Giao diện API


| Hàm                                       | Chức năng                                             |
| ----------------------------------------- | ----------------------------------------------------- |
| `update_context(intent, entities, query)` | Cập nhật trạng thái sau mỗi lượt                      |
| `resolve_reference(query)`                | Trả về `(câu đã viết lại, thực thể suy ra)`           |
| `get_state_summary()`                     | Tóm tắt trạng thái (turn, last_intent, last_chapter…) |
| `get_history(limit=5)`                    | Lịch sử các lượt gần đây                              |
| `reset()`                                 | Xoá sạch ngữ cảnh                                     |




### 4.6 Trạng thái hiện tại và hướng hoàn thiện

`DialogueManager` đã được viết đầy đủ và có test contract riêng (`tests/test_dialogue_cases.py`:
6 test pass cho API nội bộ, 6 test xfail cho các ca chưa nối vào pipeline), nhưng
**chưa được nối vào pipeline chính** của `CourseAssistant.process_dialogue()`. Vì vậy:

- Phần lớn test hội thoại hiện được đánh dấu `xfail` với lý do
*"DialogueManager chưa được nối vào process_dialogue()"* (6 ca xfail).
- Việc nối vào pipeline là nội dung của **WP6** (xem mục 6.1).

Đây là hạn chế đã được **đo và ghi nhận công khai** trong `tests/known_issues.py`,
không phải lỗi ẩn.

---



## 5. Kết quả và phân tích



### 5.1 Đánh giá hệ thống



#### 5.1.1 Tập kiểm thử

Tập kiểm thử lấy từ dữ liệu mẫu chính thức của bài tập
(`tests/data/sample_queries.txt`, **34 câu**), bao phủ các nhóm truy vấn:


| Nhóm                       | Số câu | Mô tả                                                                        |
| -------------------------- | ------ | ---------------------------------------------------------------------------- |
| Câu hỏi hợp lệ trong miền  | 29     | Hỏi thông tin chung, chương, tuần, chủ đề, bài tập, quy định, tài liệu, L.O. |
| Câu hỏi ngoài phạm vi      | 2      | Không liên quan tới môn học                                                  |
| Câu hỏi phụ thuộc ngữ cảnh | 3      | Cần thông tin từ lượt trước                                                  |


Bộ test còn có thêm **5 kịch bản hội thoại** (`tests/data/dialogues.txt`) mô tả
các mẫu tham chiếu ngữ cảnh cục bộ.

#### 5.1.2 Cơ sở đo lường

Hai script đảm bảo mọi con số trong báo cáo đều **tái lập được**:

```bash
python scripts/baseline.py --out docs/baseline.txt   # đo các chỉ số
python -m pytest                                   # chạy bộ test
```

`docs/baseline.txt` lưu lại kết quả đo tại thời điểm bàn giao.

#### 5.1.3 Các chỉ số

**Kết quả trên 34 câu hỏi chính thức:**


| Chỉ số                          | Kết quả | Tỉ lệ       |
| ------------------------------- | ------- | ----------- |
| Intent accuracy                 | 30/34   | **88.24 %** |
| Entity accuracy (có bảng alias) | 19/34   | 55.88 %     |
| Entity accuracy (khớp thô)      | 16/34   | 47.06 %     |
| **Intent + Entity accuracy**    | 18/34   | **52.94 %** |
| Strict recursive-descent parse  | 4/34    | 11.76 %     |
| Pattern fallback parse          | 30/34   | 88.24 %     |
| Parse failure                   | 0/34    | 0 %         |


**Chất lượng bộ sinh câu (10 000 câu):**


| Chỉ số                     | Kết quả    |
| -------------------------- | ---------- |
| Câu chứa dấu `_`           | 0 / 10 000 |
| Câu rò non-terminal        | 0 / 10 000 |
| Câu mở bằng động từ        | 0 / 10 000 |
| Câu thiếu dấu câu kết thúc | 0 / 10 000 |




#### 5.1.4 Phân tích theo từng intent

Phân bố 4 lỗi intent trên tập kiểm thử:


| Câu hỏi                                   | Intent đúng       | Intent thực tế | Nguyên nhân                                                       |
| ----------------------------------------- | ----------------- | -------------- | ----------------------------------------------------------------- |
| "Hãy giải bài tập xác suất này giúp tôi." | UNKNOWN           | GET_ASSIGNMENT | Bộ phát hiện ngoài phạm vi chưa bao phủ "giải bài tập … giúp tôi" |
| "Nó có liên quan đến parsing không?"      | CONTEXT_DEPENDENT | GET_RULE       | Chưa có intent CONTEXT_DEPENDENT; "không" khớp mẫu GET_RULE       |
| "Còn chương sau?"                         | CONTEXT_DEPENDENT | GET_TOPIC      | Chưa có intent CONTEXT_DEPENDENT                                  |
| "Phần này cần xuất file gì?"              | CONTEXT_DEPENDENT | GET_ASSIGNMENT | Chưa có intent CONTEXT_DEPENDENT                                  |


**Nhận xét quan trọng:** 30/34 intent đúng là kết quả **khá cao**, nhưng con số
này **không phải** "độ chính xác tổng thể" của hệ thống. Khi đo đồng thời intent
*và* entity, độ chính xác chỉ còn **52.94 %**. Báo cáo này trình bày cả hai số
để tránh hiểu sai.

#### 5.1.5 Kết quả evaluation tổng hợp

```bash
$ python scripts/baseline.py
======================================================================
COURSE ASSISTANT - BASELINE METRICS
======================================================================

Official test set (tests/data/sample_queries.txt): 34 cases
  Intent accuracy:        30/34 = 88.24%
  Entity accuracy (alias-aware): 19/34 = 55.88%
  Entity accuracy (raw match):   16/34 = 47.06%
  Intent + Entity accuracy: 18/34 = 52.94%

Parser (on the official test set):
  Strict recursive descent: 4/34 = 11.76%
  Pattern fallback:        30/34 = 88.24%
  Failure:                 0/34 = 0.00%

Sentence generation:
  Sentences generated:      10000
  Containing '_':            0
  Containing 'WH_PHRASE':    0
  Bad leading token:         0
  Missing end punctuation:   0
```



#### 5.1.6 Ví dụ hệ thống trả lời đúng


| Câu hỏi                         | Dạng logic                                       | Câu trả lời                                                                                         |
| ------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| "Môn NLP có bao nhiêu tín chỉ?" | `GET_COURSE_INFO(course=NLP, attribute=credits)` | "Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ."                                                |
| "Tuần 3 học gì?"                | `GET_SCHEDULE(week=WEEK_03)`                     | "Tuần 03: Học Chương 03 — Grammar and Parsing. Nội dung: CFG, Top-down parsing, Bottom-up parsing." |
| "Chương nào học về CFG?"        | `GET_TOPIC(topic=CFG)`                           | "Chương 03: Grammar and Parsing trình bày về CFG."                                                  |
| "L.O.4.2 là gì?"                | `GET_LO(lo=LO4.2)`                               | "LO4.2: Ngữ cảnh diễn ngôn cục bộ và sự tham chiếu."                                                |




### 5.2 Một vài hạn chế



#### 5.2.1 Hạn chế về độ bao phủ của văn phạm và parser

**Hiện trạng:** strict parse chỉ đạt 11.76 % trên tập kiểm thử.

**Nguyên nhân:** văn phạm được thiết kế để *sinh câu* một cách tự nhiên và có
tính đầy đủ về mặt ngôn ngữ, còn câu hỏi thật của người dùng có rất nhiều
biến thể (ví dụ *"Phần CFG và Parsing nằm ở tuần nào?"*, *"Có được sử dụng
công cụ AI không?"*) mà văn phạm chưa bao phủ hết.

**Hệ quả:** người dùng hỏi câu lạ → parser không sinh được cây cú pháp đúng →
cây phân tích cú pháp trong báo cáo có thể không đúng với câu đó. Tuy nhiên
**intent vẫn đúng** nhờ tầng semantic làm việc trực tiếp trên văn bản và cơ
chế fallback của parser.

**Hướng khắc phục:** mở rộng văn phạm theo hướng *rule + pattern* (WP3), hoặc
chuyển sang bộ phân tích cú pháp dựa trên FIRST/FOLLOW (chart parsing / Earley)
để tăng độ bao phủ mà không phải liệt kê thủ công.

#### 5.2.2 Hạn chế về trích xuất thực thể

**Hiện trạng:** entity accuracy 55.88 % (alias-aware) — thấp hơn đáng kể so với
intent accuracy 88.24 %.

**Nguyên nhân:** các lỗi còn lại tập trung ở việc **ưu tiên khớp** và **suy luận**:

- *Khớp chồng lấn:* "PCFG" bị khớp thành "CFG" (substring), "semantic grammar"
bị khớp thành "SEMANTIC".
- *Tranh chấp miền:* "Tài liệu về statistical NLP" bị gán `course=NLP` thay vì
`topic=STATISTICAL_NLP`.
- *Thiếu suy luận:* "Bài tập lớn có phần parser không?" cần suy luận
`part=PART_I` từ từ khoá "parser"; "… có phần hỏi đáp không?" cần suy luận
`part=PART_II`.
- *Thiếu thực thể:* chưa trích xuất được `rule=LLM_RAG`, `rule=AI_USAGE`.

**Hướng khắc phục:** dùng bảng `models/lexicon.json` làm nguồn chuẩn, khớp
theo **độ dài cụm từ giảm dần** (ưu tiên cụm dài trước), và bổ sung luật suy luận
`part` từ từ khoá (WP4).

#### 5.2.3 Hạn chế về xử lý ngữ cảnh hội thoại

**Hiện trạng:** `DialogueManager` đã hiện thực đầy đủ nhưng chưa nối vào
pipeline, nên các câu phụ thuộc ngữ cảnh chưa được giải quyết (3 trong 34 câu
kiểm thử thuộc nhóm này).

**Hướng khắc phục:** nối `resolve_reference()` vào `process_dialogue()` và bổ
sung intent `CONTEXT_DEPENDENT` (WP6).

#### 5.2.4 Hạn chế về phương pháp nhận diện intent

Phương pháp dựa trên luật có ưu điểm là **minh bạch, không cần dữ liệu huấn
luyện, giải thích được** (đây là điểm giảng viên đánh giá cao), nhưng:

- Chỉ bao phủ được các mẫu câu đã định nghĩa.
- Mâu thuẫn từ khoá phải giải quyết thủ công bằng thứ tự ưu tiên.
- Không mở rộng tự động khi gặp cách diễn đạt mới.

**Hướng khắc phục (phương án dự phòng):** bổ sung một mô hình phân loại đa lớp
(học máy thống kê) trên đặc trưng n-gram, dùng luật làm đường dẫn fallback khi
độ tin cậy thấp. Nhóm chọn hướng **Classical/Statistical NLP** nên đây là hướng
mở rộng tự nhiên, không phải LLM.

#### 5.2.5 Hạn chế về độ bao phủ knowledge base

- Chỉ hỗ trợ truy vấn đơn giản theo `(intent, entities)`, không có suy luận nhiều
bước.
- Chưa có cơ chế **trả lời khi thiếu thông tin theo ngữ cảnh** — hiện tại mọi
truy vấn không có kết quả đều trả về cùng một thông báo.
- Nội dung knowledge base còn sơ lược so với đề cương môn học đầy đủ.

---



## 6. Kết luận



### 6.1 Kết luận

Hệ thống **Course Assistant** đã hiện thực được chuỗi xử lý NLP hoàn chỉnh trong miền môn học, từ ngôn ngữ tự nhiên đến câu trả lời.

**Về mặt phương pháp**, hệ thống thể hiện được đầy đủ các kỹ thuật NLP được yêu
cầu: xây dựng văn phạm CFG có trọng số, sinh câu, phân tích cú pháp top-down,
biểu diễn ngữ nghĩa dạng logic form, nhận diện intent bằng luật theo thứ tự ưu
tiên, trích xuất entity có chuẩn hoá qua lexicon, truy vấn knowledge base theo
tham số, và xử lý tham chiếu ngữ cảnh cục bộ.

**Điểm mạnh đáng chú ý** là tính **minh bạch và tái lập được**: mọi quyết định
của hệ thống đều có thể truy vết (rule nào khớp, entity nào được trích, query
gì được gửi tới KB); mọi con số trong báo cáo đều do script sinh ra chứ không
phải ước lượng tay.

**Hạn chế lớn nhất** là độ bao phủ của văn phạm so với biến thể ngôn ngữ thực
tế (strict parse 11.76 %) và độ chính xác trích xuất entity (55.88 %). Cả hai
đều đã được **đo, phân loại nguyên nhân và ghi vào sổ đăng ký lỗi**
`tests/known_issues.py` kèm Work Package chịu trách nhiệm — không phải lỗi ẩn.

### 6.2 Hướng cải tiến

---

*Báo cáo bài tập lớn CO3085 — Trợ lý hỗ trợ học tập thông minh (Course Assistant)*
*Hướng thực hiện: Classical / Statistical NLP (dựa trên luật)*