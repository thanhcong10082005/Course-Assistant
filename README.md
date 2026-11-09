# Course Assistant — Trợ lý hỗ trợ học tập thông minh

Trợ lý hỗ trợ học tập cho môn **Xử lý Ngôn ngữ Tự nhiên (CO3085)**, xây dựng
bằng Python theo hướng **Classical / Statistical NLP** (dựa trên luật, không
dùng LLM thay thế các thành phần NLP cốt lõi).

Người dùng hỏi bằng tiếng Việt tự nhiên, hệ thống trả lời về thông tin môn học:
lịch học, nội dung chương, bài tập lớn, thời hạn, tài liệu, quy định và mục
tiêu học tập.

---

## 1. Thành viên nhóm


| STT | Họ và tên         | MSSV    |
| --- | ----------------- | ------- |
| 1   | Nguyễn Thành Công | 2310373 |
| 2   | -                 | -       |
| 3   | -                 | -       |
| 4   | -                 | -       |


---

## 2. Cài đặt

### 2.1 Yêu cầu môi trường


| Thành phần        | Yêu cầu                                                 |
| ----------------- | ------------------------------------------------------- |
| Hệ điều hành      | Windows / Linux / macOS                                 |
| Python            | 3.8 trở lên (đã kiểm thử trên 3.14)                     |
| Thư viện ngoài    | **Không** — phần lõi chỉ dùng thư viện chuẩn của Python |
| Thư viện cho test | `pytest` (tuỳ chọn)                                     |


> Hệ thống được viết **không phụ thuộc thư viện bên ngoài** (không cần NLTK,
> spaCy, hay bất kỳ framework NLP nào) để bảo đảm chạy được trong bất kỳ môi
> trường chấm bài nào. `pytest` chỉ cần khi chạy bộ test.

### 2.2 Cài đặt

```bash
# 1. Clone repository
git clone https://github.com/thanhcong10082005/Course-Assistant.git
cd Course-Assistant

# 2. (Tuỳ chọn) Tạo môi trường ảo
python -m venv .venv
# Windows:      .venv\Scripts\activate
# Linux/macOS:  source .venv/bin/activate

# 3. Cài đặt (cho phần test)
pip install -r tests/requirements-test.txt
```

Không cần bước cài đặt nào khác — toàn bộ mã nguồn dùng thư viện chuẩn.

### 2.3 Chạy bằng Docker (tuỳ chọn)

```bash
docker build -t course-assistant .
docker run -it course-assistant
```

---

## 3. Chạy chương trình

### 3.1 Các lệnh chính

```bash
cd Course_Assistant_Sample

# Chế độ demo — in pipeline, grammar, parsing (mặc định)
python -m src.main --mode demo

# Chế độ tương tác — hỏi đáp trực tiếp với Course Assistant
python -m src.main --mode interactive

# Sinh lại toàn bộ file trong output/ (tất định, seed=42)
python -m src.main --mode generate

# Chạy bộ test (89 test)
python -m pytest

# Đo các chỉ số chất lượng
python scripts/baseline.py --out docs/baseline.txt
```

### 3.2 Các file trong `output/`


| File                | Nội dung                                        | Sinh bởi              |
| ------------------- | ----------------------------------------------- | --------------------- |
| `grammar.txt`       | Bộ văn phạm CFG có trọng số và chú thích        | `generate_outputs.py` |
| `samples.txt`       | 10 000 câu hỏi sinh từ văn phạm                 | `generate_outputs.py` |
| `parse-results.txt` | Cây phân tích cú pháp cho `input/sentences.txt` | `src.parser`          |
| `semantic.txt`      | Biểu diễn ngữ nghĩa (dạng logic)                | `src.semantic`        |
| `intent-entity.txt` | Intent & entity nhận diện được                  | `src.semantic`        |
| `query.txt`         | Truy vấn gửi tới knowledge base                 | `src.knowledge_base`  |
| `answer.txt`        | Câu trả lời cho người dùng                      | `src.knowledge_base`  |
| `dialogue.txt`      | Hội thoại có xử lý ngữ cảnh cục bộ              | `src.dialogue`        |
| `evaluation.txt`    | Báo cáo đánh giá hệ thống                       | `scripts/baseline.py` |


