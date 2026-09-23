# Course Assistant - NLP Assignment Sample
## Trợ lý hỗ trợ học tập thông minh - Intelligent Course Assistant

**Môn học:** Xử lý Ngôn ngữ Tự nhiên (CO3085) — HK261
**Bài tập lớn:** Course Assistant

---

## Giới thiệu

Đây là bộ code mẫu cho bài tập lớn **Course Assistant** - hệ thống trợ lý hỗ trợ học tập thông minh cho môn Xử lý Ngôn ngữ Tự nhiên.

Hệ thống cho phép người dùng tương tác bằng ngôn ngữ tự nhiên (tiếng Việt) để tra cứu thông tin về môn học CO3085.

## Cấu trúc Project

```
Course_Assistant_Sample/
├── src/                       # Source code
│   ├── __init__.py
│   ├── main.py                # Main application (CLI + interactive)
│   ├── preprocessing.py       # Text preprocessing & tokenization
│   ├── grammar.py             # CFG Grammar + sentence generation
│   ├── parser.py              # Recursive descent + fallback parser
│   ├── semantic.py            # Semantic representation & intent classification
│   ├── knowledge_base.py      # Knowledge base for course info
│   ├── dialogue.py            # Dialogue context manager
│   └── evaluation.py          # System evaluation
├── data/                      # Course data files
├── input/                     # Input sentences for testing
├── output/                    # Generated outputs (all 9 files)
│   ├── grammar.txt            # Generated grammar
│   ├── samples.txt            # 10,000+ sentences
│   ├── parse-results.txt      # Parse trees
│   ├── semantic.txt           # Semantic representations
│   ├── intent-entity.txt      # Intent + entities
│   ├── query.txt              # Generated queries
│   ├── answer.txt             # Generated answers
│   ├── dialogue.txt           # Multi-turn dialogues
│   └── evaluation.txt         # Evaluation report
├── docs/
│   └── REPORT.md              # Detailed technical report
├── README.md                  # This file
├── Dockerfile
└── requirements.txt
```

## Cài đặt

### Yêu cầu

- Python 3.8+
- pip

### Các bước

1. **Clone hoặc download project**

2. **Tạo virtual environment** (khuyến nghị):
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

## Cách sử dụng

### Chạy Demo

```bash
python -m src.main --mode demo
```

Output: Hiển thị pipeline đầy đủ cho từng câu test.

### Chế độ Interactive

```bash
python -m src.main --mode interactive
```

Output: Chat trực tiếp với Course Assistant.

### Generate Outputs

```bash
python -m src.main --mode generate
```

Output: Tạo tất cả 9 file output theo yêu cầu bài tập.

### Chạy Evaluation

```bash
python -m src.evaluation
```

Output: Báo cáo đánh giá hệ thống trên test set.

## Pipeline NLP

Hệ thống thực hiện pipeline NLP hoàn chỉnh:

```
Input → Preprocessing → Parsing → Semantic Analysis → KB Query → Answer
```

### 1. Preprocessing (`preprocessing.py`)
- Tokenization (bảo vệ L.O.X.Y patterns)
- Normalization (lowercase, NFC unicode)
- POS tagging (rule-based)
- Keyword extraction

### 2. Grammar & Parser (`grammar.py`, `parser.py`) — Phần I
- CFG grammar cho miền Course Assistant
- Recursive descent parser với fallback pattern matching
- Sinh tối đa 10,000 câu từ grammar

### 3. Semantic Representation (`semantic.py`) — Phần II
- Priority-based intent classification (9 intents)
- Entity extraction (course, chapter, week, topic, LO, assignment)
- Attribute detection (credits, midterm_duration, final_duration, parts, …)
- Logical form generation

### 4. Knowledge Base (`knowledge_base.py`)
- Course information (credits, parts, learning outcomes)
- Schedule (15 weeks)
- 12 chapters with topics and keywords
- Assignment details (BTL01 with 4 parts)
- Resources, regulations, FAQ

### 5. Answer Generation
- Query knowledge base based on intent + entities
- Generate natural language answers in Vietnamese
- Handle "not found" cases

### 6. Dialogue Context (`dialogue.py`) — Phần III (tùy chọn)
- Reference resolution (pronoun, demonstrative, definite)
- Discourse entity tracking
- Context-aware query handling

