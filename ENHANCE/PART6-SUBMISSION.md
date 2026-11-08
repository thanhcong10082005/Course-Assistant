# PART 6 — Đóng gói và nộp bài (Submission)

## 1. Mục tiêu

Sau bước này, repo phải ở trạng thái **nộp được**, không còn là “sample tham
khảo”:

1. `README.md` mô tả đúng code hiện tại, có **danh sách thành viên**, có lệnh
   chạy đúng, có số liệu đánh giá lấy từ file thật.
2. `docs/REPORT.md` khớp với code: không còn module hư cấu, không còn bước NLTK
   không tồn tại, không còn lệnh `python src/main.py --part 1`.
3. Có **video demo** 5–7 phút, quay đúng luồng: parse → semantic → KB → dialogue
   → evaluation → Docker.
4. Repo sạch: không có `__pycache__`, `.pyc`, file tạm, dữ liệu cá nhân.
5. Docker build được và chạy được **cả** `--mode demo` **và** `--mode generate`.
6. File zip nộp bài có cấu trúc rõ ràng, mở ra chạy được ngay.
7. Có checklist cuối cùng để không quên mục nào.

## 2. Phạm vi file

| File | Việc cần làm |
|---|---|
| `README.md` | Viết lại theo template, thêm thành viên, sửa số liệu/lệnh |
| `docs/REPORT.md` | Sửa section 4–6, bỏ module hư cấu, cập nhật số liệu |
| `Dockerfile` | Sửa base image, encoding, entrypoint, bỏ dependency thừa |
| `.dockerignore` (mới) | Giảm context, tránh copy rác |
| `.gitignore` (mới) | Chặn `__pycache__`, `.pyc`, venv, cache |
| `.gitattributes` (khuyến nghị) | Ổn định line ending |
| `requirements.txt` | Chỉ giữ dependency thật dùng |
| `requirements-dev.txt` (mới) | `pytest` cho dev |
| `src/__pycache__/` | Xóa khỏi git và ổ đĩa |
| `output/` | Sinh lại toàn bộ, không chỉnh tay |
| `demo.mp4` / link video | Video demo |
| `docs/SUBMISSION-CHECKLIST.md` (khuyến nghị) | Checklist trước khi nộp |

## 3. Hiện trạng và vấn đề

### 3.1 README

`README.md` hiện tại:

- Tiêu đề: **“Course Assistant - NLP Assignment Sample”** → vẫn là sample, không
  phải bài nộp.
- **Không có danh sách thành viên**, không có phân công, không có MSSV.
- Ghi “10,000+ sentences” nhưng thực tế `output/samples.txt` có **10.069 câu**
  (vượt yêu cầu ≤ 10.000) và 6.508 câu chứa `_`.
- Ghi “Test set with 20+ queries” nhưng thực tế 20 case, chưa có no-info/context.
- Ghi “Intent Accuracy 100%, Entity Accuracy 100%, Out-of-Scope 100%” nhưng đây
  là số liệu của harness lỗi (xem Part 5), không phải chất lượng thật.
- Bảng ví dụ Q&A có câu trả lời **sai** so với code:
  - `Chương 4 học vào tuần nào?` → “Week 04” (tiếng Anh).
  - `PCFG được học ở đâu?` → trả về CFG/Chương 03.
  - `Hôm nay thời tiết thế nào?` → “Xin lỗi, tôi không hiểu câu hỏi này.” trong
    khi code trả lời khác.
- Cấu trúc project ghi `Course_Assistant_Sample/`, không khớp tên repo.
- Docker chỉ ghi `docker run -it course-assistant`, không nói rõ mode.
- Không có mục “Sử dụng AI” (nếu nhóm có dùng).
- Không có mục “Hạn chế”.

### 3.2 REPORT

`docs/REPORT.md` (727 dòng) có nội dung tốt nhưng **không khớp code**:

| Vị trí | Nội dung hiện tại | Thực tế |
|---|---|---|
| Mục 4 — Thiết kế | Module `intent.py`, `entity.py`, `query.py`, `answer.py` | Không tồn tại; code nằm trong `semantic.py`, `knowledge_base.py`, `main.py` |
| Mục 5 — Cài đặt | Các bước NLTK (tokenize, POS tag, chunk) | Code chỉ dùng stdlib; tokenizer tự viết |
| Mục 5 — Lệnh chạy | `python src/main.py --part 1` | Đúng phải là `python -m src.main --mode demo` |
| Mục 6 — Đánh giá | Số liệu/sample output không lấy từ `output/` | Cần lấy từ `output/evaluation.json` |
| Mục 3 — Kế hoạch | Timeline không có ngày thật | Cần cập nhật |
| Mục 1 — Giới thiệu | Không có thành viên | Cần bổ sung |

Nếu giảng viên đọc REPORT rồi chạy thử, sẽ thấy mô tả và code lệch nhau. Đây là
lỗi nghiêm trọng hơn một câu trả lời sai.

### 3.3 Repo hygiene

- `src/__pycache__/` có **9 file `.pyc` được track** (cpython-314) và 9 file
  untracked (cpython-312).
- **Không có `.gitignore`**, không có `.dockerignore`.
- `NLPAssignment-Course Assistant.pdf` nằm ở root, không phải file nộp.
- `ENHANCE/` là tài liệu nội bộ, không nên có trong zip nộp.
- `requirements.txt` liệt kê `nltk`, `pandas`, `numpy`, `regex`, `pytest` nhưng
  `src/*.py` chỉ import stdlib (`re`, `os`, `sys`, `json`, `random`,
  `unicodedata`, `dataclasses`, `enum`, `typing`).