---

## 4. Mô tả kiến trúc hệ thống

Hệ thống gồm 6 tầng, mỗi tầng nhận đầu vào từ tầng trước và trả kết quả cho
tầng sau:

```
Input (câu hỏi tiếng Việt)
   │
   ▼  [1] Preprocessing
   ├─ Normalize : Unicode NFC → lowercase → chuẩn hoá dấu → gộp khoảng trắng
   ├─ Tokenize  : tách từ, bảo vệ mã L.O.X.Y
   ├─ POS Tag   : gán nhãn từ loại theo luật
   └─ Spans     : nhận diện thực thể nhiều từ ("bài tập lớn", "tín chỉ")
   │
   ▼  [2] Parsing  (src/grammar.py + src/parser.py)
   └─ CFG Grammar → Recursive Descent Parser → Parse Tree
      (có cơ chế fallback dựng cây theo mẫu khi không khớp văn phạm)
   │
   ▼  [3] Semantic Representation  (src/semantic.py)
   └─ Parse tree / văn bản → dạng logic   GET_INTENT(entity=value)
   │
   ▼  [4] Intent & Entity
   ├─ Intent : khớp luật theo thứ tự ưu tiên + chấm điểm từ khoá
   └─ Entity : nhận diện & chuẩn hoá qua models/lexicon.json
   │
   ▼  [5] Query & Knowledge Base  (src/knowledge_base.py)
   └─ (intent, entities) → truy vấn có tham số → tra cứu 9 nhóm thông tin
   │
   ▼  [6] Answer Generation
   └─ Sinh câu trả lời tiếng Việt; nếu thiếu dữ liệu → thông báo, không bịa
```

Ngoài ra còn có **tầng ngữ cảnh hội thoại** (`src/dialogue.py`) đặt cạnh tầng 3,
giữ trạng thái giữa các lượt để giải quyết tham chiếu tân ngữ.

### 4.1 Cấu trúc thư mục

```
Course_Assistant_Sample/
├── src/
│   ├── __init__.py
│   ├── preprocessing.py     # Tầng 1: normalize, tokenize, POS tag, entity spans
│   ├── grammar.py           # Tầng 2a: CFG, trọng số, detokenize, bộ sinh câu
│   ├── parser.py            # Tầng 2b: recursive-descent parser + fallback
│   ├── semantic.py          # Tầng 3-4: logical form, intent, entity
│   ├── knowledge_base.py    # Tầng 5-6: dữ liệu môn học, query engine, câu trả lời
│   ├── dialogue.py          # Tầng ngữ cảnh: DialogueState, DialogueManager
│   ├── evaluation.py        # Sinh báo cáo đánh giá (output/evaluation.txt)
│   └── main.py              # CourseAssistant — điều phối pipeline + CLI
├── models/
│   └── lexicon.json         # Bảng tra cứu surface form → canonical value
├── data/
│   └── course_data.txt      # Knowledge base của môn học
├── input/
│   └── sentences.txt        # 34 câu đầu vào cho bộ phân tích cú pháp
├── output/                  # Các sản phẩm sinh ra (xem bảng ở mục 3.2)
├── scripts/
│   ├── baseline.py          # Đo chỉ số chất lượng
│   └── generate_outputs.py  # Sinh lại output/ một cách tất định
├── tests/                   # 89 test pytest
│   ├── conftest.py          # Fixture dùng chung
│   ├── known_issues.py      # Sổ đăng ký lỗi còn lại (xfail)
│   └── data/                # Bản sao dữ liệu mẫu chính thức
├── docs/
│   ├── REPORT.md            # Báo cáo bài tập lớn
│   └── baseline.txt         # Kết quả đo baseline
├── README.md
├── Dockerfile
├── requirements.txt         # Dependency runtime (rỗng — chỉ dùng thư viện chuẩn)
├── pytest.ini
└── .gitignore
```