### 7. Evaluation (`evaluation.py`) — Phần IV
- Test set with 20+ queries
- Intent accuracy, entity accuracy, out-of-scope detection
- Error analysis
- Per-intent performance breakdown

## Intents được hỗ trợ

| Intent | Mô tả | Ví dụ |
|--------|-------|-------|
| GET_COURSE_INFO | Thông tin chung môn học | "Môn NLP có bao nhiêu tín chỉ?" |
| GET_SCHEDULE | Lịch học | "Tuần 3 học gì?", "Chương 4 học vào tuần nào?" |
| GET_TOPIC | Nội dung chương | "Chương nào học về CFG?" |
| GET_ASSIGNMENT | Thông tin bài tập | "Bài tập lớn yêu cầu gì?" |
| GET_DEADLINE | Thời hạn | "Deadline BTL là khi nào?" |
| GET_RESOURCE | Tài liệu tham khảo | "Tài liệu về CFG ở đâu?" |
| GET_RULE | Quy định | "Có được dùng LLM không?" |
| GET_LO | Learning Outcome | "L.O.2.5 là gì?" |
| UNKNOWN | Ngoài phạm vi | "Hôm nay thời tiết thế nào?" |

## Kết quả đánh giá

Trên test set 20 câu (17 in-scope + 3 out-of-scope):

- **Intent Accuracy:** 100% (20/20)
- **Entity Accuracy:** 100% (20/20)
- **Out-of-Scope Detection:** 100% (3/3)
- **Per-Intent Accuracy:** 100% cho tất cả 9 intent

Xem chi tiết trong `output/evaluation.txt`.

## Ví dụ câu hỏi & câu trả lời

| Câu hỏi | Intent | Trả lời |
|----------|--------|---------|
| Môn NLP có bao nhiêu tín chỉ? | GET_COURSE_INFO | Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ. |
| Môn học gồm những phần nào? | GET_COURSE_INFO | Môn học gồm 3 phần chính: Xử lý cú pháp; Diễn dịch ngữ nghĩa; Ngữ cảnh và tri thức thế giới. |
| Tuần 3 học gì? | GET_SCHEDULE | Tuần 03: Học Chương 03 - Grammar and Parsing. |
| Chương nào học về CFG? | GET_TOPIC | Chương 03: Grammar and Parsing trình bày về CFG. |
| Chương 4 học vào tuần nào? | GET_SCHEDULE | Chương 04 (Features and Augmented Grammar) được học vào Week 04. |
| PCFG được học ở đâu? | GET_TOPIC | Chương 03: Grammar and Parsing trình bày về CFG. |
| BTL gồm những phần nào? | GET_ASSIGNMENT | Bài tập lớn gồm các phần: Grammar and Parser; Semantic Interpretation and QA; Local Discourse Context; Evaluation. |
| Deadline BTL là khi nào? | GET_DEADLINE | Thời hạn BTL: checkpoint_1: Tuần 8, checkpoint_2: Tuần 12, final: Tuần 15. |
| L.O.2.5 là gì? | GET_LO | LO2.5: Kiến thức xác suất để giải quyết nhập nhằng từ ở mức câu. |
| Hôm nay thời tiết thế nào? | UNKNOWN | Xin lỗi, tôi không hiểu câu hỏi này. |

## Tùy chọn nâng cao (LLM/RAG)

Bài tập cho phép mở rộng bằng LLM/RAG. Trong mẫu này, nhóm đã chọn **Classical/Statistical NLP** làm phương pháp chính. Có thể mở rộng thêm:

- **Retrieval:** Thêm TF-IDF hoặc BM25 cho việc tìm kiếm thông tin trong KB.
- **RAG:** Kết hợp LLM (qua API) để sinh câu trả lời mượt mà hơn.
- **Thư viện:** Sử dụng `transformers`, `sentence-transformers` cho embedding.

## Docker

### Build
```bash
docker build -t course-assistant .
```

### Run
```bash
docker run -it course-assistant
```

## Tài liệu tham khảo

1. **Slide bài giảng CO3085** — Grammar, Parsing, Semantic Interpretation
2. **Jurafsky & Martin** — Speech and Language Processing
3. **Bird, Klein, Loper** — NLP with Python
4. **Eisenstein** — Introduction to NLP

## License

MIT License - Mã nguồn mẫu tham khảo cho bài tập lớn NLP CO3085.

---