- `Dockerfile` tải NLTK data (`punkt`, `averaged_perceptron_tagger`) dù code
  không dùng NLTK → build chậm, dễ fail nếu không có mạng.
- `Dockerfile` dùng `python:3.9-slim`; nếu Part 3/4 dùng cú pháp `str | None`
  (Python 3.10+) sẽ crash.

### 3.4 Docker

`Dockerfile` hiện tại:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
COPY src/ ./src/
COPY data/ ./data/
COPY input/ ./input/
COPY output/ ./output/
ENV PYTHONPATH=/app
CMD ["python", "-m", "src.main", "--mode", "demo"]
```

Vấn đề:

| # | Vấn đề | Hệ quả |
|---|---|---|
| D1 | Cài `nltk`, `pandas`, `numpy` không dùng | Image nặng, build lâu |
| D2 | Download NLTK data | Build fail nếu không có mạng; không cần |
| D3 | `python:3.9-slim` | Không chạy được cú pháp 3.10+ nếu Part 3/4 dùng |
| D4 | Không set `PYTHONIOENCODING` / `LANG` | Có thể `UnicodeEncodeError` với tiếng Việt |
| D5 | `CMD` cố định `demo` | Không chạy `--mode generate` nếu không override toàn bộ |
| D6 | Copy `output/` từ host | Output cũ có thể lẫn vào image; generate ghi đè không rõ |
| D7 | Không có `.dockerignore` | Copy `.git`, `__pycache__`, PDF, ENHANCE vào build context |
| D8 | Chạy bằng root | Không tối ưu bảo mật (không bắt buộc với bài tập) |
| D9 | `apt-get install git` | Không cần |
| D10 | Không tạo `output/` nếu thiếu | `--mode generate` có thể lỗi |

Ngoài ra, `main.py` có bug đường dẫn:

```python
parser.add_argument('--output', default='../output', ...)
...
output_dir = os.path.join(os.path.dirname(__file__), args.output)
```

- Mặc định chạy từ `src/` → `src/../output` = `output/` (đúng).
- Nếu người dùng truyền `--output output` → `src/output` (sai).
- Nếu chạy từ thư mục khác → vẫn phụ thuộc `__file__`, nhưng `../output` dễ gây
  nhầm.

Cần đổi default thành `output` và resolve theo project root.

### 3.5 Encoding trên Windows

`python -m src.main --mode demo` crash với `UnicodeEncodeError` trên console
cp1252. Nguyên nhân: `print()` tiếng Việt khi stdout không phải UTF-8.

Cách xử lý (làm cả ba):

1. Trong `main()`:

```python
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
```

2. README ghi rõ:

```powershell
$env:PYTHONIOENCODING = "utf-8"
python -m src.main --mode demo
```

3. Dockerfile set `ENV PYTHONIOENCODING=utf-8` và `ENV LANG=C.UTF-8`.

## 4. README — template bài nộp

Thay toàn bộ `README.md` bằng cấu trúc sau. Các chỗ `<...>` là placeholder phải
điền.

```markdown
# Course Assistant — Trợ lý hỗ trợ học tập môn Xử lý Ngôn ngữ Tự nhiên (CO3085)

**Môn học:** Xử lý Ngôn ngữ Tự nhiên — CO3085 — HK261
**Bài tập lớn:** Intelligent Course Assistant
**Nhóm:** <Tên nhóm>
**Repo:** <link GitHub nếu có>

---

## 1. Thành viên nhóm

| STT | Họ và tên | MSSV | Vai trò | Phân công chính | Đóng góp |
|---:|---|---|---|---|---:|
| 1 | <Họ tên> | <MSSV> | Nhóm trưởng | Grammar, parser, tích hợp | 25% |
| 2 | <Họ tên> | <MSSV> | Thành viên | Semantic, knowledge base | 25% |
| 3 | <Họ tên> | <MSSV> | Thành viên | Dialogue, evaluation | 25% |
| 4 | <Họ tên> | <MSSV> | Thành viên | Data, báo cáo, Docker, demo | 25% |

> Ghi rõ ai làm phần nào để giảng viên đối chiếu khi hỏi code.

## 2. Giới thiệu

Hệ thống trả lời câu hỏi tiếng Việt về môn CO3085: thông tin môn học, lịch 15
tuần, nội dung 12 chương, bài tập lớn, deadline, tài liệu, quy định và learning
outcome. Hệ thống là pipeline NLP rule-based:

```
Câu hỏi
  → Tiền xử lý (chuẩn hóa, tokenize, detokenize)
  → Parser CFG (recursive descent + fallback có kiểm soát)
  → Phân tích ngữ nghĩa (intent + entity + logical form)
  → Resolve tham chiếu hội thoại (DialogueManager)
  → Truy vấn knowledge base (load từ data/)
  → Sinh câu trả lời (có status + evidence)
```

## 3. Tính năng

- Phân tích cú pháp bằng CFG, xuất parse tree.
- Sinh câu hợp lệ từ grammar (≤ 10.000 câu, không có câu vô nghĩa).
- Nhận diện 9 intent + `UNKNOWN`.
- Trích xuất entity: course, chapter, week, topic, assignment, part, LO, rule,
  attribute.