### 4.2 Đặc điểm thiết kế đáng chú ý

`src/grammar.py` **là nguồn sự thật duy nhất cho ngôn ngữ.** Bộ phân tích cú
pháp đọc productions, terminal classes và tập FIRST/FOLLOW trực tiếp từ văn
phạm, thay vì hard-code một bản sao. Nhờ vậy khi văn phạm thay đổi, parser tự
động đồng bộ — không thể xảy ra tình trạng "văn phạm và parser lệch nhau".

---

## 5. Mô tả grammar

### 5.1 Cấu trúc

Văn phạm nằm trong `src/grammar.py` (lớp `CFG`), xuất ra `output/grammar.txt`
(254 dòng, **28 non-terminal**, **119 terminal**).

```
S              → WH_QUESTION | YES_NO_QUESTION
WH_QUESTION    → WH_QWORD NP VP PUNCT | NP VP PUNCT
YES_NO_QUESTION→ NP VP PUNCT

WH_QWORD       → "gì" | "nào" | "bao_nhiêu" | "ở_đâu" | "khi_nào" | "thế_nào" | "ai"

NP             → COURSE_NAME | CHAPTER_REF | WEEK_REF | TOPIC_NAME
               | ASSIGNMENT_NAME | LO_ID | DET NOMINAL | NOMINAL | PRONOUN

CHAPTER_REF    → "chương" | "chương" CHAPTER_NUM | "chương" WH_QWORD
WEEK_REF       → "tuần"  | "tuần" WEEK_NUM      | "tuần"  WH_QWORD

VP             → VERB | VERB NP | VERB PP | VERB WH_QWORD
               | VERB WH_QWORD NP | AUX VERB NP | AUX VERB NP PP
PP             → PREP NP | PREP NOUN

COURSE_NAME    → "nlp" | "co3085" | "xử_lý_ngôn_ngữ_tự_nhiên"
CHAPTER_NUM    → "1" … "12"          WEEK_NUM  → "1" … "15"
TOPIC_NAME     → "cfg" | "pcfg" | "parsing" | "semantic" | "syntax" | "pos"
               | "feature" | "grammar" | "tagging" | "disambiguation"
ASSIGNMENT_NAME→ "btl" | "bài_tập_lớn" | "assignment"
LO_ID          → "l.o.1.1" … "l.o.4.2"
PUNCT          → "?" | "!"
```

### 5.2 Đặc điểm thiết kế


| Đặc điểm                     | Giải thích                                                                                                                         |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **Từ hỏi nằm trong vị ngữ**  | Khớp với cách diễn đạt tiếng Việt thực tế. Nếu đặt từ hỏi ở đầu câu, bộ sinh sẽ sinh ra câu vô nghĩa kiểu *"Tuần tuần 15 cần gì?"* |
| **Head noun luôn đi kèm số** | `CHAPTER_REF → "chương" CHAPTER_NUM` đảm bảo số trần không bao giờ đứng một mình (*"10 nói nào?"*)                                 |
| **Luật có trọng số**         | Biến CFG thành PCFG nhẹ: động từ `học` (3.0) sinh nhiều hơn `tra` (0.3) → câu nghe tự nhiên                                        |
| **Luật có chú thích**        | Mỗi luật có comment tiếng Việt, `output/grammar.txt` tự giải thích được                                                            |


### 5.3 Ví dụ đọc văn phạm

Câu `"Chương 4 nói về gì?"` được suy ra theo cây:

```
S → WH_QUESTION
  → NP → CHAPTER_REF → "chương" CHAPTER_NUM → "4"
  → VP → VERB "nói" | VERB "về" | DET "gì"
```

---

## 6. Mô tả parser

### 6.1 Thuật toán

**Recursive-descent parsing (top-down)** với cơ chế backtracking, nằm trong
`src/parser.py`:

