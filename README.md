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
| Python            | 3.9 trở lên (đã kiểm thử trên 3.14)                    |
| Thư viện ngoài    | **Không** — phần lõi chỉ dùng thư viện chuẩn của Python |
| Thư viện cho test | `pytest` (tuỳ chọn)                                     |

Hệ thống được viết **không phụ thuộc thư viện bên ngoài** (không cần NLTK,
spaCy, hay bất kỳ framework NLP nào) để bảo đảm chạy được trong bất kỳ môi
trường chấm bài nào. `pytest` chỉ cần khi chạy bộ test.

### 2.2 Cài đặt

```bash
# 1. Clone repository
git clone https://github.com/thanhcong10082005/Course-Assistant.git
cd Course-Assistant/Course_Assistant_Sample

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
# Build (chạy từ thư mục gốc của gói, tức là Course_Assistant_Sample/)
docker build -t course-assistant .

# Chạy thử — container sinh ra 9 file trong output/ rồi thoát
docker run --rm course-assistant

# Chạy chế độ hỏi đáp tương tác
docker run -it course-assistant python -m src.main --mode interactive

# Hoặc dùng docker-compose (ghi artifact thẳng ra máy host)
docker compose up --build
docker compose down
```

Image không cài thêm gói NLP nào — chỉ dùng thư viện chuẩn của Python. Nếu
`docker build` báo lỗi kéo image `python:3.11-slim`, chạy lại lần hai (lần đầu
thường chậm vì tải base image ~130 MB).

---

## 3. Chạy chương trình

### 3.1 Các lệnh chính

```bash
cd Course_Assistant_Sample

# Chế độ demo — in pipeline, grammar, parsing (mặc định)
python -m src.main --mode demo

# Chế độ tương tác — hỏi đáp trực tiếp với Course Assistant
#   (lệnh phụ: /context xem ngữ cảnh, /reset xoá ngữ cảnh, exit để thoát)
python -m src.main --mode interactive

# Sinh lại toàn bộ file trong output/ (tất định, seed=42)
python -m src.main --mode generate

# Chạy bộ test (158 test)
python -m pytest

# Chạy báo cáo đánh giá (57 câu kiểm thử)
python -m src.evaluation

# Đo các chỉ số chất lượng
python scripts/baseline.py --out docs/baseline.txt

# Kiểm tra gói nộp bài trước khi nộp
python scripts/check_submission.py
```

### 3.2 Các file trong `output/`

| File                | Nội dung                                        | Sinh bởi              |
| ------------------- | ----------------------------------------------- | --------------------- |
| `grammar.txt`       | Bộ văn phạm CFG có trọng số và chú thích        | `src.grammar`         |
| `samples.txt`       | 95 câu mẫu có nhãn intent + 10 000 câu sinh từ văn phạm | `src.grammar`   |
| `parse-results.txt` | Cây phân tích cú pháp + nhãn `[STRICT]`/`[FALLBACK]`/`[INVALID]` | `src.parser` |
| `semantic.txt`      | Biểu diễn ngữ nghĩa (dạng logic)                | `src.semantic`        |
| `intent-entity.txt` | Intent & entity nhận diện được                  | `src.semantic`        |
| `query.txt`         | Truy vấn gửi tới knowledge base                 | `src.knowledge_base`  |
| `answer.txt`        | Câu trả lời cho người dùng                      | `src.knowledge_base`  |
| `dialogue.txt`      | 5 hội thoại, mỗi lượt có đủ 4 phần             | `src.dialogue`        |
| `evaluation.txt`    | Báo cáo đánh giá hệ thống (6 mục)               | `src.evaluation`      |

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
   └─ CFG Grammar → Earley Chart Parser → Parse Tree
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
   └─ (intent, entities) → truy vấn có tham số → tra cứu tri thức môn học
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
│   ├── parser.py            # Tầng 2b: Earley chart parser + fallback
│   ├── lexicon.py           # Tra cứu surface form → canonical value (longest-match)
│   ├── semantic.py          # Tầng 3-4: logical form, intent, entity
│   ├── knowledge_base.py    # Tầng 5-6: dữ liệu môn học, query engine, câu trả lời
│   ├── dialogue.py          # Tầng ngữ cảnh: DialogueState, DialogueManager
│   ├── evaluation.py        # Sinh báo cáo đánh giá (output/evaluation.txt)
│   └── main.py              # CourseAssistant — điều phối pipeline + CLI
├── models/
│   └── lexicon.json         # Bảng tra cứu surface form → canonical value
├── data/
│   └── course_data.txt      # Bản tóm tắt knowledge base của môn học
├── input/
│   └── sentences.txt        # 34 câu đầu vào cho bộ phân tích cú pháp
├── output/                  # Các sản phẩm sinh ra (xem bảng ở mục 3.2)
├── scripts/
│   ├── baseline.py          # Đo chỉ số chất lượng
│   ├── check_submission.py  # Kiểm tra gói nộp bài
│   └── generate_outputs.py  # Sinh lại output/ một cách tất định
├── tests/                   # 158 test pytest
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
(386 dòng, **36 non-terminal**, **182 terminal**, **307 production**).