- Trả lời theo dữ liệu môn học, có phân biệt:
  - `OK`
  - `NOT_FOUND`
  - `INVALID_VALUE`
  - `OUT_OF_SCOPE`
  - `NEEDS_CLARIFICATION`
- Hội thoại nhiều lượt: resolve `nó`, `phần này`, `chương này`, `nội dung này`,
  `chương sau`.
- Đánh giá bằng test set 100 case, chấm intent/entity/status/answer/context.

## 4. Cấu trúc thư mục

```text
Course-Assistant/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI, demo, generate, interactive
│   ├── preprocessing.py     # Chuẩn hóa, tokenize, detokenize
│   ├── grammar.py           # CFG + template + generator
│   ├── parser.py            # Recursive descent + fallback
│   ├── semantic.py          # Intent, entity, logical form
│   ├── knowledge_base.py    # Query layer + answer
│   ├── data_loader.py       # Load data/*.txt (Part 3)
│   ├── dialogue.py          # DialogueManager
│   ├── evaluation.py        # Runner + metrics
│   └── generator.py         # Sinh samples (Part 2)
├── data/
│   ├── course_info.txt
│   ├── schedule.txt
│   ├── topics.txt
│   ├── assignments.txt
│   ├── resources.txt
│   ├── regulations.txt
│   ├── faq.txt
│   ├── entities.txt
│   ├── dialogues.txt
│   ├── sample_queries.txt
│   ├── test_cases.jsonl
│   └── README.md
├── input/
│   └── sentences.txt
├── output/                  # Sinh bằng --mode generate
├── docs/
│   └── REPORT.md
├── tests/
│   ├── test_parser.py
│   ├── test_generator.py
│   ├── test_data_loader.py
│   ├── test_knowledge_base.py
│   ├── test_dialogue.py
│   └── test_evaluation.py
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## 5. Yêu cầu

- Python 3.10+ (khuyến nghị 3.11/3.12)
- Docker (tùy chọn)
- Không cần NLTK hay thư viện NLP ngoài

## 6. Cài đặt

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt   # nếu chạy test
```

## 7. Cách chạy

### 7.1 Demo pipeline

```bash
python -m src.main --mode demo
```

Hiển thị: parse tree, semantic form, intent/entity, answer, dialogue mẫu.

### 7.2 Interactive

```bash
python -m src.main --mode interactive
```

Gõ câu hỏi tiếng Việt; gõ `exit` để thoát.

### 7.3 Sinh toàn bộ output

```bash
python -m src.main --mode generate
```

Sinh 9 file trong `output/`:

| File | Nội dung |
|---|---|
| `grammar.txt` | CFG đầy đủ |
| `samples.txt` | Câu sinh từ grammar (≤ 10.000) |
| `samples.meta.jsonl` | Metadata từng câu |
| `parse-results.txt` | Parse tree cho `input/sentences.txt` |
| `semantic.txt` | Intent, entity, logical form |
| `intent-entity.txt` | Intent + entity |
| `query.txt` | Query có cấu trúc |
| `answer.txt` | Câu trả lời |
| `dialogue.txt` | Hội thoại nhiều lượt |
| `evaluation.txt` | Báo cáo đánh giá |
| `evaluation.json` | Số liệu máy đọc |

### 7.4 Chạy evaluation

```bash
python -m src.evaluation --cases data/test_cases.jsonl --out output/evaluation.txt --json output/evaluation.json
```

### 7.5 Chạy test

```bash
pytest -q
```

### 7.6 Docker

```bash
docker build -t course-assistant .

# Demo
docker run --rm course-assistant --mode demo

# Generate, mount output ra host
docker run --rm -v "$(pwd)/output:/app/output" course-assistant --mode generate

# Interactive
docker run --rm -it course-assistant --mode interactive
```

Windows PowerShell:

```powershell
docker run --rm -v "${PWD}/output:/app/output" course-assistant --mode generate
```

## 8. Intents và status

| Intent | Ví dụ |
|---|---|
| `GET_COURSE_INFO` | Môn NLP có bao nhiêu tín chỉ? |
| `GET_SCHEDULE` | Tuần 3 học gì? |
| `GET_TOPIC` | Chương nào học về CFG? |
| `GET_ASSIGNMENT` | Phần I của BTL là gì? |
| `GET_DEADLINE` | Deadline BTL là khi nào? |
| `GET_RESOURCE` | Tài liệu về PCFG ở đâu? |
| `GET_RULE` | Có được dùng LLM/RAG không? |
| `GET_LO` | L.O.2.5 là gì? |
| `GET_INSTRUCTOR` | Ai dạy môn NLP? |
| `UNKNOWN` | Hôm nay thời tiết thế nào? |

| Status | Nghĩa |
|---|---|
| `OK` | Trả lời được |
| `NOT_FOUND` | Trong miền nhưng không có dữ liệu |
| `INVALID_VALUE` | Giá trị ngoài range (tuần 30, chương 15) |
| `OUT_OF_SCOPE` | Ngoài miền môn học |
| `NEEDS_CLARIFICATION` | Thiếu ngữ cảnh |

## 9. Ví dụ