```
parse(text):
    tokens ← tokenize_input(text)
    tree   ← _parse_question()
    if tree ≠ null và đã tiêu thụ hết tokens:
        return tree                      # phân tích thành công
    fallback ← _parse_fallback(text)     # dựng cây theo mẫu
    if fallback ≠ null: return fallback
    return null, errors                 # không thuộc văn phạm
```

Các hàm đệ quy tương ứng từng non-terminal:


| Hàm                        | Phụ trách                                           |
| -------------------------- | --------------------------------------------------- |
| `_parse_question()`        | Chọn nhánh `WH_QUESTION` hoặc `YES_NO_QUESTION`     |
| `_parse_wh_question()`     | `WH_QWORD` + `NP` + `VP` + dấu câu hỏi              |
| `_parse_yes_no_question()` | `NP` + `VP` + dấu câu hỏi                           |
| `_parse_np()`              | Định danh miền, `DET NOMINAL`, `NOMINAL`, `PRONOUN` |
| `_parse_vp()`              | `VERB` kèm `NP` / `PP` / `WH_QWORD` / `AUX`         |


Bảng tra cứu (`_build_lookup_tables()`) được sinh tự động từ văn phạm nên
parser luôn đồng bộ với grammar.

### 6.2 Cơ chế fallback

Khi câu không khớp văn phạm nghiêm ngặt, `_parse_fallback()` phân loại từng
token theo bảng từ khoá rồi dựng cây theo mẫu (`WH_WORD` | `NP` | `VP` |
`PUNCT`). Cơ chế này giữ intent accuracy cao ngay cả khi strict parse thấp, vì
tầng semantic làm việc trực tiếp trên văn bản chứ không phụ thuộc cây cú pháp.

### 6.3 Định dạng đầu ra

Kết quả ghi ra `output/parse-results.txt`:

```
(WH_QUESTION (WH_WORD chương) (NP (NUM 4)) (VP (VERB nói) (VERB về) (DET gì)))
```

Câu không thuộc văn phạm được xuất `()`.

### 6.4 Kết quả đo


| Chế độ                   | Số câu | Tỉ lệ (34 câu kiểm thử chính thức) |
| ------------------------ | ------ | ---------------------------------- |
| Strict recursive descent | 4      | 11.76 %                            |
| Pattern fallback         | 30     | 88.24 %                            |
| Thất bại                 | 0      | 0 %                                |


---

## 7. Mô tả semantic representation

### 7.1 Dạng logic

Mỗi câu hỏi được ánh xạ thành một **dạng logic** có cấu trúc
(`src/semantic.py`):

```python
@dataclass
class SemanticRepresentation:
    intent: IntentType                  # Ý định của câu hỏi
    entities: Dict[str, Any]            # Các thực thể đã nhận diện
    attributes: Dict[str, bool]         # Thuộc tính cần truy vấn
    query_type: str                     # Loại truy vấn
    raw_query: str                      # Câu gốc
```

Cấu trúc dạng logic: `GET_INTENT(entity₁=value₁, entity₂=value₂, …)`

### 7.2 Ví dụ


| Câu hỏi                         | Dạng logic                                       |
| ------------------------------- | ------------------------------------------------ |
| "Môn NLP có bao nhiêu tín chỉ?" | `GET_COURSE_INFO(course=NLP, attribute=credits)` |
| "Tuần 3 học gì?"                | `GET_SCHEDULE(week=WEEK_03)`                     |
| "Chương 4 nói về gì?"           | `GET_TOPIC(chapter=CH04)`                        |
| "Chương nào học về CFG?"        | `GET_TOPIC(topic=CFG)`                           |
| "Deadline BTL là khi nào?"      | `GET_DEADLINE(assignment=BTL01)`                 |
| "Có được dùng LLM không?"       | `GET_RULE()`                                     |
| "L.O.4.2 là gì?"                | `GET_LO(lo=LO4.2)`                               |


### 7.3 Tập Intent


