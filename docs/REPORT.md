# BÁO CÁO BÀI TẬP LỚN

## Trợ lý hỗ trợ học tập thông minh - Course Assistant

---

## MỤC LỤC

1. [Giới thiệu](#1-giới-thiệu)
2. [Phân tích yêu cầu](#2-phân-tích-yêu-cầu)
3. [Kế hoạch thực hiện](#3-kế-hoạch-thực-hiện)
4. [Thiết kế hệ thống](#4-thiết-kế-hệ-thống)
5. [Cài đặt và triển khai](#5-cài-đặt-và-triển-khai)
6. [Đánh giá hệ thống](#6-đánh-giá-hệ-thống)
7. [Kết luận và hạn chế](#7-kết-luận-và-hạn-chế)

---

## 1. Giới thiệu

### 1.1 Bối cảnh bài toán

Trong bài tập lớn này, sinh viên sẽ xây dựng một hệ thống **Trợ lý hỗ trợ học tập (Course Assistant)** trong một miền ngữ nghĩa hẹp. Hệ thống cho phép người dùng tương tác bằng ngôn ngữ tự nhiên để tra cứu và hỏi đáp về thông tin của một môn học (cụ thể là môn Xử lý Ngôn ngữ Tự nhiên - CO3085).

### 1.2 Mục tiêu

- Vận dụng kiến thức NLP đã học trong môn học
- Xây dựng pipeline NLP hoàn chỉnh từ parsing đến semantic interpretation và question answering
- Hiểu và thể hiện được các kỹ thuật: văn phạm, parsing, biểu diễn ngữ nghĩa, nhận diện intent/entity, truy vấn thông tin, và xử lý ngữ cảnh hội thoại

### 1.3 Phạm vi Knowledge Base

Knowledge base của hệ thống bao gồm:

- Thông tin chung của môn học (CO3085)
- Đề cương và nội dung 12 chương
- Lịch học 15 tuần
- Thông tin bài tập lớn
- Quy định môn học
- Tài liệu tham khảo

---

## 2. Phân tích yêu cầu

### 2.1 Cấu trúc bài tập lớn


| Phần         | Mô tả                     | Yêu cầu bắt buộc |
| ------------ | ------------------------- | ---------------- |
| **Phần I**   | Viết văn phạm và Parser   | ✅ Bắt buộc       |
| **Phần II**  | Diễn giải ngữ nghĩa và QA | ✅ Bắt buộc       |
| **Phần III** | Xử lý ngữ cảnh hội thoại  | ⭐ Tùy chọn       |
| **Phần IV**  | Đánh giá hệ thống         | ✅ Bắt buộc       |


### 2.2 Hai lựa chọn cho Phần II

**Lựa chọn 1: Classical/Statistical NLP**

- Xây dựng hoàn toàn bằng phương pháp NLP cổ điển
- Không sử dụng LLM
- Tự xây dựng semantic representation, intent/entity recognition, query mechanism

**Lựa chọn 2: Mở rộng bằng LLM/RAG**

- Sử dụng LLM kết hợp với retrieval
- Đây là phần mở rộng, không thay thế yêu cầu NLP cốt lõi

### 2.3 Các loại Intent cần xử lý


| Intent          | Mô tả                   | Ví dụ                           |
| --------------- | ----------------------- | ------------------------------- |
| GET_COURSE_INFO | Thông tin chung môn học | "Môn NLP có bao nhiêu tín chỉ?" |
| GET_SCHEDULE    | Lịch học                | "Tuần 5 học những gì?"          |
| GET_TOPIC       | Nội dung/chủ đề         | "Chương nào học về CFG?"        |
| GET_ASSIGNMENT  | Thông tin bài tập       | "Bài tập lớn yêu cầu gì?"       |
| GET_DEADLINE    | Thời hạn                | "Deadline BTL là khi nào?"      |
| GET_RESOURCE    | Tài liệu tham khảo      | "Tài liệu về PCFG ở đâu?"       |
| GET_RULE        | Quy định                | "Có được dùng AI không?"        |
| GET_LO          | Learning Outcome        | "L.O.4.2 là gì?"                |
| UNKNOWN         | Ngoài phạm vi           | "Hôm nay thời tiết thế nào?"    |


---

## 3. Kế hoạch thực hiện

### 3.1 Giai đoạn 1: Chuẩn bị

**Hoạt động:**

1. Phân tích chi tiết bộ dữ liệu mẫu (NLP_Course_Assistant_Sample_Data)
2. Xác định các loại câu hỏi và mẫu câu cần xử lý
3. Thiết kế grammar cho miền Course Assistant
4. Chuẩn bị môi trường phát triển (Python/Java)

**Output:**

- Danh sách các loại intent và entity đã xác định
- Môi trường dev sẵn sàng

### 3.2 Giai đoạn 2: Phần I - Grammar & Parser

**Hoạt động:**

1. Xây dựng văn phạm CFG cho miền Course Assistant
2. Cài đặt parser (Top-down hoặc Bottom-up)
3. Sinh câu hợp lệ từ grammar
4. Kiểm thử parser với câu đầu vào

**Grammar mẫu:**

```
S -> WH_WORD NP VP
S -> WH_WORD VP
S -> QUESTION_MARK
NP -> DET NOMINAL | PRONOUN | COURSE_NAME
VP -> V NP | V PREP NP | V
NOMINAL -> N | ADJ NOMINAL
WH_WORD -> "Tuần" | "Chương" | "Môn" | "Bài" | "Tài" | "Quy" | "Thời"
DET -> "các" | "những" | "nào" | "gì"
V -> "học" | "nói" | "có" | "xuất" | "liên quan" | "ở"
```

**Output files:**

```
output/grammar.txt      - Văn phạm
output/samples.txt      - Câu sinh ra (tối đa 10,000 câu)
output/parse-results.txt - Kết quả phân tích
```

### 3.3 Giai đoạn 3: Phần II - Semantic & QA

**Hoạt động:**

1. Xây dựng semantic representation (logic form)
2. Cài đặt intent classifier và entity extractor
3. Xây dựng knowledge base và query engine
4. Tạo câu trả lời từ query results

**Semantic Representation mẫu:**

```
"Môn NLP có bao nhiêu tín chỉ?"
=> GET_COURSE_INFO(course=NLP, attribute=credits)

"Deadline BTL là khi nào?"
=> GET_DEADLINE(assignment=BTL01)
```

**Pipeline xử lý:**

```
Input → Tokenize → Parse → Semantic Rep → Intent/Entity → Query → Answer
```

**Output files:**

```
output/semantic.txt     - Biểu diễn ngữ nghĩa
output/intent-entity.txt - Intent và entity nhận diện
output/query.txt       - Query được tạo
output/answer.txt      - Câu trả lời
```

### 3.4 Giai đoạn 4: Phần III - Dialogue Context [Tùy chọn]

**Hoạt động:**

1. Lưu trữ discourse entities
2. Xử lý tham chiếu đại từ ("nó", "phần này")
3. Xử lý definite description ("chương này", "bài tập đó")
4. Xử lý một số trường hợp ellipsis đơn giản

**Output files:**

```
output/dialogue.txt     - Hội thoại có xử lý ngữ cảnh
```

### 3.5 Giai đoạn 5: Phần IV - Evaluation

**Hoạt động:**

1. Xây dựng test set đa dạng
2. Đánh giá accuracy
3. Phân tích lỗi
4. Viết báo cáo đánh giá

**Test set cần bao gồm:**

- Câu hỏi hợp lệ
- Các cách diễn đạt khác nhau
- Câu hỏi ngoài phạm vi
- Câu hỏi không có thông tin
- Câu hỏi có ngữ cảnh (nếu có Phần III)

**Output files:**

```
output/evaluation.txt  - Báo cáo đánh giá
```

---

## 4. Thiết kế hệ thống

### 4.1 Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│                     NATURAL LANGUAGE INPUT                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PREPROCESSING LAYER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │Tokenize  │→ │ Normalize│→ │ POS Tag  │→ │ Lemmatize│         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PARSING LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              CFG Grammar + Parser                        │   │
│  │   Grammar Rule → Parse Tree → Syntactic Structure        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                SEMANTIC INTERPRETATION LAYER                    │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Semantic Rep     │  │ Intent/Entity    │                     │
│  │ (Logic Form)     │  │ Recognition      │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE BASE LAYER                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Course   │  │ Schedule │  │ Topics   │  │ Assign-  │         │
│  │ Info     │  │          │  │          │  │ ment     │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ Resources│  │ Regula-  │  │ FAQ      │                       │
│  │          │  │ tions    │  │          │                       │
│  └──────────┘  └──────────┘  └──────────┘                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANSWER GENERATION LAYER                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │  Query   │→ │ Retrieve │→ │ Generate │                       │
│  │  Engine  │  │  Info    │  │ Answer   │                       │
│  └──────────┘  └──────────┘  └──────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ANSWER OUTPUT                            │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Chi tiết từng thành phần

#### 4.2.1 Preprocessing Layer

```python
# Text preprocessing pipeline
def preprocess(text):
    # 1. Tokenization
    tokens = tokenize(text)
    
    # 2. Normalization (lowercase, remove punctuation)
    normalized = normalize(tokens)
    
    # 3. POS Tagging
    pos_tags = pos_tag(normalized)
    
    # 4. Lemmatization
    lemmas = lemmatize(normalized, pos_tags)
    
    return {
        'tokens': tokens,
        'normalized': normalized,
        'pos_tags': pos_tags,
        'lemmas': lemmas
    }
```

#### 4.2.2 Grammar và Parser

**Grammar Format (CFG):**

```
SENTENCE → WH_WORD NP VP
SENTENCE → WH_WORD VP
SENTENCE → STATEMENT QUESTION_MARK

WH_WORD → "tuần" | "chương" | "môn" | "bài" | "tài" | "quy" | "thời"
NP → DET NOMINAL
NP → PRONOUN
NP → COURSE_NAME
VP → VERB NP
VP → VERB PP
VP → VERB

NOMINAL → NOUN
NOMINAL → ADJ NOMINAL
...
```

**Parser Algorithm:**

- Top-down parsing với backtracking
- Hoặc CYK algorithm cho CFG
- Hoặc Chart parsing để tăng hiệu suất

#### 4.2.3 Semantic Representation

**Logic Form Structure:**

```python
class SemanticRepresentation:
    intent: str           # GET_COURSE_INFO, GET_TOPIC, etc.
    entities: Dict        # {course: NLP, chapter: CH03, ...}
    attributes: Dict      # {credits: true, schedule: true}
    operators: List      # AND, OR, NOT
    
# Ví dụ:
"Môn NLP có bao nhiêu tín chỉ?"
=> SemanticRepresentation(
    intent="GET_COURSE_INFO",
    entities={"course": "NLP"},
    attributes={"credits": True}
)
```

#### 4.2.4 Intent Classification

**Phương pháp:** Rule-based + Keyword matching

```python
INTENT_PATTERNS = {
    "GET_COURSE_INFO": [
        r"(tín chỉ|credit|bao nhiêu)",
        r"(phần|chính|nội dung)",
        r"(midterm|final|thi)",
        r"(mô tả|mục tiêu)"
    ],
    "GET_SCHEDULE": [
        r"(tuần|học|lich)",
        r"(khi nào|nào)"
    ],
    "GET_TOPIC": [
        r"(chương|chapter)",
        r"(về|nói|học về)"
    ],
    "GET_ASSIGNMENT": [
        r"(btl|bài tập lớn|assignment)",
        r"(yêu cầu|requirement)"
    ],
    "GET_DEADLINE": [
        r"(deadline|thời hạn|hạn nộp)",
        r"(khi nào|mấy giờ)"
    ],
    "GET_RESOURCE": [
        r"(tài liệu|tài nguyên|resource)",
        r"(sách|giáo trình|tham khảo)"
    ],
    "GET_RULE": [
        r"(quy định|rule|regulation)",
        r"(được phép|không được)"
    ]
}
```

#### 4.2.5 Entity Extraction

```python
ENTITY_PATTERNS = {
    "course": ["nlp", "co3085", "xử lý ngôn ngữ tự nhiên"],
    "chapter": ["chương 1", "chương 2", ..., "chương 12"],
    "week": ["tuần 1", "tuần 2", ..., "tuần 15"],
    "topic": ["cfg", "pcfg", "parsing", "semantic", ...],
    "assignment": ["btl", "bài tập lớn", "part i", "part ii"],
    "lo": ["l.o.1", "l.o.2", ..., "l.o.4.2"]
}
```

### 4.3 Knowledge Base Structure

```python
KNOWLEDGE_BASE = {
    "course_info": {
        "CO3085": {
            "name": "Xử lý Ngôn ngữ Tự nhiên",
            "credits": 3,
            "ects": 6,
            "parts": ["Syntactic Processing", "Semantic Interpretation", "Context"],
            "description": "..."
        }
    },
    
    "schedule": {
        "WEEK_01": {"chapter": "CH01", "topics": [...]},
        "WEEK_02": {"chapter": "CH02", "topics": [...]},
        ...
    },
    
    "topics": {
        "CH01": {"name": "Introduction", "keywords": [...], "content": "..."},
        "CH02": {"name": "English Syntax", "keywords": [...], "content": "..."},
        ...
    },
    
    "assignments": {
        "BTL01": {
            "title": "Intelligent Course Assistant",
            "parts": ["Grammar & Parser", "Semantic & QA", "Dialogue"],
            "deadlines": {...}
        }
    },
    
    "resources": [...],
    
    "regulations": {...}
}
```

---

## 5. Cài đặt và triển khai

### 5.1 Yêu cầu môi trường

**Ngôn ngữ:** Python 3.8+ hoặc Java 11+

**Python dependencies:**

```
nltk>=3.6
pandas>=1.3
numpy>=1.19
```

**Cài đặt:**

```bash
# Python
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

### 5.2 Cấu trúc project

```
Course_Assistant_Sample/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── preprocessing.py      # Text preprocessing
│   ├── grammar.py            # CFG grammar definitions
│   ├── parser.py             # Parser implementation
│   ├── semantic.py           # Semantic representation
│   ├── intent.py             # Intent classification
│   ├── entity.py             # Entity extraction
│   ├── knowledge_base.py     # KB management
│   ├── query.py              # Query engine
│   ├── answer.py             # Answer generation
│   └── dialogue.py           # Dialogue context (optional)
├── data/
│   ├── course_info.txt
│   ├── schedule.txt
│   ├── topics.txt
│   ├── assignments.txt
│   ├── resources.txt
│   ├── regulations.txt
│   └── entities.txt
├── input/
│   └── sentences.txt         # Input sentences for parsing
├── output/
│   ├── grammar.txt
│   ├── samples.txt
│   ├── parse-results.txt
│   ├── semantic.txt
│   ├── intent-entity.txt
│   ├── query.txt
│   ├── answer.txt
│   ├── dialogue.txt
│   └── evaluation.txt
├── docs/
│   └── REPORT.md
├── README.md
├── Dockerfile
└── requirements.txt
```

### 5.3 Chạy chương trình

```bash
# Chạy toàn bộ pipeline
python src/main.py

# Chạy từng phần
python src/main.py --part 1    # Grammar & Parser
python src/main.py --part 2    # Semantic & QA
python src/main.py --part 3    # Dialogue
python src/main.py --evaluate  # Evaluation
```

### 5.4 Docker deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "src/main.py"]
```

---

## 6. Đánh giá hệ thống

### 6.1 Test Set Construction

**Nguyên tắc xây dựng test set:**

1. **Câu hỏi hợp lệ:** Được sinh từ grammar
2. **Các biến thể:** Cùng intent nhưng cách diễn đạt khác nhau
3. **Out-of-scope:** Câu hỏi ngoài miền dữ liệu
4. **No-info:** Câu hỏi không có thông tin trong KB
5. **Context-dependent:** Câu hỏi cần ngữ cảnh

**Kích thước test set đề xuất:** 50-100 câu hỏi

### 6.2 Metrics


| Metric    | Công thức           | Mục tiêu |
| --------- | ------------------- | -------- |
| Accuracy  | Correct / Total     | > 80%    |
| Precision | TP / (TP + FP)      | > 85%    |
| Recall    | TP / (TP + FN)      | > 80%    |
| F1-Score  | 2 * P * R / (P + R) | > 82%    |


### 6.3 Error Analysis

**Các loại lỗi thường gặp:**

1. **Parsing errors:** Câu không theo grammar
2. **Intent misclassification:** Sai intent
3. **Entity extraction errors:** Entity không đúng
4. **KB lookup failures:** Không tìm thấy thông tin
5. **Answer generation errors:** Câu trả lời không chính xác

**Ví dụ phân tích lỗi:**

```
Query: "NLP là gì?"
Expected Intent: GET_COURSE_INFO
Predicted Intent: GET_TOPIC
Error Type: Intent misclassification

Root Cause: Từ "gì" trigger GET_TOPIC nhưng câu hỏi này muốn 
           hỏi mô tả course info

Fix: Thêm pattern "X là gì?" cho GET_COURSE_INFO với highest priority
```

### 6.4 Báo cáo đánh giá mẫu

```
EVALUATION REPORT
=================

Test Set Statistics:
- Total queries: 50
- Valid in-scope: 40
- Out-of-scope: 10

Results:
- Correct answers: 38
- Accuracy: 76.0%

Per-Intent Performance:
| Intent           | Precision | Recall | F1-Score |
|------------------|-----------|--------|----------|
| GET_COURSE_INFO  | 0.85      | 0.90   | 0.87     |
| GET_SCHEDULE     | 0.80      | 0.85   | 0.82     |
| GET_TOPIC        | 0.75      | 0.80   | 0.77     |
| GET_ASSIGNMENT   | 0.90      | 0.85   | 0.87     |
| GET_DEADLINE     | 0.95      | 0.95   | 0.95     |
| GET_RESOURCE     | 0.70      | 0.75   | 0.72     |
| GET_RULE         | 0.80      | 0.80   | 0.80     |
| UNKNOWN          | 0.90      | 0.90   | 0.90     |

Error Cases:
1. Query: "Môn học có gì hay?" 
   Expected: GET_COURSE_INFO
   Predicted: GET_TOPIC
   Reason: Keyword "có" và "gì" conflicting

2. Query: "Tham khảo tài liệu nào?"
   Expected: GET_RESOURCE
   Predicted: GET_TOPIC
   Reason: "nào" trigger topic intent

Limitations:
1. Rule-based intent classification has limited coverage
2. Cannot handle complex multi-intent queries
3. Vietnamese text normalization needs improvement
4. Out-of-scope detection is conservative
```

---

## 7. Kết luận và hạn chế

### 7.1 Kết luận

1. **Hoàn thành các yêu cầu cơ bản:** Đã xây dựng được pipeline NLP hoàn chỉnh từ grammar/parser đến QA.
2. **Áp dụng kiến thức NLP:** Hệ thống thể hiện được các kỹ thuật:
  - CFG grammar và parsing
  - Semantic representation
  - Intent/entity recognition
  - Knowledge-based QA
  - Local discourse context (tùy chọn)
3. **Khả năng mở rộng:** Hệ thống có thể được mở rộng với LLM/RAG cho phần bonus.

### 7.2 Hạn chế

1. **Rule-based approach:**
  - Giới hạn trong việc xử lý các mẫu câu đã được định nghĩa
  - Khó mở rộng cho các cách diễn đạt mới
2. **Vietnamese NLP:**
  - Tokenization và lemmatization cho tiếng Việt chưa hoàn hảo
  - Thiếu Vietnamese-specific NLP tools
3. **Knowledge Base:**
  - Chỉ hỗ trợ truy vấn đơn giản
  - Không hỗ trợ reasoning phức tạp
4. **Dialogue Context:**
  - Chỉ hỗ trợ một số trường hợp đơn giản
  - Không xử lý được multi-turn dialogue phức tạp

### 7.3 Hướng phát triển

1. **LLM Integration:** Sử dụng LLM để cải thiện intent classification và answer generation
2. **RAG Pipeline:** Xây dựng retrieval system để hỗ trợ open-domain queries
3. **Better Vietnamese NLP:** Tích hợp Vietnamese NLP libraries
4. **Dialogue Manager:** Xây dựng dialogue manager hoàn chỉnh hơn
5. **Evaluation:** Bổ sung A/B testing và human evaluation

---

## Phụ lục

### Sample Input/Output

**Input (input/sentences.txt):**

```
Môn NLP có bao nhiêu tín chỉ?
Tuần 3 học những gì?
Chương nào nói về CFG?
Deadline BTL là khi nào?
Tài liệu về PCFG ở đâu?
```

**Output (output/parse-results.txt):**

```
SENTENCE
├── WH_WORD: "Môn"
├── NP
│   └── COURSE: "NLP"
└── VP
    ├── VERB: "có"
    └── NP
        ├── QUANTIFIER: "bao nhiêu"
        └── NOUN: "tín chỉ"

SENTENCE
├── WH_WORD: "Tuần"
├── NUM: "3"
└── VP
    └── VERB: "học"
    └── NP
        └── PRONOUN: "gì"
...
```

**Output (output/answer.txt):**

```
Query: "Môn NLP có bao nhiêu tín chỉ?"
Intent: GET_COURSE_INFO
Entity: {course: NLP}
Answer: "Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ."

Query: "Tuần 3 học những gì?"
Intent: GET_SCHEDULE
Entity: {week: WEEK_03}
Answer: "Tuần 3 học Chương 3 về Văn phạm và phân tích cú pháp, gồm CFG, top-down parsing, bottom-up chart parsing, PCFG và dependency grammar."
...
```

---

*Báo cáo được viết cho mục đích tham khảo thực hiện bài tập lớn Course Assistant*