| Câu hỏi | Trả lời |
|---|---|
| Môn NLP có bao nhiêu tín chỉ? | Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ. |
| Tuần 3 học gì? | Tuần 03 — Chương 03: Grammar and Parsing; gồm CFG, parsing, PCFG, dependency grammar. |
| PCFG được học ở đâu? | PCFG được trình bày ở Chương 3 và tiếp tục ở Chương 6. |
| Phần IV của BTL là gì? | Phần IV — Evaluation: test set, metric, phân tích lỗi. |
| BTL cần xuất những file gì? | Phần I: grammar.txt, samples.txt, parse-results.txt; Phần II: semantic.txt, intent-entity.txt, query.txt, answer.txt; Phần IV: evaluation.txt. |
| Tuần 30 học gì? | Tuần 30 không nằm trong lịch 15 tuần của môn học. |
| Ai dạy môn NLP? | Dữ liệu môn học hiện không có thông tin giảng viên. |
| Hôm nay thời tiết thế nào? | Câu hỏi này nằm ngoài phạm vi môn học CO3085. |

> Các câu trả lời trên phải khớp **thực tế** sau khi sửa Part 1–5. Không chép
> trước khi chạy thử.

## 10. Đánh giá

Số liệu lấy từ `output/evaluation.json` (test set 100 case):

| Metric | Giá trị |
|---|---:|
| Pass Rate | <%> |
| Intent Accuracy | <%> |
| Entity F1 | <F1> |
| Status Accuracy | <%> |
| Answer Accuracy | <%> |
| Context Resolution | <%> |
| OOS Precision / Recall | <%> / <%> |

Xem chi tiết trong `output/evaluation.txt` và `docs/REPORT.md`.

## 11. Hạn chế

- Rule-based, không học từ dữ liệu; phụ thuộc grammar và alias.
- Chưa xử lý câu phức, nhiều ý trong một câu.
- Chưa có thông tin giảng viên.
- Dữ liệu lịch/deadline là dữ liệu mẫu, không phải thông tin hành chính chính thức.
- Chưa hỗ trợ tiếng Anh.

## 12. Sử dụng AI

<Chỉ giữ mục này nếu nhóm có dùng AI. Ghi rõ: công cụ, mục đích, phần nào, cách
kiểm chứng. Nếu không dùng, ghi “Nhóm không sử dụng AI/LLM trong code và báo
cáo.”>

## 13. Tài liệu tham khảo

1. Jurafsky & Martin — *Speech and Language Processing*.
2. Manning & Schütze — *Foundations of Statistical NLP*.
3. Bird, Klein, Loper — *Natural Language Processing with Python*.
4. Eisenstein — *Introduction to Natural Language Processing*.
5. Slide bài giảng CO3085.

## 14. License

MIT License — bài tập lớn CO3085.
```

### 4.1 Quy tắc viết README

1. **Không tuyên bố số liệu chưa đo.** Mọi con số phải lấy từ
   `output/evaluation.json`.
2. **Không mô tả module không tồn tại.** Đối chiếu `src/`.
3. **Mọi lệnh trong README phải chạy được** từ thư mục gốc repo.
4. **Mọi ví dụ Q&A phải được chạy thử** và copy nguyên văn output.
5. **Có thành viên + phân công**, vì yêu cầu bài tập là làm nhóm.
6. **Ghi rõ dữ liệu mẫu** để không bị coi là thông tin chính thức.

## 5. REPORT — checklist căn chỉnh

### 5.1 Nguyên tắc

`docs/REPORT.md` phải là **mô tả của code hiện tại**, không phải mô tả của một
hệ thống lý tưởng. Cách kiểm tra: mở từng mục, tìm file/hàm tương ứng trong
`src/`. Nếu không tìm thấy → sửa REPORT hoặc sửa code, không để lệch.

### 5.2 Checklist từng mục

| Mục | Kiểm tra | Hành động |
|---|---|---|
| 1. Giới thiệu | Có thành viên, mục tiêu, phạm vi | Bổ sung bảng thành viên |
| 2. Phân tích yêu cầu | Map đúng Part I–IV của PDF | Đối chiếu PDF, sửa tên phần |
| 3. Kế hoạch | Timeline thật, phân công thật | Cập nhật ngày/tuần |
| 4. Thiết kế | Chỉ dùng module có thật | Xóa `intent.py`, `entity.py`, `query.py`, `answer.py`; thay bằng `preprocessing.py`, `grammar.py`, `parser.py`, `semantic.py`, `knowledge_base.py`, `dialogue.py`, `evaluation.py` |
| 4. Kiến trúc | Sơ đồ khớp pipeline thật | Vẽ lại: Preprocess → Parse → Semantic → Dialogue → KB → Answer |
| 5. Cài đặt | Không còn NLTK nếu không dùng | Xóa bước NLTK; mô tả tokenizer/CFG/parser tự viết |
| 5. Lệnh chạy | Đúng entrypoint | `python -m src.main --mode ...`, không `python src/main.py --part 1` |
| 5. Output | Đúng 9+ file thật | Liệt kê từ `output/` |
| 6. Đánh giá | Số liệu từ `evaluation.json` | Chép số thật, kèm ngày chạy |
| 6. Error analysis | Có lỗi thật + root cause | Lấy từ Part 5 |
| 7. Kết luận | Khớp kết quả | Sửa “hệ thống hoàn chỉnh” nếu còn hạn chế |
| Phụ lục | Grammar, test set, sample output | Thêm nếu thiếu |

### 5.3 Những câu/từ cần xóa hoặc sửa

Tìm trong `docs/REPORT.md` và xử lý:

| Tìm | Sửa thành |
|---|---|
| `intent.py` | `semantic.py` (IntentType + SemanticAnalyzer) |
| `entity.py` | `semantic.py` (Entity + extraction) |
| `query.py` | `knowledge_base.py` (`KnowledgeBase.query`) |
| `answer.py` | `knowledge_base.py` (answer generation) |
| `NLTK` / `nltk` | “tokenizer tự viết bằng regex/unicodedata” (nếu đúng) |
| `python src/main.py --part 1` | `python -m src.main --mode demo` |
| `10,000+ sentences` | “≤ 10.000 câu hợp lệ” (sau Part 2) |
| `100%` không nguồn | Số liệu từ `output/evaluation.json` |
| `Week 04` | `Tuần 04` |
| `sample` | “bài nộp” (nếu không còn là sample) |

### 5.4 Cấu trúc REPORT đề xuất

```text
1. Giới thiệu
   1.1 Thành viên và phân công
   1.2 Bối cảnh
   1.3 Mục tiêu