| Intent            | Mô tả                                                                |
| ----------------- | -------------------------------------------------------------------- |
| `GET_COURSE_INFO` | Thông tin chung môn học (tín chỉ, mô tả, mục tiêu, giữa kỳ, cuối kỳ) |
| `GET_SCHEDULE`    | Lịch học theo tuần, hoặc tuần dạy một chương/chủ đề                  |
| `GET_TOPIC`       | Nội dung / chủ đề của chương                                         |
| `GET_ASSIGNMENT`  | Thông tin bài tập lớn và các phần                                    |
| `GET_DEADLINE`    | Mốc thời gian nộp bài                                                |
| `GET_RESOURCE`    | Tài liệu tham khảo                                                   |
| `GET_RULE`        | Quy định môn học                                                     |
| `GET_INSTRUCTOR`  | Giảng viên phụ trách                                                 |
| `GET_LO`          | Mục tiêu học tập (Learning Outcome)                                  |
| `UNKNOWN`         | Ngoài phạm vi hệ thống                                               |


---

## 8. Mô tả phương pháp xử lý intent / entity

### 8.1 Intent — phương pháp dựa trên luật

**Kỹ thuật:** khớp từ khoá + biểu thức chính quy (regex), theo **thứ tự ưu tiên
từ cụ thể đến chung**, kết hợp chấm điểm từ khoá ở bước cuối.

```
Bước 1  Kiểm tra ngoài phạm vi (thời tiết, bóng đá, giá vàng, giải bài toán…)
        → nếu khớp: return UNKNOWN

Bước 2  Các intent có mẫu đặc biệt, theo thứ tự ưu tiên:
        GET_DEADLINE → GET_LO → GET_INSTRUCTOR → GET_RULE
        → GET_RESOURCE → GET_ASSIGNMENT → GET_SCHEDULE → GET_TOPIC

Bước 3  Chấm điểm từ khoá cho từng intent:
        score = (# từ khoá xuất hiện) + 2 × (# pattern khớp)
        → trả intent có điểm cao nhất (nếu điểm > 0), ngược lại UNKNOWN
```

**Vì sao cần thứ tự ưu tiên?** Nhiều từ khoá xung đột. *"Tài liệu nào liên quan
đến PCFG?"* chứa cả `tài liệu` (→ GET_RESOURCE) lẫn `pcfg` (→ GET_TOPIC). Đặt
GET_RESOURCE trước GET_TOPIC giải quyết mâu thuẫn này.

### 8.2 Entity — trích xuất theo luật + lexicon

Entity được trích xuất theo 3 lớp:

```
Lớp 1 — Định danh miền (khớp trực tiếp)
    course      : "nlp" | "co3085" → NLP | CO3085
    chapter     : /chương\s*(\d+)/          → CH04
    week        : /tuần\s*(\d+)/            → WEEK_12
    topic       : cfg, pcfg, parsing, semantic, … → CFG, PCFG, …
    assignment  : "btl" | "bài tập lớn"      → BTL01
    lo          : /lo_(\d)(?:_(\d+))?/     → LO2.5

Lớp 2 — Lexicon chuẩn hoá (models/lexicon.json)
    surface form → canonical value
    "semantic grammar"        → SEMANTIC_GRAMMAR
    "selectional restriction" → SELECTIONAL_RESTRICTION
    "llm/rag"                 → LLM_RAG
    "phần ii"                 → PART_II
    "sách tham khảo"          → REFERENCE_BOOK

Lớp 3 — Suy luận theo intent
    GET_COURSE_INFO + "tín chỉ"  → attribute=credits
    GET_COURSE_INFO + "giữa kỳ"  → attribute=midterm_duration
    GET_ASSIGNMENT + "phần ii"   → part=PART_II
```

Bảng lexicon được kiểm thử tự động bằng `tests/test_lexicon.py` (11 test),
bao gồm kiểm tra mọi surface form đều ở dạng chữ thường để tra cứu không phân
biệt hoa thường.