```
S              → WH_QUESTION | YES_NO_QUESTION
WH_QUESTION    → WH_QWORD NP VP PUNCT | NP VP PUNCT
YES_NO_QUESTION→ NP VP PUNCT
WH_QWORD       → "gì" | "nào" | "bao_nhiêu" | "ở_đâu" | "khi_nào" | "thế_nào" | "ai"
NP             → COURSE_REF | CHAPTER_REF | WEEK_REF | TOPIC_NAME
               | ASSIGNMENT_NAME | TECH_NAME | LO_ID | ATTR_NOUN | PART_REF
               | DET NOMINAL | NOMINAL | PRONOUN | QUANT ATTR_NOUN | …
CHAPTER_REF    → "chương" | "chương" CHAPTER_NUM | "chương" WH_QWORD
WEEK_REF       → "tuần"  | "tuần" WEEK_NUM      | "tuần"  WH_QWORD
VP             → VERB | VERB NP | VERB PP | VERB WH_QWORD | AUX VERB NP | …
CHAPTER_NUM    → "1" … "12"          WEEK_NUM  → "1" … "15"
TOPIC_NAME     → "cfg" | "pcfg" | "parsing" | "semantic" | "semantic_grammar"
               | "syntax" | "pos" | "feature" | "grammar" | "tagging" | …
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
(WH_QUESTION (NP (CHAPTER_REF (chương) (CHAPTER_NUM (4))))
             (VP (VERB (nói_về)) (ADV (gì)))
             (PUNCT (?)))
```

---

## 6. Mô tả parser

### 6.1 Thuật toán

**Earley chart parsing** (bottom-up, xử lý nhập bằng tự nhiên), nằm trong
`src/parser.py`:

```
parse(text):
    tokens ← tokenize_input(text)
    tree   ← _earley_parse(tokens)        # nhận diện theo văn phạm
    if tree ≠ null:
        return tree                       # phân tích thành công
    fallback ← _parse_fallback(text)      # dựng cây theo mẫu
    if fallback ≠ null: return fallback
    return null, errors                  # không thuộc văn phạm
```

Ba pha chính của Earley: **Predict** (dự đoán non-terminal), **Scan** (quét
terminal), **Complete** (hoàn tất production). Văn phạm là **nhập đơn vị** của
Earley: productions, terminal classes và tập từ vựng đều được đọc trực tiếp từ
`src/grammar.py`, nên parser không bao giờ lệch khỏi văn phạm.

### 6.2 Cơ chế fallback

Khi câu không khớp văn phạm nghiêm ngặt, `_parse_fallback()` phân loại từng
token theo bảng từ khoá rồi dựng cây theo mẫu (`WH_WORD` | `NP` | `VP` |
`PUNCT`). Cơ chế này giữ intent accuracy cao ngay cả khi strict parse thấp, vì
tầng semantic làm việc trực tiếp trên văn bản chứ không phụ thuộc cây cú pháp.