2. Phân tích yêu cầu
   2.1 Part I — Grammar and Parser
   2.2 Part II — Semantic Interpretation and QA
   2.3 Part III — Local Discourse Context
   2.4 Part IV — Evaluation
3. Thiết kế hệ thống
   3.1 Kiến trúc pipeline
   3.2 Preprocessing
   3.3 Grammar và Parser
   3.4 Semantic representation
   3.5 Knowledge base
   3.6 Dialogue
   3.7 Evaluation
4. Cài đặt
   4.1 Môi trường
   4.2 Cấu trúc code
   4.3 Luồng xử lý một câu hỏi
   4.4 Sinh output
5. Dữ liệu
   5.1 Nguồn dữ liệu
   5.2 Schema
   5.3 Loader và validation
6. Đánh giá
   6.1 Test set
   6.2 Metrics
   6.3 Kết quả
   6.4 Phân tích lỗi
   6.5 Hạn chế
7. Kết luận và hướng phát triển
8. Tài liệu tham khảo
9. Phụ lục
   A. Grammar
   B. Danh sách intent/entity
   C. Sample output
   D. Phân công chi tiết
```

## 6. Video demo

### 6.1 Yêu cầu

- Thời lượng: **5–7 phút**.
- Độ phân giải: 1080p, chữ terminal đủ lớn (font ≥ 16).
- Có tiếng nói hoặc phụ đề.
- Quay trên máy sạch, không lộ thông tin cá nhân (email, tài khoản, đường dẫn
  chứa tên).
- Terminal dùng UTF-8 để hiển thị tiếng Việt đúng.
- Không cắt ghép quá nhiều; ưu tiên quay liên tục.

### 6.2 Storyboard

| Thời gian | Nội dung | Việc làm trên màn hình |
|---|---|---|
| 0:00–0:30 | Giới thiệu | Mở README, giới thiệu nhóm, môn, mục tiêu |
| 0:30–1:30 | Kiến trúc | Mở sơ đồ pipeline; chỉ vào `src/` |
| 1:30–2:30 | Parse | Chạy `--mode demo`, chỉ parse tree câu đúng; chạy câu sai `asdf qwerty zzz` → `()` |
| 2:30–3:30 | Semantic + KB | Hỏi `Môn NLP có bao nhiêu tín chỉ?`, `PCFG được học ở đâu?`, `Phần IV của BTL là gì?` |
| 3:30–4:30 | No-info | Hỏi `Tuần 30 học gì?`, `Ai dạy môn NLP?`, `Hôm nay thời tiết thế nào?`; chỉ status khác nhau |
| 4:30–5:30 | Dialogue | Chạy 3 kịch bản: `Tuần 3` → `Tài liệu của chương này`; `Chương 4` → `Nó có liên quan đến parsing không?`; `BTL phần parser` → `Phần này cần xuất file gì?` |
| 5:30–6:15 | Evaluation | Chạy `python -m src.evaluation ...`; mở `output/evaluation.txt`, chỉ pass rate/error analysis |
| 6:15–6:45 | Docker | `docker build`, `docker run --mode demo`, `--mode generate` |
| 6:45–7:00 | Kết luận | Tóm tắt kết quả, hạn chế, hướng phát triển |

### 6.3 Lệnh cần quay

```powershell
# 1. Demo
python -m src.main --mode demo

# 2. Interactive (gõ lần lượt)
python -m src.main --mode interactive
# Môn NLP có bao nhiêu tín chỉ?
# PCFG được học ở đâu?
# Tuần 30 học gì?
# exit

# 3. Generate
python -m src.main --mode generate

# 4. Evaluation
python -m src.evaluation --cases data/test_cases.jsonl --out output/evaluation.txt --json output/evaluation.json