---

## 9. Knowledge base và cách truy vấn

### 9.1 Cấu trúc knowledge base

Dữ liệu môn học nằm trong `data/course_data.txt`, được nạp vào lớp
`KnowledgeBase` (`src/knowledge_base.py`) dưới dạng dict có cấu trúc:


| Nhóm          | Nội dung                                                                       |
| ------------- | ------------------------------------------------------------------------------ |
| `course`      | Thông tin chung: tên, mã, số tín chỉ, mô tả, mục tiêu, thời lượng giữa/cuối kỳ |
| `schedule`    | 15 tuần, ánh xạ tuần ↔ chương ↔ nội dung                                       |
| `chapters`    | 12 chương, nội dung và chủ đề từng chương                                      |
| `assignment`  | BTL: 4 phần (PART_I…PART_IV), yêu cầu, file phải xuất, checkpoint              |
| `resources`   | Danh mục sách tham khảo, slide, tài liệu                                       |
| `regulations` | Quy định dùng AI/LLM, chính sách bản quyền                                     |
| `faq`         | Câu hỏi thường gặp                                                             |


### 9.2 Cách truy vấn

Truy vấn được dựng từ cặp `(intent, entities)` — mỗi intent ánh xạ tới một hàm
truy vấn riêng:

```
query(intent, entities):
    GET_COURSE_INFO → get_course_info(attribute)
    GET_TOPIC        → get_chapter_info(chapter) | get_topic_chapter(topic)
    GET_SCHEDULE     → get_chapter_week(chapter) | get_topic_week(topic)
                       | get_schedule(week)
    GET_ASSIGNMENT   → get_assignment_info(part, list_parts)
    GET_DEADLINE     → get_deadline()
    GET_RESOURCE     → get_resource(topic)
    GET_RULE         → get_regulation(rule)
    GET_LO           → get_learning_outcome(lo)
    (mặc định)       → "Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu môn học."
```

Đây là truy vấn có tham số theo mẫu (template-based query), không phải truy vấn
SQL hay vector search — phù hợp với hướng Classical/Statistical NLP và đủ cho
miền dữ liệu hẹp.

### 9.3 Xử lý trường hợp không tìm thấy thông tin

Khi truy vấn không có kết quả, hệ thống trả về thông báo:

```
"Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu môn học."
```

Hệ thống **không tự tạo thông tin** khi không có dữ liệu — đây là yêu cầu bắt
buộc của đề bài (mục 4.1.5).

---

## 10. Lựa chọn hướng thực hiện

Nhóm thực hiện theo **Lựa chọn 1: Classical / Statistical NLP**.

### 10.1 Nội dung đã dùng


| Kỹ thuật                                        | Nơi áp dụng                              |
| ----------------------------------------------- | ---------------------------------------- |
| Văn phạm CFG có trọng số (PCFG-lite)            | `src/grammar.py`                         |
| Sinh câu bằng mở rộng đệ quy theo trọng số      | `src/grammar.py`                         |
| Phân tích cú pháp recursive descent (top-down)  | `src/parser.py`                          |
| Tính FIRST/FOLLOW cho văn phạm                  | `src/grammar.py`                         |
| Biểu diễn ngữ nghĩa dạng logic form             | `src/semantic.py`                        |
| Nhận diện intent bằng luật + chấm điểm từ khoá  | `src/semantic.py`                        |
| Trích xuất entity bằng luật + lexicon tra cứu   | `src/semantic.py`, `models/lexicon.json` |
| Truy vấn knowledge base theo mẫu có tham số     | `src/knowledge_base.py`                  |
| Giải quyết tham chiếu ngữ cảnh cục bộ bằng luật | `src/dialogue.py`                        |


### 10.2 Lựa chọn phương pháp phân loại intent