### 6.3 Định dạng đầu ra

Kết quả ghi ra `output/parse-results.txt`, mỗi câu kèm nhãn chế độ parse:

```
Môn NLP có bao nhiêu tín chỉ?
[STRICT]
(WH_QUESTION (NP (COURSE_REF (COURSE_MOD (môn)) (COURSE_NAME (nlp))))
             (VP (VERB (có)) (NP (QUANT (bao_nhiêu)) (ATTR_NOUN (tín_chỉ))))
             (PUNCT (?)))
```

Nhãn: `[STRICT]` = parse bằng Earley theo văn phạm · `[FALLBACK]` = ngoài văn
phạm, dựng theo mẫu · `[INVALID]` = không dựng được cây.

### 6.4 Kết quả đo

| Chế độ                    | Số câu | Tỉ lệ (34 câu kiểm thử chính thức) |
| ------------------------- | ------ | ---------------------------------- |
| Strict (Earley chart)     | 31     | **91.18 %**                       |
| Pattern fallback          | 3      | 8.82 %                            |
| Thất bại                  | 0      | 0 %                               |

3 câu rơi vào fallback là `Q026` ("Hôm nay ở TP.HCM có mưa không?"), `Q027`
("Ai là tổng thống của Pháp?") và `Q028` ("Hãy giải bài tập xác suất này giúp
tôi.") — cả ba đều **cố ý nằm ngoài phạm vi** của đề bài. Trên 31 câu in-scope,
strict parse đạt **100 %**.

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
| "Môn NLP có bao nhiêu tín chỉ?" | `GET_COURSE_INFO(course=CO3085, attribute=credits)` |
| "Tuần 3 học gì?"                | `GET_SCHEDULE(week=WEEK_03)`                     |
| "Chương 4 nói về gì?"           | `GET_TOPIC(chapter=CH04)`                        |
| "Chương nào học về CFG?"        | `GET_TOPIC(topic=CFG)`                           |
| "Deadline BTL là khi nào?"      | `GET_DEADLINE(attribute=deadline, assignment=BTL01)` |
| "Có được dùng LLM không?"       | `GET_RULE(rule=LLM_RAG)`                         |
| "L.O.4.2 là gì?"                | `GET_LO(lo=LO4.2)`                               |

### 7.3 Tập Intent

Hệ thống hỗ trợ **11 intent**:

| Intent            | Mô tả                                                                |
| ----------------- | -------------------------------------------------------------------- |
| `GET_COURSE_INFO` | Thông tin chung môn học (tín chỉ, mô tả, mục tiêu, giữa kỳ, cuối kỳ) |
| `GET_SCHEDULE`    | Lịch học theo tuần, hoặc tuần dạy một chương/chủ đề                  |
| `GET_TOPIC`       | Nội dung / chủ đề của chương                                         |
| `GET_ASSIGNMENT`  | Thông tin bài tập lớn và các phần                                    |
| `GET_DEADLINE`    | Mốc thời gian nộp bài                                                |
| `GET_RESOURCE`    | Tài liệu tham khảo                                                   |
| `GET_RULE`        | Quy định môn học                                                     |
| `GET_LO`          | Mục tiêu học tập (Learning Outcome)                                  |
| `GET_INSTRUCTOR`  | Giảng viên phụ trách và giờ gặp trực tiếp                             |
| `CONTEXT_DEPENDENT` | Câu hỏi phụ thuộc lượt trước — cần ngữ cảnh để trả lời            |
| `UNKNOWN`         | Ngoài phạm vi hệ thống                                               |

---

## 8. Mô tả phương pháp xử lý intent / entity

### 8.1 Intent — phương pháp dựa trên luật

**Kỹ thuật:** bảng luật có **trọng số** (`INTENT_RULES` trong `src/semantic.py`),
mỗi luật là một cặp `(intent, regex, điểm)`. Điểm cao hơn thắng; các điểm cộng
theo entity được dùng để phá thế hoà.

```
Bước 1  Kiểm tra ngoài phạm vi (lexicon.out_of_scope + mẫu "giải bài tập…")
        → nếu khớp: return UNKNOWN

Bước 2  Chấm điểm các luật trong INTENT_RULES:
        score(intent) = Σ điểm của các regex khớp
        + điểm cộng theo entity đã trích (rule, chapter, part, lo…)

Bước 3  Nếu câu chứa tham chiếu ngữ cảnh mà không có hội thoại đang mở
        → intent = CONTEXT_DEPENDENT (xin người dùng làm rõ)
```

**Vì sao cần chấm điểm thay vì thứ tự ưu tiên cứng?** Nhiều từ khoá xung đột.
*"Tài liệu nào liên quan đến PCFG?"* chứa cả `tài liệu` (→ GET_RESOURCE) lẫn
`pcfg` (→ GET_TOPIC). Chấm điểm cho phép nhiều tín hiệu cùng tồn tại thay vì
phải cố đặt một thứ tự tuần tự.

### 8.2 Entity — trích xuất theo luật + lexicon

Entity được trích xuất qua **3 lớp**, tất cả đều dựa trên `src/lexicon.py`
(`models/lexicon.json` là nguồn sự thật duy nhất):

```
Lớp 1 — Lexicon tra cứu theo chiến lược LONGEST-MATCH
    "semantic grammar"        → topic=SEMANTIC_GRAMMAR   (thắng "semantic")
    "statistical nlp"         → topic=STATISTICAL_NLP    (thắng "nlp")
    "pcfg"                    → topic=PCFG               (thắng "cfg")
    "chương 4"                → chapter=CH04
    "tuần 3"                  → week=WEEK_03
    "l.o.2.5"                 → lo=LO2.5
    "llm/rag"                 → rule=LLM_RAG
    "hỏi đáp"                 → part=PART_II

Lớp 2 — Suy luận theo nhóm ưu tiên
    assignment_part > part_of_assignment > assignment > learning_outcome
    > chapter > week > rule > attribute > topic > course > resource
    > instructor
    (nhóm "part_of_assignment" cho phép "parser" → part=PART_I,
     "hỏi đáp" → part=PART_II)

Lớp 3 — Thuộc tính của câu hỏi
    "tín chỉ"   → attribute=credits
    "giữa kỳ"   → attribute=midterm_duration
    "cuối kỳ"   → attribute=final_duration
```

Bảng lexicon được kiểm thử tự động bằng `tests/test_lexicon.py` (11 test),
bao gồm kiểm tra mọi surface form đều ở dạng chữ thường để tra cứu không phân
biệt hoa thường.

---

## 9. Knowledge base và cách truy vấn

### 9.1 Cấu trúc knowledge base

Dữ liệu môn học nằm ngay trong `src/knowledge_base.py` (một module Python với
các hằng dict có cấu trúc), được nạp vào lớc `KnowledgeBase` dưới dạng dict:

| Nhóm          | Nội dung                                                                       |
| ------------- | ------------------------------------------------------------------------------ |
| `COURSE_INFO` | Thông tin chung: tên, mã, số tín chỉ, mô tả, mục tiêu, thời lượng giữa/cuối kỳ, giảng viên |
| `SCHEDULE`    | 15 tuần, ánh xạ tuần ↔ chương ↔ nội dung ↔ hoạt động ↔ mốc nộp                 |
| `CHAPTERS`    | 12 chương: tóm tắt, chủ đề con, tuần dạy, phương pháp, mục tiêu học tập phục vụ |
| `ASSIGNMENT`  | BTL: 4 phần (PART_I…PART_IV), yêu cầu, file phải xuất, checkpoint, tiêu chí    |
| `RESOURCES`   | Danh mục 7 tài liệu tham khảo, slide, ghi chú — kèm chủ đề liên quan            |
| `REGULATIONS` | 7 nhóm quy định: tham dự, liêm chính học thuật, dùng AI, LLM/RAG, bản quyền, chính sách, phạm vi |
| `FAQ`         | 7 câu hỏi thường gặp                                                             |
| `TOPIC_TO_CHAPTER` / `LO_TO_CHAPTERS` | Ánh xạ ngược: chủ đề → chương, LO → chương |

Ngoài ra có các hàm trả lời theo ngữ cảnh:
`ask_for_clarification()` (câu cần ngữ cảnh), `unknown_answer()` (không hiểu),
`out_of_scope_answer()` (ngoài phạm vi môn học).

> **Nguồn dữ liệu:** toàn bộ tri thức môn học do nhóm biên soạn tay dựa trên đề
> cương môn CO3085 và tài liệu giảng viên cung cấp (`data/course_data.txt` là
> bản tóm tắt dạng văn bản của cùng bộ dữ liệu đó). Không sử dụng dữ liệu từ
> nguồn bên ngoài nào khác.

### 9.2 Cách truy vấn

Truy vấn được dựng từ cặp `(intent, entities)` — mỗi intent ánh xạ tới một hàm
truy vấn riêng:

```
query(intent, entities):
    GET_COURSE_INFO → get_course_info(attribute)
    GET_TOPIC        → get_chapter_info(chapter) | get_topic_detail(topic)
    GET_SCHEDULE     → get_chapter_week(chapter) | get_topic_week(topic)
                       | get_schedule(week)
    GET_ASSIGNMENT   → get_assignment_info(part, list_parts)
                       | get_assignment_deliverables(part)
    GET_DEADLINE     → get_deadline()
    GET_RESOURCE     → get_resource(topic)
    GET_RULE         → get_regulation(rule)
    GET_LO           → get_learning_outcome(lo) | get_lo_chapter(lo)
    GET_INSTRUCTOR   → get_instructor()
    CONTEXT_DEPENDENT→ ask_for_clarification()
    UNKNOWN          → out_of_scope_answer() | unknown_answer()
```

Đây là truy vấn có tham số theo mẫu (template-based query), không phải truy vấn
SQL hay vector search — phù hợp với hướng Classical/Statistical NLP và đủ cho
miền dữ liệu hẹp.

### 9.3 Xử lý trường hợp không tìm thấy thông tin

Hệ thống có **hai** thông báo chuẩn, tùy nguyên nhân:

| Tình huống                              | Thông báo trả về                                              |
| --------------------------------------- | ------------------------------------------------------------- |
| Ngoài phạm vi môn học (`scope=OUT_OF_SCOPE`) | "Hệ thống chỉ chịu trách nhiệm trong phạm vi dữ liệu môn học…" |
| Câu hỏi phụ thuộc ngữ cảnh chưa đủ      | "Tôi cần thêm ngữ cảnh để trả lời câu hỏi này…"             |
| Không xác định được ý định              | "Xin lỗi, tôi không hiểu câu hỏi này…"                       |

Ngoài ra, câu hỏi trong phạm vi nhưng knowledge base không có dữ liệu được trả
lời rõ ràng, ví dụ *"Chương 99 nói về gì?"* → "Không tìm thấy thông tin Chương
CH99."

Hệ thống **không tự tạo thông tin** khi không có dữ liệu — đây là yêu cầu bắt
buộc của đề bài (mục 4.1.5).

---

## 10. Xử lý ngữ cảnh hội thoại

Tầng ngữ cảnh nằm trong `src/dialogue.py`, gồm hai lớc:

- **`DialogueState`** — trạng thái diễn ngôn: số lượt, ý định cuối, và các
  thực thể đang "nổi bật" (`last_topic`, `last_chapter`, `last_week`,
  `last_part`, `last_assignment`, `last_lo`) cùng bảng discourse entity.
- **`DialogueManager`** — bộ giải tham chiếu, chạy **trước** bước phân tích
  ngữ nghĩa để câu hỏi trở nên tự chứa.

### 10.1 Bốn loại tham chiếu được hỗ trợ

| Loại                       | Ví dụ                        | Cách giải                                     |
| -------------------------- | ---------------------------- | --------------------------------------------- |
| **Đại từ** (pronoun)       | "Nó có liên quan đến parsing không?" | Thay bằng thực thể nổi bật nhất (ưu tiên chương) |
| **Mô tả xác định** (definite) | "Tài liệu của **chương này** là gì?" | Thay bằng chương/tuần/phần vừa nói |
| **Cấu trúc rút gọn** (ellipsis) | "Còn **chương sau**?"      | Quan hệ "kế tiếp" — cần tri thức miền (12 chương, 15 tuần) |
| **Mô tả xác định + kế tiếp** | "**Phần này** cần xuất file gì?" | Suy ra phần của bài tập đang bàn |

### 10.2 Hai chế độ xử lý

```
process_query(q)   # câu đơn lẻ
  ├─ có tham chiếu?  → CONTEXT_DEPENDENT (hỏi lại người dùng) + gợi ý referent
  └─ không            → trả lời bình thường

process_dialogue(q) # trong phiên hội thoại
  ├─ resolve_reference(q) theo trạng thái → câu tự chứa
  ├─ phân tích ngữ nghĩa → intent + entity
  └─ update_context(...) → cập nhật trạng thái cho lượt sau
```

Ví dụ minh hoạ (`output/dialogue.txt`):

```
User: Chương 4 nói về gì?
Assistant: Chương 04 - Features and Augmented Grammar ...
User: Nó có liên quan đến parsing không?      ← "nó" → CH04
Assistant: Chương 04 - Features and Augmented Grammar ...
User: Còn chương sau?                        ← "chương sau" → CH05
Assistant: Chương 05 - Grammar for Natural Language ...
```

---

## 11. Lựa chọn hướng thực hiện

Nhóm thực hiện theo **Lựa chọn 1: Classical / Statistical NLP**.

### 11.1 Nội dung đã dùng

| Kỹ thuật                                        | Nơi áp dụng                              |
| ----------------------------------------------- | ---------------------------------------- |
| Văn phạm CFG có trọng số (PCFG-lite)            | `src/grammar.py`                         |
| Sinh câu bằng mở rộng đệ quy theo trọng số      | `src/grammar.py`                         |
| Phân tích cú pháp Earley chart (bottom-up)      | `src/parser.py`                          |
| Tính FIRST/FOLLOW cho văn phạm                  | `src/grammar.py`                         |
| Biểu diễn ngữ nghĩa dạng logic form             | `src/semantic.py`                        |
| Nhận diện intent bằng luật có trọng số          | `src/semantic.py`                        |
| Trích xuất entity bằng lexicon longest-match     | `src/lexicon.py`, `models/lexicon.json`   |
| Truy vấn knowledge base theo mẫu có tham số     | `src/knowledge_base.py`                  |
| Giải quyết tham chiếu ngữ cảnh cục bộ bằng luật | `src/dialogue.py`                        |

### 11.2 Lựa chọn phương pháp phân loại intent

| Phương án                            | Đánh giá                                                                                               |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| **Luật + từ khoá (đang dùng)**       | Minh bạch, không cần dữ liệu huấn luyện, giải thích được từng quyết định, phù hợp miền hẹp. Được chọn. |
| Học máy thống kê (Naive Bayes / SVM) | Có thể thêm sau để tăng độ bao phủ; luật giữ vai trò fallback khi độ tin cậy thấp.                     |
| LLM / RAG                            | Là **phần mở rộng**, không bắt buộc, và không thay thế được các thành phần NLP cốt lõi.                |

Hệ thống **không dùng LLM ở bất kỳ đâu** — toàn bộ pipeline xử lý ngôn ngữ
bằng luật, đúng như yêu cầu của Lựa chọn 1.

---

## 12. Mô tả cách đánh giá

### 12.1 Tập kiểm thử

Bộ đánh giá gồm **57 câu** từ **3 nguồn** (`src/evaluation.py`):

| Nguồn                                          | Số câu | Vai trò                                                  |
| ---------------------------------------------- | ------ | -------------------------------------------------------- |
| `tests/data/sample_queries.txt` (chính thức)   | 34     | Câu hỏi có nhãn của đề bài                                |
| Câu biến thể (`PARAPHRASE_CASES`)               | 15     | Cùng ý nhưng cách diễn đạt khác — chống "học thuộc"        |
| Câu hội thoại nhiều lượt (`DIALOGUE_EVAL_CASES`) | 8      | Chứng minh ngữ cảnh hội thoại thực sự được dùng          |

Phân loại theo bản chất:

| Nhóm                                                  | Số câu |
| ---------------------------------------------------- | ------ |
| Câu hỏi hợp lệ trong miền                            | 38     |
| Câu hỏi ngoài phạm vi                                 | 5      |
| Câu hỏi phụ thuộc ngữ cảnh                            | 11     |
| Câu hỏi trong phạm vi nhưng KB không có dữ liệu      | 3      |

Ngoài ra còn có **5 kịch bản hội thoại** đầy đủ trong `tests/data/dialogues.txt`.

### 12.2 Công cụ đánh giá

```bash
# Chạy bộ test đầy đủ (158 test)
python -m pytest

# Báo cáo đánh giá đầy đủ (6 mục, ghi ra output/evaluation.txt)
python -m src.evaluation

# Đo các chỉ số
python scripts/baseline.py --out docs/baseline.txt
```

`src/evaluation.py` đo 6 nhóm chỉ số:

1. **Số lượng câu kiểm thử** — theo nguồn và theo nhóm
2. **Số lượng câu trả lời đúng** — intent / entity / intent+entity / câu trả lời / ngoài phạm vi
3. **Độ chính xác theo từng intent** — bảng phân bố
4. **Các trường hợp hệ thống trả lời sai** — liệt kê từng câu
5. **Phân tích nguyên nhân lỗi** — theo loại lỗi và theo nhóm test
6. **Nhận xét ưu điểm và hạn chế**

So sánh entity là **alias-aware** (`ENTITY_ALIASES`): nhãn chính thức `MIDTERM`
được chấp nhận khi pipeline trích ra `midterm_duration`, nhãn `CO3085` được
chấp nhận khi pipeline trích ra `NLP`.

`scripts/baseline.py` đo 5 nhóm chỉ số:

1. **Intent accuracy** — tỉ lệ intent đúng trên tập chính thức
2. **Entity accuracy** — đo cả bản alias-aware lẫn khớp thô
3. **Intent + Entity accuracy** — độ chính xác tổng thể của pipeline
4. **Chất lượng parse** — tỉ lệ strict / fallback / failure
5. **Chất lượng sinh câu** — số câu chứa `_`, rò non-terminal, sai dấu câu

### 12.3 Kết quả hiện tại

**Trên 57 câu kiểm thử (34 chính thức + 15 biến thể + 8 hội thoại):**

| Chỉ số                        | Kết quả               |
| ----------------------------- | --------------------- |
| Intent accuracy               | 57/57 — **100.00 %**  |
| Entity accuracy (alias-aware) | 57/57 — **100.00 %**  |
| **Intent + Entity accuracy**  | 57/57 — **100.00 %**  |
| Câu trả lời đúng              | 57/57 — **100.00 %**  |
| Phát hiện ngoài phạm vi       | **100.00 %**          |

**Trên 34 câu hỏi chính thức:**

| Chỉ số                        | Kết quả               |
| ----------------------------- | --------------------- |
| Intent accuracy               | 34/34 — **100.00 %**  |
| Entity accuracy (alias-aware) | 34/34 — **100.00 %**  |
| Entity accuracy (khớp thô)    | 32/34 — 94.12 %       |
| **Intent + Entity accuracy**  | 34/34 — **100.00 %**  |
| Strict parse (Earley chart)   | 31/34 — **91.18 %**   |
| Pattern fallback parse        | 3/34 — 8.82 %         |
| Parse failure                 | 0/34 — 0 %            |
| Bộ test                       | **158 passed — 0 failed, 0 xfailed** |

**Chất lượng bộ sinh câu (10 000 câu):** 0 câu chứa `_`, 0 câu rò non-terminal,
0 câu mở sai, 0 câu thiếu dấu câu.

> **Cách đọc đúng các con số này:** 100 % là độ chính xác trên **bộ 57 câu
> kiểm thử** của đề bài và nhóm tự bổ sung — **không** phải độ phủ trên tiếng
> Việt nói chung. 15 câu biến thể được cố ý thêm vào để phát hiện trường hợp
> hệ thống chỉ nhớ đúng câu chữ của đề bài. Ba câu parse fallback là ba câu
> **ngoài phạm vi** cố ý — trên 31 câu in-scope, strict parse đạt **100 %**.

### 12.4 Quản lý lỗi tồn đọng

Mọi lỗi chưa sửa được liệt kê tập trung trong `tests/known_issues.py`, mỗi lỗi
ghi rõ nguyên nhân và phần hệ thống liên quan. Các test này được đánh dấu
`xfail` (non-strict) nên quality gate luôn xanh, nhưng lỗi vẫn hiện rõ mỗi lần
chạy và không thể bị "quên".

> **Trạng thái hiện tại:** sổ đăng ký đã được **dọn sạch** — toàn bộ 21 mục
> đã xử lý xong và được chuyển thành regression test thật (không còn
> `xfail`/`XPASS`). File `tests/known_issues.py` vẫn được giữ lại như một
> "hàng rào" cho các đợt nâng cấp sau: khi có lỗi mới, chỉ cần thêm entry
> vào đây là test sẽ tự động được đánh dấu `xfail`.

---

## 13. Hạn chế của hệ thống

1. **Lexicon là bảng tra thủ công.** Một cách diễn đạt mới sẽ không được nhận
   diện; mở rộng miền tri thức đòi hỏi thêm surface form thủ công.
2. **Tham chiếu ngữ cảnh theo bộ quy tắc cố định.** Hệ thống xử lý được 4 loại
   tham chiếu (đại từ, mô tả xác định, cấu trúc rút gọn, quan hệ kế tiếp) nhưng
   chưa xử lý được tham chiếu mơ hồ khi có nhiều ứng viên.
3. **Knowledge base chỉ trả lời truy vấn đơn.** Chưa suy luận nhiều bước (ví dụ
   so sánh, tổng hợp, hoặc kết hợp thông tin từ nhiều nguồn trong một câu hỏi).
4. **Độ phủ đo được trên tập kiểm thử, không phải trên tiếng Việt nói chung.**
   100 % là kết quả trên 57 câu của đề bài và nhóm tự bổ sung; chưa có tập dữ
   liệu lớn hơn để đo độ tổng quát.
5. **Không có phân tích ngữ nghĩa (Word Sense Disambiguation) độc lập.**
   Việc chọn nghĩa của từ đa nghĩa được giải quyết bằng lexicon theo nhóm ưu
   tiên, chưa phải bằng thuật toán WSD chuyên dụng.
6. **Chưa mở rộng LLM/RAG.** Đây là phần mở rộng không bắt buộc của đề bài; hệ
   thống hiện hoàn toàn rule-based theo Lựa chọn 1.

---

## 14. Ghi chú về tính trung thực học thuật

Hệ thống được xây dựng bằng phương pháp **Classical/Statistical NLP dựa trên
luật** — không sử dụng LLM hay API bên ngoài ở bất kỳ thành phần nào. Toàn bộ
mã nguồn dùng thư viện chuẩn của Python.

Mọi chỉ số trong tài liệu này đều **tự động sinh bằng script**
(`scripts/baseline.py`, `scripts/check_submission.py`) chứ không ước lượng tay, và
mọi hạn chế đều có test tương ứng trong bộ test.

---

*Course Assistant — Bài tập lớn CO3085 — Kỳ học HK261*