# 5. Docker
docker build -t course-assistant .
docker run --rm course-assistant --mode demo
docker run --rm -v "${PWD}/output:/app/output" course-assistant --mode generate
```

### 6.4 Lưu ý khi quay

- Chạy `--mode demo` trước để chắc không lỗi encoding.
- Mở sẵn `output/evaluation.txt` ở tab bên cạnh.
- Không quay màn hình có thông báo riêng tư.
- Nếu video nặng, đưa lên YouTube/Drive **unlisted** và ghi link trong README;
  không commit file `.mp4` lớn vào git.

## 7. Repo hygiene

### 7.1 Xóa `__pycache__`

```bash
git rm -r --cached src/__pycache__
rm -rf src/__pycache__
```

Windows PowerShell:

```powershell
git rm -r --cached src/__pycache__
Remove-Item -Recurse -Force src/__pycache__
```

Kiểm tra:

```bash
git ls-files | grep -E "__pycache__|\.pyc$"
```

Kỳ vọng: không còn dòng nào.

### 7.2 `.gitignore`

Tạo file `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
build/
dist/
*.egg-info/
.eggs/

# Virtual env
.venv/
venv/
env/
ENV/

# Test / cache
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# IDE / OS
.idea/
.vscode/
*.swp
.DS_Store
Thumbs.db

# Project
data/.cache/
output/*.tmp
*.log
*.zip
demo.mp4
```

### 7.3 `.dockerignore`

Tạo file `.dockerignore`:

```dockerignore
.git
.gitignore
.gitattributes
__pycache__
**/__pycache__
*.py[cod]
.venv
venv
env
.pytest_cache
.mypy_cache
.ruff_cache
.coverage
htmlcov
.idea
.vscode
ENHANCE
docs
*.pdf
*.mp4
*.zip
README.md
```

Lưu ý: nếu Dockerfile cần `README.md` để copy thì bỏ dòng đó. Với Dockerfile
mới chỉ copy `src/`, `data/`, `input/`, không cần README.

### 7.4 `.gitattributes` (khuyến nghị)

```gitattributes
* text=auto
*.py text eol=lf
*.txt text eol=lf
*.md text eol=lf
*.json text eol=lf
*.jsonl text eol=lf
*.sh text eol=lf
Dockerfile text eol=lf
```

Mục đích: tránh diff toàn file do CRLF/LF khi làm việc nhóm.

### 7.5 Kiểm tra encoding

Tất cả file `.py`, `.txt`, `.md`, `.jsonl` phải là UTF-8 (không BOM):

```powershell
$env:PYTHONIOENCODING = "utf-8"
python - <<'PY'
from pathlib import Path
for p in Path(".").rglob("*"):
    if p.suffix in {".py", ".txt", ".md", ".json", ".jsonl"} and p.is_file():
        raw = p.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            print("BOM:", p)
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as e:
            print("NOT UTF-8:", p, e)