| Phương án                            | Đánh giá                                                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| **Luật + từ khoá (đang dùng)**       | Minh bạch, không cần dữ liệu huấn luyện, giải thích được từng quyết định, phù hợp miền hẹp. Được chọn. |
| Học máy thống kê (Naive Bayes / SVM) | Có thể thêm sau để tăng độ bao phủ; luật giữ vai trò fallback khi độ tin cậy thấp.                     |
| LLM / RAG                            | Là **phần mở rộng**, không bắt buộc, và không thay thế được các thành phần NLP cốt lõi.                |


Hệ thống **không dùng LLM ở bất kỳ đâu** — toàn bộ pipeline xử lý ngôn ngữ
bằng luật, đúng như yêu cầu của Lựa chọn 1.

---

## 11. Mô tả cách đánh giá

### 11.1 Tập kiểm thử

Lấy từ dữ liệu mẫu chính thức (`tests/data/sample_queries.txt`, **34 câu**),
bao phủ:


| Nhóm                       | Số câu |
| -------------------------- | ------ |
| Câu hỏi hợp lệ trong miền  | 29     |
| Câu hỏi ngoài phạm vi      | 2      |
| Câu hỏi phụ thuộc ngữ cảnh | 3      |


Thêm **5 kịch bản hội thoại** (`tests/data/dialogues.txt`) cho ngữ cảnh cục bộ.

### 11.2 Công cụ đánh giá

```bash
# Chạy bộ test đầy đủ (89 test)
python -m pytest

# Đo các chỉ số
python scripts/baseline.py --out docs/baseline.txt
```

`scripts/baseline.py` đo 4 nhóm chỉ số:

1. **Intent accuracy** — tỉ lệ intent đúng trên tập chính thức
2. **Entity accuracy** — đo cả bản alias-aware lẫn khớp thô
3. **Intent + Entity accuracy** — độ chính xác tổng thể của pipeline
4. **Chất lượng parse** — tỉ lệ strict / fallback / failure
5. **Chất lượng sinh câu** — số câu chứa `_`, rò non-terminal, sai dấu câu

### 11.3 Kết quả hiện tại

**Trên 34 câu hỏi chính thức:**


| Chỉ số                         | Kết quả             |
| ------------------------------ | ------------------- |
| Intent accuracy                | 30/34 — **88.24 %** |
| Entity accuracy (alias-aware)  | 19/34 — 55.88 %     |
| Entity accuracy (khớp thô)     | 16/34 — 47.06 %     |
| **Intent + Entity accuracy**   | 18/34 — **52.94 %** |
| Strict recursive-descent parse | 4/34 — 11.76 %      |
| Pattern fallback parse         | 30/34 — 88.24 %     |
| Parse failure                  | 0/34 — 0 %          |


**Chất lượng bộ sinh câu (10 000 câu):** 0 câu chứa `_`, 0 câu rò non-terminal,  
0 câu mở sai, 0 câu thiếu dấu câu.

### 11.4 Quản lý lỗi tồn đọng

Mọi lỗi chưa sửa được liệt kê tập trung trong `tests/known_issues.py`, mỗi lỗi
ghi rõ nguyên nhân và Work Package chịu trách nhiệm:

```python
"test_official_query[Q007]": (
    "topic 'pcfg' bị match sai thành 'cfg' (substring)",
    "WP4",
),
```

Các test này được đánh dấu `xfail` (non-strict) nên quality gate luôn xanh,
nhưng lỗi vẫn hiện rõ mỗi lần chạy và không thể bị "quên".

---

## 12. Ghi chú về tính trung thực học thuật

Hệ thống được xây dựng bằng phương pháp **Classical/Statistical NLP dựa trên
luật** — không sử dụng LLM hay API bên ngoài ở bất kỳ thành phần nào. Toàn bộ
mã nguồn dùng thư viện chuẩn của Python.

Mọi chỉ số trong tài liệu này đều **tự động sinh bằng script** (`scripts/baseline.py`)
chứ không ước lượng tay, và mọi hạn chế đều có test tương ứng trong bộ test.

---

*Course Assistant — Bài tập lớn CO3085 — Kỳ học HK261*