PY
```

Kỳ vọng: không in gì.

### 7.6 Dọn file không nộp

| File | Hành động |
|---|---|
| `NLPAssignment-Course Assistant.pdf` | Chuyển vào `docs/` hoặc loại khỏi zip |
| `ENHANCE/` | Loại khỏi zip (tài liệu nội bộ) |
| `src/__pycache__/` | Xóa |
| `.venv/`, `venv/` | Không commit |
| `demo.mp4` | Không commit; dùng link |
| `output/*.tmp` | Xóa |
| File `.log`, `.bak` | Xóa |

## 8. Docker — sửa và kiểm chứng

### 8.1 Dockerfile mới

```dockerfile
# Course Assistant — CO3085
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONPATH=/app

WORKDIR /app

# Chỉ copy thứ cần thiết
COPY src/ ./src/
COPY data/ ./data/
COPY input/ ./input/

# Tạo thư mục output và user không phải root
RUN mkdir -p /app/output \
    && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--mode", "demo"]
```

Nếu vẫn cần dependency runtime:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

Nhưng hiện tại code chỉ dùng stdlib → **không cần** `pip install`, không cần
NLTK download. Điều này làm image nhỏ hơn nhiều và build không phụ thuộc mạng.

### 8.2 Vì sao dùng `ENTRYPOINT` + `CMD`

- `docker run course-assistant` → chạy `--mode demo`.
- `docker run course-assistant --mode generate` → thay `CMD`, vẫn qua
  `ENTRYPOINT`.
- Không phải gõ lại `python -m src.main`.

### 8.3 Sửa `--output`

Trong `src/main.py`:

```python
from pathlib import Path

parser.add_argument(
    '--output',
    default='output',
    help='Output directory (relative to project root)',
)
...
base_dir = Path(__file__).resolve().parent.parent
output_dir = Path(args.output)
if not output_dir.is_absolute():
    output_dir = base_dir / output_dir
save_outputs(str(output_dir))
```

Kỳ vọng:

| Lệnh | Thư mục ghi |
|---|---|
| `python -m src.main --mode generate` | `<repo>/output` |
| `python -m src.main --mode generate --output output` | `<repo>/output` |
| `python -m src.main --mode generate --output /tmp/out` | `/tmp/out` |
| Trong Docker `--mode generate` | `/app/output` |

### 8.4 Kiểm chứng Docker

> **Trạng thái tại thời điểm lập kế hoạch:** `docker --version` trả về
> `29.5.3`, nhưng Docker daemon chưa chạy
> (`failed to connect to ... dockerDesktopLinuxEngine`). Vì vậy các lệnh dưới
> đây **chưa được chạy thực tế** trong lần audit này. Trước khi nộp, bật Docker
> Desktop và chạy lại toàn bộ mục 8.4, ghi kết quả vào
> `docs/SUBMISSION-CHECKLIST.md`.

Chạy tuần tự và ghi log:

```bash
# 1. Build
docker build -t course-assistant:latest .

# 2. Kiểm tra image
docker images course-assistant:latest

# 3. Demo
docker run --rm course-assistant:latest --mode demo

# 4. Generate (không mount) — kiểm tra file trong container
docker run --rm course-assistant:latest --mode generate
docker run --rm course-assistant:latest sh -c "ls -la /app/output && wc -l /app/output/samples.txt"

# 5. Generate (mount ra host)
docker run --rm -v "${PWD}/output:/app/output" course-assistant:latest --mode generate

# 6. Interactive (chỉ khi có TTY)
docker run --rm -it course-assistant:latest --mode interactive

# 7. Kiểm tra encoding
docker run --rm course-assistant:latest python -c "import sys; print(sys.stdout.encoding)"
```

Kỳ vọng:

| Bước | Kỳ vọng |
|---|---|
| Build | Thành công, không cần mạng sau khi có base image |
| Demo | In tiếng Việt đúng, không `UnicodeEncodeError` |
| Generate | `output/` có 9+ file; `samples.txt` ≤ 10.000 dòng câu |
| Mount | File xuất hiện trên host |
| Encoding | `utf-8` |

### 8.5 Lỗi Docker thường gặp

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| `UnicodeEncodeError` | Thiếu `PYTHONIOENCODING` | Thêm `ENV PYTHONIOENCODING=utf-8` |
| `ModuleNotFoundError: src` | Thiếu `PYTHONPATH=/app` hoặc sai WORKDIR | Thêm `ENV PYTHONPATH=/app`, `WORKDIR /app` |
| Build fail ở `nltk.download` | Không có mạng | Bỏ NLTK nếu không dùng |
| `Permission denied` khi ghi output | User không có quyền | `chown` hoặc mount đúng quyền |
| `samples.txt` rỗng | `--output` trỏ sai chỗ | Sửa `--output` như 8.3 |
| Image quá lớn | Cài pandas/numpy không dùng | Bỏ khỏi requirements |
| `--mode generate` không chạy | `CMD` cố định | Dùng `ENTRYPOINT` + `CMD` |

### 8.6 `docker-compose.yml` (tùy chọn)

```yaml
services:
  course-assistant:
    build: .
    image: course-assistant:latest
    volumes:
      - ./output:/app/output
    command: ["--mode", "generate"]
```

Chạy:

```bash
docker compose run --rm course-assistant
```

Không bắt buộc, nhưng tiện demo.

## 9. Cấu trúc zip nộp bài

```text
CO3085-CourseAssistant-<Team>.zip
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── preprocessing.py
│   ├── grammar.py
│   ├── parser.py
│   ├── semantic.py
│   ├── knowledge_base.py
│   ├── data_loader.py
│   ├── dialogue.py
│   ├── evaluation.py
│   └── generator.py
├── data/
│   ├── *.txt
│   ├── test_cases.jsonl
│   └── README.md
├── input/
│   └── sentences.txt
├── output/
│   ├── grammar.txt
│   ├── samples.txt
│   ├── samples.meta.jsonl
│   ├── parse-results.txt
│   ├── semantic.txt
│   ├── intent-entity.txt
│   ├── query.txt
│   ├── answer.txt
│   ├── dialogue.txt
│   ├── evaluation.txt
│   └── evaluation.json
├── docs/
│   └── REPORT.md
├── tests/
│   └── test_*.py
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

**Không đưa vào zip:**

- `.git/`
- `src/__pycache__/`, `*.pyc`
- `.venv/`, `venv/`
- `.pytest_cache/`
- `ENHANCE/`
- `demo.mp4` (dùng link)
- file PDF đề bài (trừ khi giảng viên yêu cầu)
- file log/tmp

### 9.1 Lệnh tạo zip (PowerShell)

```powershell
$exclude = @('.git','__pycache__','.venv','venv','.pytest_cache','ENHANCE','demo.mp4')
# Dùng 7-Zip hoặc Compress-Archive sau khi đã dọn file
Compress-Archive -Path * -DestinationPath CO3085-CourseAssistant.zip -Force
```

Lưu ý: `Compress-Archive` không hỗ trợ exclude pattern tốt. Cách an toàn hơn:

```powershell
# Tạo thư mục tạm sạch
New-Item -ItemType Directory -Force -Path .\submission | Out-Null
Copy-Item src,data,input,output,docs,tests,Dockerfile,.dockerignore,.gitignore,requirements.txt,requirements-dev.txt,README.md -Destination .\submission -Recurse
# Xóa rác trong bản copy
Get-ChildItem .\submission -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Compress-Archive -Path .\submission\* -DestinationPath CO3085-CourseAssistant.zip -Force
Remove-Item -Recurse -Force .\submission
```

### 9.2 Kiểm tra zip trước khi nộp

```powershell
# Giải nén ra thư mục mới và chạy thử
Expand-Archive CO3085-CourseAssistant.zip -DestinationPath .\verify -Force
cd .\verify
python -m src.main --mode demo
python -m src.main --mode generate
python -m src.evaluation --cases data/test_cases.jsonl
```

Nếu chạy được từ bản giải nén → zip đạt.

## 10. Checklist cuối cùng

### 10.1 Code

- [ ] `python -m src.main --mode demo` chạy không lỗi, tiếng Việt đúng.
- [ ] `python -m src.main --mode interactive` nhận câu hỏi và trả lời.
- [ ] `python -m src.main --mode generate` sinh đủ file trong `output/`.
- [ ] `python -m src.evaluation --cases data/test_cases.jsonl` chạy và ghi report.
- [ ] `pytest -q` pass.
- [ ] Không còn `TODO`, `FIXME`, `print()` debug trong code nộp.
- [ ] Không còn hard-code dữ liệu môn học trong `knowledge_base.py`.
- [ ] `samples.txt` ≤ 10.000 câu, không có `_`, không câu vô nghĩa.
- [ ] Parser trả `()` cho câu sai.
- [ ] `PCFG` → CH03 + CH06; `Phần IV` → PART_IV.
- [ ] `Tuần 30` → `INVALID_VALUE`; `Ai dạy` → `NOT_FOUND` rõ ràng.
- [ ] Dialogue resolve `nó`, `phần này`, `chương này`, `nội dung này`.

### 10.2 Dữ liệu

- [ ] `data/` có đủ file, UTF-8.
- [ ] `data/README.md` ghi nguồn và cảnh báo dữ liệu mẫu.
- [ ] Loader validate fail fast.
- [ ] `data/test_cases.jsonl` có 100 case.

### 10.3 Output

- [ ] 9 file output cũ + `evaluation.json` + `samples.meta.jsonl`.
- [ ] Không file nào chỉnh tay.
- [ ] `output/evaluation.txt` khớp `output/evaluation.json`.
- [ ] `output/dialogue.txt` có `Resolved reference` và `State after turn`.

### 10.4 Tài liệu

- [ ] `README.md` có bảng thành viên, MSSV, phân công.
- [ ] `README.md` không còn chữ “Sample”.
- [ ] `README.md` số liệu khớp `evaluation.json`.
- [ ] `README.md` lệnh chạy đúng.
- [ ] `docs/REPORT.md` không còn module hư cấu.
- [ ] `docs/REPORT.md` không còn NLTK nếu code không dùng.
- [ ] `docs/REPORT.md` có error analysis thật.
- [ ] Có link video demo.

### 10.5 Docker

- [ ] `docker build -t course-assistant .` thành công.
- [ ] `docker run --rm course-assistant --mode demo` chạy.
- [ ] `docker run --rm course-assistant --mode generate` chạy.
- [ ] `docker run --rm -v "${PWD}/output:/app/output" course-assistant --mode generate` ghi ra host.
- [ ] Không có `UnicodeEncodeError`.
- [ ] Image không cài NLTK/pandas/numpy không dùng.

### 10.6 Repo

- [ ] Không còn `src/__pycache__/`, `*.pyc`.
- [ ] Có `.gitignore`, `.dockerignore`.
- [ ] `git status` sạch (trừ file chưa track có chủ đích).
- [ ] Không có file cá nhân, log, tmp.
- [ ] `.git` không nằm trong zip.

### 10.7 Nộp bài

- [ ] Zip đúng tên: `CO3085-CourseAssistant-<Team>.zip`.
- [ ] Giải nén và chạy thử thành công.
- [ ] Đã upload đúng portal/link.
- [ ] Đã kiểm tra dung lượng (< giới hạn).
- [ ] Đã gửi link video (nếu không kèm file).

## 11. Kế hoạch triển khai

| Bước | Việc làm | Kết quả | Ước lượng |
|---|---|---|---|
| 1 | Dọn repo: xóa `__pycache__`, thêm `.gitignore`, `.dockerignore` | Repo sạch | 0.5 ngày |
| 2 | Sửa `main.py`: encoding, `--output`, entrypoint | Chạy ổn | 0.5 ngày |
| 3 | Sửa Dockerfile, build, chạy demo/generate | Docker đạt | 1 ngày |
| 4 | Viết lại README theo template, thêm thành viên | README đúng | 0.5 ngày |
| 5 | Căn chỉnh REPORT từng mục | REPORT khớp code | 1 ngày |
| 6 | Quay video demo 5–7 phút | Video | 0.5–1 ngày |
| 7 | Sinh lại output, kiểm tra zip | Bản nộp | 0.5 ngày |
| 8 | Checklist cuối, nộp | Hoàn tất | 0.25 ngày |

Tổng: **2–3 ngày** (sau khi Part 1–5 xong).

## 12. Rủi ro và lưu ý

- **README/REPORT mô tả sai code:** giảng viên chạy thử sẽ phát hiện ngay. Ưu
  tiên căn chỉnh trước khi quay video.
- **Số liệu đẹp nhưng sai:** không dùng 100% của harness lỗi. Lấy từ
  `evaluation.json` sau khi Part 5 xong.
- **Docker build lâu:** bỏ dependency không dùng; dùng `.dockerignore`.
- **Docker không có mạng:** bỏ `nltk.download`; nếu cần pip install, build trên
  máy có mạng rồi cache image.
- **Encoding Windows:** set `PYTHONIOENCODING=utf-8` trong cả code và Docker.
- **`--output` tương đối:** resolve theo project root, không theo `src/`.
- **Video quá dài:** 5–7 phút, tập trung vào điểm mạnh và case khó.
- **Zip chứa `.git`/`__pycache__`:** kiểm tra bằng `git ls-files` và giải nén
  thử.
- **Quên thành viên:** đây là yêu cầu bắt buộc của bài tập nhóm; kiểm tra lại.
- **Nộp nhầm bản sample:** đổi tiêu đề, xóa chữ “Sample”, kiểm tra commit hash
  trong report.
