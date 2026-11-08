# PART 3 — Cải thiện Knowledge Base và Answer

> Đây là phần quan trọng nhất. Mục tiêu không chỉ là “sửa vài câu trả lời” mà là
> **thay toàn bộ nguồn dữ liệu hard-code bằng một pipeline load dữ liệu có schema,
> có kiểm tra, có index và có chính sách “không có thông tin” nhất quán**.

## 1. Mục tiêu

Sau bước này:

1. Knowledge base đọc dữ liệu từ `data/`, không hard-code nội dung môn học trong
   `src/knowledge_base.py`.
2. Trả lời đúng:
   - `PCFG` → **CFG** (không còn nhầm),
   - `Phần IV của BTL` → **PART_IV** (không còn nhầm thành PART_I),
   - yêu cầu của bài tập lớn,
   - các file cần xuất của từng phần BTL,
   - tài liệu theo chủ đề,
   - quy định, FAQ, learning outcome theo đúng dữ liệu.
3. Xử lý nhất quán các trường hợp:
   - ngoài phạm vi môn học,
   - trong phạm vi nhưng không có dữ liệu,
   - có entity nhưng giá trị không hợp lệ (tuần 30, chương 15, LO4.3),
   - câu hỏi mơ hồ (nhiều chương cùng chứa một topic).
4. Mọi câu trả lời có thể truy vết về file + record nguồn.
5. `output/answer.txt`, `output/query.txt`, `output/semantic.txt`,
   `output/intent-entity.txt` được sinh lại từ code.

## 2. Kết luận điều tra nhanh

**Có cần pipeline load dữ liệu? Có.** Một file `data/course_data.txt` phẳng
35 dòng hiện tại **không đủ** và cũng **không được code đọc**. Knowledge base
đang hard-code ít nhất:

| Nhóm dữ liệu | Số record hard-code | File nguồn mẫu tương ứng |
|---|---:|---|
| Course info | 1 record + 16 LO + 3 parts + 2 exam | `course_info.txt` |
| Chapters | 12 record | `topics.txt` |
| Schedule | 15 record | `schedule.txt` |
| Assignment | 1 record + 4 parts + 3 deadlines | `assignments.txt` |
| Resources | 4 record | `resources.txt` |
| Regulations | 5 record | `regulations.txt` |
| FAQ | 4 record | `faq.txt` |
| **Tổng record nội dung** | **42 record** | 11 file mẫu |

So với `BTL/NLP_Sample_Data`, dữ liệu hard-code **thiếu**:

- 4/8 tài liệu,
- 3/8 quy định,
- 11/15 FAQ,
- toàn bộ `requirements`, `suggested_outputs`, `minimum_requirements`,
  `suggested_intents` của bài tập lớn,
- `activity`/`milestone` của lịch 15 tuần,
- nhiều subtopic của chương,
- assessment, exam format, số giờ học,
- alias topic như `SEMANTIC_GRAMMAR`, `KNOWLEDGE_REPRESENTATION`,
  `QUESTION_ANSWERING`, `REFERENCE`, `SELECTIONAL_RESTRICTION`,
- 5 kịch bản hội thoại mẫu và 34 query đánh giá mẫu.

Vì vậy cần:

1. Copy bộ dữ liệu mẫu vào `data/` (giữ nguyên định dạng text để dễ so sánh).
2. Viết `src/data_loader.py` đọc từng file thành dataclass.
3. Thay các biến global trong `knowledge_base.py` bằng object load từ loader.
4. Sinh alias/index từ dữ liệu, không hard-code trong `semantic.py`/`grammar.py`.
5. Thêm validation và test dữ liệu.

## 3. Phương pháp audit

Đã kiểm tra:

- Toàn bộ `src/*.py` tại commit `883e0c6`.
- `data/course_data.txt`.
- Toàn bộ 11 file trong
  `D:\_HCMUT\_Nam4\k261\CO3085-Natual-Lannguage-Processing\BTL\NLP_Sample_Data`.
- Chạy thử `CourseAssistant.process_query()` với các câu hỏi đại diện.
- Đối chiếu `output/evaluation.txt`, `output/answer.txt`, `output/samples.txt`.

Mọi số dòng trong tài liệu này là số dòng tại thời điểm audit; khi sửa code cần
cập nhật lại.

## 4. Kiểm kê hard-code chi tiết

### 4.1 `src/knowledge_base.py` — 527 dòng

| Vị trí | Nội dung hard-code | Ghi chú |
|---|---|---|
| dòng 10–67 | 6 dataclass: `CourseInfo`, `ChapterInfo`, `WeekSchedule`, `AssignmentInfo`, `ResourceInfo` | Schema đã có nhưng không dùng để load |
| dòng 71–103 | `COURSE_INFO` | `course_id`, `name`, `name_en`, `credits=3`, `ects=6`, `semester=HK261`, `department`, `description` ngắn, 3 `parts`, 16 `learning_outcomes`, `exam_duration={midterm:60, final:90}` |
| dòng 106–222 | `CHAPTERS` dict 12 phần tử | Mỗi chương: `chapter_id`, `name`, `part`, `keywords`, `summary`, `subtopics` |
| dòng 225–231 | `SCHEDULE` sinh bằng comprehension | 15 tuần, chapter tính bằng công thức `(i-1)//2+1` |
| dòng 234–248 | 15 override `SCHEDULE["WEEK_xx"]` | `WEEK_15` gán `CH00` (không tồn tại) |
| dòng 251–267 | `ASSIGNMENT` | `BTL01`, title, team size, goal, 4 parts (name + description), 3 deadlines |
| dòng 270–275 | `RESOURCES` | 4 `ResourceInfo` |
| dòng 278–284 | `REGULATIONS` | 5 cặp key/value |
| dòng 287–292 | `FAQ` | 4 cặp key/value; **không được dùng trong `query()`** |
| dòng 295–308 | `KnowledgeBase.__init__` | Gán trực tiếp các global |
| dòng 310–449 | Các hàm trả lời | Logic hard-code theo từng nhánh |
| dòng 451–491 | `query()` | Dispatch theo intent; không có `GET_INSTRUCTOR` |

Các lỗi logic đáng chú ý:

- `get_assignment_info()` dùng `if part_upper in p["id"].upper()` và sau đó
  duyệt `roman_map` bằng `if full in part_upper`, gây nhầm `PART_IV` → `PART_I`.
- `get_topic_chapter()` so khớp `topic_lower in ch.name.lower()` và
  `any(topic_lower in k ...)`, không ưu tiên alias dài; `pcfg` chứa `cfg`.
- `get_schedule()` trả “Vui lòng cho biết tuần cụ thể.” khi `week=None`, và
  cũng trả câu tương tự khi `WEEK_30` không có trong dict.
- `get_resource()` chỉ tìm `topic_lower in r.title.lower()`; không có mapping
  topic → resource.
- `get_regulation()` chỉ nhận diện `ai`/`llm` và `giả`/`copy`; bỏ sót
  `source_code`, `assignment_sharing`, `external_libraries`.
- `get_learning_outcome()` không xử lý LO cấp 1 (`LO2`) và không phân biệt
  “không có LO” với “LO không tồn tại”.
- `FAQ` là dữ liệu chết.

### 4.2 `src/semantic.py` — 428 dòng

| Vị trí | Nội dung hard-code |
|---|---|
| dòng 12–23 | 9 intent + `UNKNOWN` |
| dòng 77–164 | `intent_patterns`: keyword + regex cho từng intent |
| dòng 190–200 | `priority_order` 9 intent |
| dòng 206–214 | 7 regex out-of-scope |
| dòng 220–260 | Chuỗi `if re.search(...)` hard-code cho deadline, LO, instructor, rule, resource, assignment, schedule, topic |
| dòng 307–312 | `topic_keywords`: 11 alias topic |
| dòng 322–333 | Regex part `i{1,3}|iv|v|\d+`, map roman, `list_parts` |
| dòng 335–344 | Regex LO `lo_(\d)(?:_(\d+))?`, mặc định `.1` nếu không có sub |
| dòng 346–359 | Attribute detection cho course info |
| dòng 388–397 | `EXAMPLE_SEMANTIC_FORMS` 8 ví dụ |

Không đọc `entities.txt`, `topics.txt` hay bất kỳ file dữ liệu nào.

### 4.3 `src/grammar.py` — 421 dòng

| Vị trí | Nội dung hard-code |
|---|---|
| dòng 50–230 | Toàn bộ CFG: 12 chapter, 15 week, 8 topic, 3 course name, 3 assignment name, 16 LO, 17 verb, 16 noun, 8 DET, 6 ADV, 8 ADJ, 18 NUM |
| dòng 314–365 | 35 template câu hỏi |
| dòng 368–407 | `generate_template_sentences()`: danh sách course/chapter/week/topic/part/LO hard-code, chỉ dùng một phần tử đầu |

Grammar không lấy terminal từ KB. Khi dữ liệu đổi (thêm chương, đổi LO), grammar
vẫn sinh dữ liệu cũ.

### 4.4 `src/main.py` — 469 dòng

| Vị trí | Nội dung hard-code |
|---|---|
| dòng 201–209 | 7 query demo pipeline |
| dòng 248–250 | 30 câu grammar demo |
| dòng 261–267 | 5 câu parsing demo |
| dòng 372–379 | 6 lượt dialogue demo |
| dòng 403–409 | 5 query evaluation riêng |
| dòng 323–327 | 3 câu fallback nếu không có `input/sentences.txt` |

Đáng chú ý: `save_outputs()` tự viết một báo cáo evaluation 5 câu, **khác** với
`src/evaluation.py` (20 câu). Hai nguồn số liệu không khớp.

### 4.5 `src/evaluation.py` — 367 dòng

| Vị trí | Nội dung hard-code |
|---|---|
| dòng 297–333 | `DEFAULT_TEST_CASES`: 20 case (17 in-scope + 3 out-of-scope) |
| dòng 336–363 | `run_evaluation()` dùng test set trên, ghi `output/evaluation.txt` |

### 4.6 `data/course_data.txt` — 35 dòng

Chỉ có:

```text
[COURSE_INFO]  course_id, course_name, course_name_en, credits, ects, semester
[CHAPTERS]     12 dòng CH01..CH12 (chỉ tên)
[PARTS]        3 dòng Part_I..Part_III
[LEARNING_OUTCOMES] LO1..LO4 (chỉ 4 dòng)
```

Không có schedule, assignment, resources, regulations, FAQ, entities.
**Không file nào trong `src/` mở file này.**

## 5. Đối chiếu với `BTL/NLP_Sample_Data`

### 5.1 Tổng quan 11 file mẫu

| File | Số dòng | Nội dung chính |
|---|---:|---|
| `00_README.txt` | 57 | Mô tả bộ dữ liệu, phạm vi, cấu trúc |
| `course_info.txt` | 64 | Thông tin môn, LO, assessment, exam format |
| `schedule.txt` | 166 | 15 tuần, topics, activity, milestone |
| `topics.txt` | 207 | 12 chương, keywords, summary, subtopics |
| `assignments.txt` | 81 | Yêu cầu 4 phần BTL, output, intent gợi ý, LLM/RAG |
| `resources.txt` | 55 | 3 textbook + 5 reference + study note |
| `regulations.txt` | 36 | 8 quy định |
| `faq.txt` | 68 | 15 cặp Q/A |
| `dialogues.txt` | 49 | 5 kịch bản hội thoại |
| `sample_queries.txt` | 46 | 34 query có nhãn |
| `entities.txt` | 69 | Alias course/part/chapter/topic/assignment/intent |

### 5.2 Course info

| Trường | Hard-code hiện tại | `course_info.txt` | Hành động |
|---|---|---|---|
| `course_id` | `CO3085` | `CO3085` | Load |
| `course_name` | Có | Có | Load |
| `course_name_en` | Có | Có | Load |
| `semester` | `HK261` | `HK261` | Load |
| `credits` | `3` | `3` | Load |
| `ects` | `6` | `6` | Load |
| `course_type` | **Thiếu** | `Specialty / Graduation knowledge block` | Bổ sung |
| `department` | Có | Có | Load |
| `format` | **Thiếu** | `2 lecture periods per week, 15 weeks` | Bổ sung |
| `total_course_hours` | **Thiếu** | `150` | Bổ sung |
| `lecture_hours` | **Thiếu** | `30` | Bổ sung |
| `major_assignment_hours` | **Thiếu** | `45` | Bổ sung |
| `self_study_hours` | **Thiếu** | `60` | Bổ sung |
| `course_description` | Bản ngắn | Bản đầy đủ 2 đoạn | Load bản đầy đủ |
| `main_parts` | 3 phần tiếng Việt | 3 phần tiếng Anh + tiếng Việt | Load cả hai |
| `learning_outcomes` | 16 entry | 4 LO chính + 12 LO chi tiết | Load đúng cấu trúc |
| `assessment` | **Thiếu** | 15/15/30/40% | Bổ sung |
| `exam_format` | Chỉ 60/90 phút | Open-book, written, 60/90 phút | Bổ sung |

Lưu ý: 16 entry LO hiện tại trùng số lượng với mẫu nhưng được viết lại/không
đầy đủ; phải lấy nguyên văn từ `course_info.txt`, không chép tay.

### 5.3 Chapters / topics

| Chương | Hard-code hiện tại | `topics.txt` | Thiếu |
|---|---|---|---|
| CH01 | 5 subtopic | 6 subtopic (1.1–1.6) | 1.6 Organization of NLU systems |
| CH02 | 6 | 6 | Đủ |
| CH03 | 6 | 9 (3.1, 3.1.1–3.1.5, 3.2, 3.3, 3.4) | grammar/sentence structure, good grammar, top-down chart |
| CH04 | 7 | 7 | Đủ |
| CH05 | 4 | 4 | Đủ |
| CH06 | 6 | 7 | 6.7 Simple context-dependent best-first parser |
| CH07 | 6 | 7 | 7.5 Verbs and states in logical form |
| CH08 | 5 | 7 | 8.6 Feature unification, 8.7 Generation from logical form |
| CH09 | 4 | 4 | Đủ |
| CH10 | 4 | 4 | Đủ |
| CH11 | 6 | 5 | Cần chuẩn hóa lại danh sách |
| CH12 | 6 | 7 | 12.5 Definite reference and sets |

Ngoài ra:

- `keywords` hiện tại thiếu một số alias như `WSD`, `semantic grammar`,
  `question answering`, `local discourse context`, `reference`, `anaphora`,
  `centering`.
- `summary` hiện tại là bản rút gọn, không phải nguyên văn.
- Không có trường `chapter_number` tách riêng; đang suy ra từ `CH01`.

### 5.4 Schedule

| Trường | Hard-code | `schedule.txt` | Hành động |
|---|---|---|---|
| 15 tuần | Có | Có | Load |
| `part` | **Không có** | Có | Bổ sung |
| `chapter` | Có, nhưng `WEEK_15=CH00` | `Chapter 1..12`, tuần 15 không chapter | Sửa |
| `topics` | Có, bản rút gọn | Đầy đủ | Load |
| `activity` | **Không có** | Tuần 5, 8 | Bổ sung |
| `milestone` | **Không có** | Tuần 8, 12, 15 | Bổ sung |

Công thức sinh `SCHEDULE` hiện tại là dead code vì mọi tuần đều bị override,
nhưng vẫn gây lỗi `CH00`. Phải xóa công thức và load trực tiếp.

### 5.5 Assignment

| Trường | Hard-code | `assignments.txt` | Hành động |
|---|---|---|---|
| `assignment_id` | `BTL01` | `BTL01` | Load |
| `title` | Có | Có | Load |
| `team_size` | `3-4 sinh viên` | `3-4 students` | Load, hiển thị tiếng Việt |
| `domain` | **Thiếu** | Có | Bổ sung |
| `goal` | Bản ngắn | Bản đầy đủ | Load |
| `parts` | 4 phần, chỉ name + description | 4 phần + requirements/outputs | Bổ sung |
| `PART I.requirements` | **Thiếu** | 5 mục | Bổ sung |
| `PART I.suggested_outputs` | **Thiếu** | 3 file | Bổ sung |
| `PART II.minimum_requirements` | **Thiếu** | 7 mục | Bổ sung |
| `PART II.suggested_intents` | **Thiếu** | 8 intent | Bổ sung |
| `PART III.optional_or_extension` | **Thiếu** | 4 mục | Bổ sung |
| `PART IV.requirements` | **Thiếu** | 4 mục | Bổ sung |
| `LLM/RAG EXTENSION` | Chỉ có trong regulations | status/description/not_required | Bổ sung |
| `deadlines` | 3 mốc | Không có trong assignments.txt (lấy từ schedule milestone) | Giữ, nhưng đánh dấu là dữ liệu mẫu |

Đây là lý do câu `BTL cần xuất những file gì?` hiện tại không thể trả lời đúng:
KB không có `suggested_outputs`.

### 5.6 Resources

| Hiện tại | `resources.txt` |
|---|---|
| 4 sách | 8 tài liệu (3 textbook + 5 reference) + study note |
| Thiếu | Lecture Slides Stanford (Jurafsky & Manning, 2016) |
| Thiếu | Xử lý ngôn ngữ tự nhiên (Phan Thị Tươi, 2012) |
| Thiếu | An Introduction to Machine Translation (Hutchins, 1992) |
| Thiếu | Natural Language Understanding and World Knowledge |
| Thiếu | `publisher`, `usage`, `study_note` |

Ngoài ra, cần map **topic → resource**:
- `CFG`, `PCFG`, `parsing` → Jurafsky & Martin, Manning & Schütze, slide Stanford.
- `Python` → Bird, Klein, Loper.
- `statistical NLP` → Manning & Schütze.
- `machine translation` → Hutchins.
- `Vietnamese NLP` → Phan Thị Tươi.

### 5.7 Regulations

| Hiện tại | `regulations.txt` |
|---|---|
| 5 mục | 8 mục |
| `attendance` | Có |
| `academic_integrity` | Có |
| `ai_usage` | Có (mẫu ghi `AI_usage`) |
| `llm_rag` | Có (mẫu ghi `LLM_RAG`) |
| `out_of_scope` | Có |
| **Thiếu** | `source_code` |
| **Thiếu** | `assignment_sharing` |
| **Thiếu** | `external_libraries` |

### 5.8 FAQ

| Hiện tại | `faq.txt` |
|---|---|
| 4 cặp | 15 cặp |
| `credits` | Q1 |
| `parts` | Q2 |
| `cfg_chapter` | Q3 |
| `llm_allowed` | Q12 |
| **Thiếu** | PCFG (Q4), Features (Q5), semantic grammar (Q6), knowledge representation (Q7), local discourse (Q8), LO4.2 (Q9), LO2.5 (Q10), LO3.3 (Q11), no-info (Q13), midterm (Q14), final (Q15) |

FAQ nên được dùng làm:
- fallback cho câu hỏi khớp gần đúng,
- nguồn câu trả lời chuẩn cho các câu hỏi phổ biến,
- test case cho Part 5.

### 5.9 Entities

`entities.txt` có 69 dòng, chia section:

```text
COURSE      CO3085, NLP, Natural Language Processing
PART        Part I/II/III + tên tiếng Anh
CHAPTERS    Chương 1..12
TOPICS      CFG, PCFG, Dependency Grammar, Features, Augmented Grammar,
            Unification, POS Tagging, Logical Form, Thematic Roles,
            Selectional Restriction, Semantic Network, WSD, Semantic Grammar,
            Knowledge Representation, Question Answering, Local Discourse Context,
            Reference, Anaphora, Centering
ASSIGNMENT  BTL01, Part I..IV
INTENTS     9 intent + UNKNOWN
```

Hiện tại `semantic.py` chỉ có 11 alias topic, thiếu ít nhất 8 alias quan trọng.

### 5.10 Dialogues / sample queries

- `dialogues.txt`: 5 kịch bản, mỗi kịch bản 2 lượt, có `EXPECTED_REFERENCE`.
- `sample_queries.txt`: 34 query, gồm 25 in-scope, 3 out-of-scope, 6 context.
- Hiện tại `dialogue.py` chỉ có 2 ví dụ; `evaluation.py` có 20 case; `main.py`
  có 6 lượt dialogue và 5 query evaluation riêng.

## 6. Lỗi Answer hiện tại — tái hiện và nguyên nhân

Chạy `CourseAssistant.process_query()` tại commit hiện tại cho kết quả:

| # | Query | Kết quả hiện tại | Kỳ vọng | Nguyên nhân gốc |
|---|---|---|---|---|
| 1 | `BTL cần xuất những file gì?` | `Bài tập lớn 'Intelligent Course Assistant' - Nhóm 3-4 sinh viên.` | `grammar.txt`, `samples.txt`, `parse-results.txt` (PART I); hoặc liệt kê output từng phần | Không có sub-intent `outputs`; `get_assignment_info()` mặc định trả title/team size; KB không có `suggested_outputs` |
| 2 | `Phần IV của BTL là gì?` | `Grammar and Parser: Xây dựng grammar và parser` | `Evaluation: tạo test set, đo metric, phân tích lỗi` | `get_assignment_info()` so khớp roman bằng substring: `'I' in 'PART_IV'` → PART_I |
| 3 | `Tài liệu về PCFG ở đâu?` | `Tài liệu tham khảo: 4 cuốn sách. Xem danh sách đầy đủ trong resources.txt` | Tài liệu cụ thể về PCFG/parsing (Jurafsky & Martin, Manning & Schütze, slide Stanford) | `topic_keywords` duyệt `cfg` trước `pcfg`, `'cfg' in 'pcfg'` → CFG; `get_resource()` chỉ tìm trong title |
| 4 | `Tuần 30 học gì?` | `Vui lòng cho biết tuần cụ thể.` | `Tuần 30 không nằm trong lịch 15 tuần của môn học.` | Không validate range; `get_schedule()` trả cùng một câu cho `None` và invalid |
| 5 | `Ai dạy môn NLP?` | `Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu môn học.` | Nếu dữ liệu không có giảng viên: thông báo rõ `Dữ liệu môn học không có thông tin giảng viên.` | `query()` không có nhánh `GET_INSTRUCTOR`; KB không có field instructor |
| 6 | `Chương nào học về semantic grammar?` | `Chương 07: Semantics and Logical Form trình bày về SEMANTIC.` | `Chương 10: Other Strategies for Semantic Interpretation` | Alias `SEMANTIC` khớp trước `SEMANTIC_GRAMMAR`; thiếu alias dài |
| 7 | `Chương nào học về knowledge representation?` | `Xin lỗi, tôi không tìm thấy thông tin này...` | `Chương 11: Knowledge Representation and Reasoning` | `semantic.py` thiếu alias `KNOWLEDGE_REPRESENTATION` |
| 8 | `PCFG được học ở đâu?` | `Chương 03: Grammar and Parsing trình bày về CFG.` | `PCFG` ở Chương 3 và Chương 6 | `'cfg' in 'pcfg'`; không trả nhiều chapter |
| 9 | `Chương 4 học vào tuần nào?` | `Chương 04 (...) được học vào Week 04.` | `... vào Tuần 04.` | Format tiếng Anh `Week` trong `get_chapter_week()` |
| 10 | `Nó có liên quan đến parsing không?` (sau `Chương 4 nói về gì?`) | Intent `GET_RULE`, trả toàn bộ quy định | `GET_TOPIC`, entity `CH04`, trả lời về parsing trong chương 4 | `process_dialogue()` không dùng `DialogueManager`; semantic thấy `không` → GET_RULE |
| 11 | `Phần này cần xuất file gì?` (sau `Bài tập lớn có phần parser không?`) | `Bài tập lớn ... Nhóm 3-4 sinh viên.` | `PART_I` + 3 output file | Không lưu `last_part`; không resolve `phần này`; KB thiếu output |
| 12 | `Tài liệu của phần này ở đâu?` (sau `Tuần 3 học gì?`) | `Tài liệu tham khảo: 4 cuốn sách...` | Tài liệu theo `WEEK_03`/`CH03` | Không lưu `last_week`; `phần này` không resolve |

Các lỗi phụ:

- `get_topic_chapter()` có thể trả sai chương khi topic là substring của keyword
  khác (ví dụ `parsing` vs `parsing with features`).
- `get_chapter_week()` chỉ trả tuần đầu tiên; CH04 học ở tuần 4 và 5 nhưng chỉ
  trả tuần 4.
- `get_schedule()` bỏ qua `activity`/`milestone`.
- `get_regulation()` bỏ sót 3 quy định.
- `FAQ` không được dùng.
- `get_learning_outcome("LO2")` trả LO2 chung, không liệt kê LO2.1–LO2.5.

## 7. Quyết định: có cần pipeline load dữ liệu?

### 7.1 Ba lựa chọn

| Lựa chọn | Mô tả | Ưu điểm | Nhược điểm | Kết luận |
|---|---|---|---|---|
| A. Mở rộng `course_data.txt` phẳng | Thêm section cho schedule, assignment, resource... vào một file INI | Ít file | Không biểu diễn được nested (chapter → subtopics, assignment → parts → outputs), khó validate, khó diff | **Không chọn** |
| B. Copy 11 file mẫu vào `data/`, viết loader riêng | Giữ định dạng text mẫu, parse từng file | Gần dữ liệu gốc, dễ đối chiếu, không cần dependency mới | Phải viết 8–10 parser nhỏ | **Chọn** |
| C. Convert sang JSON/YAML | Một file `kb.json` có schema | Typed, dễ load, dễ validate | Cần bước convert, khó sửa tay, trùng nguồn nếu vẫn giữ file text | Có thể dùng làm cache, không làm nguồn chính |

### 7.2 Khuyến nghị

**Chọn B + cache JSON tùy chọn.**

```text
data/                      <- nguồn chính, human-editable
  course_info.txt
  schedule.txt
  topics.txt
  assignments.txt
  resources.txt
  regulations.txt
  faq.txt
  entities.txt
  dialogues.txt
  sample_queries.txt
  README.md                <- nguồn gốc, cảnh báo dữ liệu mẫu
  .cache/kb.json           <- cache tùy chọn, có thể xóa
```

Lý do:

- Bộ mẫu đã có sẵn, không cần thiết kế lại schema từ đầu.
- Giữ được cấu trúc nested tự nhiên.
- Dễ so sánh với `BTL/NLP_Sample_Data` khi cần.
- Có thể thêm cache JSON để tăng tốc, nhưng **không** là nguồn sự thật.
- `data/course_data.txt` có thể giữ làm manifest/backward-compatible, nhưng
  không dùng làm nguồn chính.

### 7.3 Cảnh báo về nguồn dữ liệu

`00_README.txt` nói rõ:

> Một số thông tin phục vụ bài tập lớn như lịch 15 tuần, các mốc BTL, câu hỏi
> mẫu và quy định giả lập là DỮ LIỆU MẪU, không phải thông tin hành chính chính
> thức của học phần.

Vì vậy:

- Không trả lời như thể đó là thông tin chính thức.
- Trong `README.md`/`REPORT.md`, ghi rõ nguồn và tính chất mẫu.
- Nếu có dữ liệu chính thức, thay file text, không sửa code.

## 8. Thiết kế pipeline load dữ liệu

### 8.1 Kiến trúc module

```text
data/*.txt
   │
   ▼
src/data_loader.py
   ├── parse_course_info()
   ├── parse_schedule()
   ├── parse_topics()
   ├── parse_assignments()
   ├── parse_resources()
   ├── parse_regulations()
   ├── parse_faq()
   ├── parse_entities()
   ├── parse_dialogues()
   ├── parse_sample_queries()
   └── load_all(data_dir) -> KnowledgeBaseData
   │
   ▼
src/knowledge_base.py
   ├── KnowledgeBase(data: KnowledgeBaseData)
   ├── build_indexes()
   ├── query(intent, entities) -> Answer
   └── ...
   │
   ▼
src/main.py / src/semantic.py / src/evaluation.py
```

Không cần thư viện ngoài; chỉ dùng `re`, `unicodedata`, `dataclasses`, `pathlib`.

### 8.2 Schema nội bộ

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CourseInfo:
    course_id: str
    name: str
    name_en: str
    semester: str
    credits: int
    ects: int
    course_type: str
    department: str
    format: str
    total_course_hours: int
    lecture_hours: int
    major_assignment_hours: int
    self_study_hours: int
    description: str
    parts: list[str]
    learning_outcomes: dict[str, str]        # "LO1", "LO2.5", ...
    assessment: dict[str, str]
    exam_format: dict[str, str]

@dataclass
class Chapter:
    chapter_id: str          # CH01
    number: int              # 1
    name: str
    part: str
    keywords: list[str]
    summary: str
    subtopics: list[str]

@dataclass
class Week:
    week_id: str             # WEEK_01
    number: int
    part: str
    chapter: Optional[str]   # CH01..CH12, None cho tuần 15
    topics: list[str]
    activity: Optional[str] = None
    milestone: Optional[str] = None

@dataclass
class AssignmentPart:
    part_id: str             # PART_I
    name: str
    requirements: list[str] = field(default_factory=list)
    suggested_outputs: list[str] = field(default_factory=list)
    minimum_requirements: list[str] = field(default_factory=list)
    suggested_intents: list[str] = field(default_factory=list)
    optional_or_extension: list[str] = field(default_factory=list)

@dataclass
class Assignment:
    assignment_id: str
    title: str
    team_size: str
    domain: str
    goal: str
    parts: dict[str, AssignmentPart]
    deadlines: dict[str, str]

@dataclass
class Resource:
    resource_id: str         # R01
    kind: str                # TEXTBOOK | REFERENCE
    title: str
    author: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[int] = None
    usage: str = ""
    topics: list[str] = field(default_factory=list)

@dataclass
class Regulation:
    key: str                 # attendance, AI_usage, ...
    text: str

@dataclass
class FAQItem:
    faq_id: str              # Q1
    question: str
    answer: str

@dataclass
class EntityAlias:
    surface: str
    canonical: str
    entity_type: str         # COURSE | PART | CHAPTER | TOPIC | ASSIGNMENT | INTENT

@dataclass
class KnowledgeBaseData:
    course: CourseInfo
    chapters: dict[str, Chapter]
    weeks: dict[str, Week]
    assignment: Assignment
    resources: dict[str, Resource]
    regulations: dict[str, Regulation]
    faq: list[FAQItem]
    entities: list[EntityAlias]
    dialogues: list[dict]
    sample_queries: list[dict]
```

### 8.3 Loader: nguyên tắc parse

Không dùng `configparser` vì:

- nhiều section lặp (`TEXTBOOK 1`, `TEXTBOOK 2`),
- key lặp trong cùng section (`title`),
- value nhiều dòng,
- list item bắt đầu bằng `-`.

Dùng parser dòng + state machine:

```python
def parse_blocks(text: str) -> list[list[str]]:
    """Tách file thành các block cách nhau bởi dòng trống."""
    blocks, current = [], []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks
```

Mỗi parser chuyên biệt xử lý block của mình.

### 8.4 Parse từng file

#### `course_info.txt`

- Dòng đầu là tiêu đề, bỏ qua.
- `key: value` đơn giản.
- `course_description:` lấy các dòng tiếp theo đến khi gặp `Mục tiêu:`.
- `main_parts:` lấy các dòng `Part ...`.
- `learning_outcomes:` lấy các dòng `LO... - ...` (có thể xuống dòng).
- `detailed_learning_outcomes:` tương tự.
- `assessment:` lấy các dòng `key: value` con.
- `exam_format:` lấy các dòng `midterm: ...`, `final: ...`.

#### `schedule.txt`

- Block bắt đầu bằng `WEEK \d+`.
- `part:`, `chapter:`, `topics:` (list `-`), `activity:`, `milestone:`.
- Chuyển `Chapter 3` → `CH03`; tuần 15 không có chapter → `None`.
- Validate 1..15.

#### `topics.txt`

- Block bắt đầu bằng `CHAPTER \d+: TITLE`.
- `chapter_id`, `part`, `keywords` (split `,`), `summary` (multi-line),
  `subtopics` (list).
- Validate 12 chương, `chapter_id` khớp số.

#### `assignments.txt`

- Header: `assignment_id`, `title`, `team_size`, `domain`, `goal`.
- Block `PART I - ...` → `PART_I`; các key:
  `requirements`, `suggested_outputs`, `minimum_requirements`,
  `suggested_intents`, `optional_or_extension`.
- Block `LLM/RAG EXTENSION`: `status`, `description`, `not_required`.
- Deadline lấy từ `schedule.txt` milestone (nguồn duy nhất), không hard-code.

#### `resources.txt`

- Block `TEXTBOOK n` / `REFERENCE n`.
- `title`, `author`/`authors`, `publisher`, `year`, `usage`.
- `study_note` là block riêng.

#### `regulations.txt`

- Mỗi key (attendance, academic_integrity, AI_usage, source_code,
  assignment_sharing, external_libraries, LLM_RAG, OUT_OF_SCOPE) + value
  nhiều dòng.

#### `faq.txt`

- Block `Qn:` + `question:` + `answer:`.
- Answer có thể nhiều dòng.

#### `entities.txt`

- Section header in hoa: `COURSE`, `PART`, `CHAPTERS`, `TOPICS`, `ASSIGNMENT`,
  `INTENTS`.
- Dòng `alias = canonical` hoặc `alias` đơn (INTENTS).
- Chuẩn hóa alias lowercase, NFC.

#### `dialogues.txt` / `sample_queries.txt`

- Dùng cho Part 4/5, không bắt buộc cho KB query.
- `dialogues.txt`: block `DIALOGUE n`, `U1:`, `A1:`, `EXPECTED_REFERENCE`.
- `sample_queries.txt`: dòng `ID | QUERY | INTENT | ENTITY`.

### 8.5 Validation dữ liệu

Chạy trong `load_all()` (hoặc `--strict`):

| # | Kiểm tra | Lỗi nếu |
|---|---|---|
| 1 | File tồn tại | Thiếu file bắt buộc |
| 2 | Encoding UTF-8 | `UnicodeDecodeError` |
| 3 | Course có `course_id`, `name`, `credits` | Thiếu |
| 4 | Đúng 12 chương CH01..CH12 | Thiếu/thừa |
| 5 | Đúng 15 tuần WEEK_01..WEEK_15 | Thiếu/thừa |
| 6 | `week.chapter` thuộc chapters hoặc `None` | `CH00`, `CH13` |
| 7 | `chapter.part` thuộc `course.parts` | Sai part |
| 8 | `assignment.parts` có `PART_I..PART_IV`, không trùng | Thiếu/trùng |
| 9 | Mỗi LO trong dữ liệu có ID duy nhất | Trùng |
| 10 | Mỗi resource có `title` | Thiếu |
| 11 | Mỗi FAQ có `question` + `answer` | Thiếu |
| 12 | Mỗi alias trỏ tới canonical tồn tại | Alias mồ côi |
| 13 | Không có key trùng trong cùng file | Trùng |
| 14 | `schedule` milestone khớp deadline | Lệch |

Loader phải **fail fast** với thông báo:

```text
[data_loader] schedule.txt: WEEK_15 chapter 'CH00' không tồn tại trong topics.txt
```

Không silent fallback.

### 8.6 Index xây sau khi load

```python
class KnowledgeIndex:
    chapter_by_id: dict[str, Chapter]
    week_by_id: dict[str, Week]
    chapter_by_week: dict[str, str | None]
    weeks_by_chapter: dict[str, list[str]]
    topic_to_chapters: dict[str, list[tuple[str, float]]]
    keyword_to_chapters: dict[str, list[str]]
    lo_by_id: dict[str, str]
    part_by_id: dict[str, AssignmentPart]
    resource_by_id: dict[str, Resource]
    resource_by_topic: dict[str, list[str]]
    regulation_by_key: dict[str, Regulation]
    faq_by_norm: dict[str, FAQItem]
    alias_to_entity: dict[str, EntityAlias]
```

Quy tắc scoring cho topic:

| Nguồn khớp | Điểm |
|---|---:|
| Alias chính xác (dài nhất) | 1.0 |
| Keyword chính xác | 0.8 |
| Tên chương | 0.6 |
| Subtopics | 0.5 |
| Substring | 0.3 |

- Ưu tiên alias dài nhất: `semantic grammar` (1.0) thắng `semantic` (0.3).
- Nếu nhiều chương cùng điểm cao (PCFG ở CH03 và CH06), trả **tất cả** kèm
  giải thích, không chọn bừa.
- Không dùng `if topic in keyword`; dùng token/word boundary.

### 8.7 Query layer

Đổi `KnowledgeBase.query()` trả về object:

```python
@dataclass
class Answer:
    status: str          # OK | NOT_FOUND | OUT_OF_SCOPE | INVALID_VALUE | AMBIGUOUS | NEEDS_CLARIFICATION
    text: str
    intent: str
    entities: dict
    evidence: list[str]  # ["data/topics.txt#CH03", ...]
```

Giữ wrapper tương thích:

```python
def query_text(self, intent, entities) -> str:
    return self.query(intent, entities).text
```

#### `GET_COURSE_INFO`

Sub-attribute:

| Attribute | Nguồn | Ví dụ trả lời |
|---|---|---|
| `credits` | `course.credits` | `Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ.` |
| `ects` | `course.ects` | `Môn học có 6 ECTS.` |
| `parts` | `course.parts` | `Môn học gồm 3 phần chính: ...` |
| `description` | `course.description` | Đoạn mô tả đầy đủ |
| `objectives` | `course.description` phần Mục tiêu | `Mục tiêu: ...` |
| `assessment` | `course.assessment` | `Đánh giá: ...` |
| `exam_format` | `course.exam_format` | `Midterm: open-book, 60 phút; Final: open-book, 90 phút.` |
| `hours` | 4 trường hours | `Tổng 150 giờ: 30 lecture, 45 BTL, 60 tự học.` |
| `course_type` | `course.course_type` | `Loại môn: ...` |
| `department` | `course.department` | `Khoa: ...` |
| `semester` | `course.semester` | `Học kỳ: HK261.` |

#### `GET_SCHEDULE`

- `week`:
  - 1..15 → trả part, chapter, topics, activity, milestone.
  - ngoài range → `INVALID_VALUE`, message rõ.
- `chapter`:
  - trả **tất cả** tuần chứa chapter (CH04 → tuần 4, 5).
- `topic`:
  - tìm chapter chứa topic → tuần tương ứng; nếu nhiều, liệt kê.
- Không có entity:
  - trả tổng quan 15 tuần hoặc hỏi lại, không trả “Vui lòng cho biết tuần cụ thể”
    một cách máy móc.

#### `GET_TOPIC`

- `chapter`:
  - trả tên, part, summary, subtopics.
- `topic`:
  - trả tất cả chapter khớp, ví dụ PCFG:
    `PCFG được trình bày trong Chương 3 và tiếp tục ở Chương 6.`
  - `SEMANTIC_GRAMMAR` → CH10.
  - `KNOWLEDGE_REPRESENTATION` → CH11.
  - `QUESTION_ANSWERING` → CH11 (và CH08 nếu có).
  - `REFERENCE`/`ANAPHORA`/`CENTERING` → CH12.
- Không tìm thấy → `NOT_FOUND` với tên topic.

#### `GET_ASSIGNMENT`

Phân biệt sub-intent:

| Sub-intent | Dấu hiệu | Trả lời |
|---|---|---|
| `overview` | “bài tập lớn yêu cầu gì”, “BTL là gì” | goal + 4 phần |
| `parts` | “gồm những phần nào” | danh sách 4 phần |
| `part_detail` | “Phần I là gì” | requirements + outputs của phần |
| `outputs` | “cần xuất file gì”, “output” | suggested_outputs của phần hoặc tất cả |
| `requirements` | “yêu cầu” | requirements/minimum_requirements |
| `team_size` | “nhóm mấy người” | team_size |
| `deadline` | “khi nào nộp” | deadlines (từ schedule milestone) |

Ví dụ:

```text
Q: BTL cần xuất những file gì?
A: Phần I cần xuất: output/grammar.txt, output/samples.txt,
   output/parse-results.txt. Phần II cần semantic.txt, intent-entity.txt,
   query.txt, answer.txt. Phần IV cần evaluation.txt.
```

#### `GET_DEADLINE`

- Trả 3 mốc từ `assignment.deadlines`, lấy từ `schedule` milestone:
  - Checkpoint 1: Tuần 8 — grammar and parser.
  - Checkpoint 2: Tuần 12 — semantic interpretation and QA.
  - Final: Tuần 15 — submission and demo.
- Ghi rõ đây là dữ liệu mẫu nếu cần.

#### `GET_RESOURCE`

- `topic` → `resource_by_topic`; trả title, author, year, usage.
- Không có topic → liệt kê đủ 8 tài liệu + study note.
- Không tìm thấy topic → `NOT_FOUND` + gợi ý các topic có tài liệu.

#### `GET_RULE`

- Map key:
  - `attendance`, `academic_integrity`, `AI_usage`, `source_code`,
    `assignment_sharing`, `external_libraries`, `LLM_RAG`, `OUT_OF_SCOPE`.
- Alias:
  - “AI”, “LLM”, “RAG” → `AI_usage`/`LLM_RAG`.
  - “copy”, “chia sẻ” → `assignment_sharing`.
  - “thư viện” → `external_libraries`.
  - “giải thích code” → `source_code`.
- Không có key → liệt kê các quy định có hoặc `NOT_FOUND`.

#### `GET_LO`

- `LO2.5` → đúng entry.
- `LO2` → liệt kê LO2.1–LO2.5 hoặc nói rõ là LO cấp chính.
- `LO4.3` → `NOT_FOUND` (không tự bịa).
- `LO4.2` → nội dung + chương liên quan (CH12) nếu có mapping.

#### `GET_INSTRUCTOR`

- Nếu `course.instructor` có dữ liệu → trả.
- Nếu không → `NOT_FOUND` với message:
  `Dữ liệu môn học hiện không có thông tin giảng viên.`
- Không trả generic “không tìm thấy thông tin này” mà không nói rõ.

#### `UNKNOWN` / out-of-scope

- `OUT_OF_SCOPE`:
  `Câu hỏi này nằm ngoài phạm vi môn học CO3085.`
- Không cố gắng trả lời bằng KB.

### 8.8 Chính sách “không có thông tin” nhất quán

| Tình huống | Status | Message mẫu |
|---|---|---|
| Câu ngoài miền | `OUT_OF_SCOPE` | `Câu hỏi này nằm ngoài phạm vi môn học CO3085.` |
| Intent đúng, entity không có trong KB | `NOT_FOUND` | `Tôi không tìm thấy thông tin về <X> trong dữ liệu môn học.` |
| Entity có nhưng giá trị sai range | `INVALID_VALUE` | `Tuần 30 không nằm trong lịch 15 tuần của môn học.` |
| Nhiều kết quả cùng khớp | `AMBIGUOUS` | `Có nhiều chương liên quan: Chương 3 và Chương 6. Bạn muốn xem chương nào?` |
| Thiếu ngữ cảnh | `NEEDS_CLARIFICATION` | `Bạn đang nói đến chương/tuần/phần nào?` |
| Dữ liệu không có field (giảng viên) | `NOT_FOUND` | `Dữ liệu môn học hiện không có thông tin giảng viên.` |

Quy tắc:

1. Không dùng cùng một câu cho mọi trường hợp.
2. Không tự tạo thông tin.
3. Không trả lời “Vui lòng cho biết tuần cụ thể” khi đã có `week`.
4. Luôn ghi `status` để evaluation chấm được.
5. Luôn có `evidence` nếu `status == OK`.

### 8.9 Answer generation

Tách khỏi `KnowledgeBase.query()` nếu muốn:

```python
class AnswerGenerator:
    def generate(self, intent, entities, data) -> Answer:
        ...
```

Nhưng với quy mô hiện tại, đặt trong `knowledge_base.py` là đủ. Điều quan trọng
là **mọi câu trả lời đều có template + dữ liệu**, không nối chuỗi tùy tiện.

## 9. Mapping current → new data source

| Thành phần hiện tại | Thay bằng |
|---|---|
| `COURSE_INFO` | `data/course_info.txt` → `CourseInfo` |
| `CHAPTERS` | `data/topics.txt` → `dict[str, Chapter]` |
| `SCHEDULE` | `data/schedule.txt` → `dict[str, Week]` |
| `ASSIGNMENT` | `data/assignments.txt` + milestone từ `schedule.txt` |
| `RESOURCES` | `data/resources.txt` |
| `REGULATIONS` | `data/regulations.txt` |
| `FAQ` | `data/faq.txt` |
| Alias topic trong `semantic.py` | `data/entities.txt` |
| Chapter/week/LO terminal trong `grammar.py` | sinh từ KB |
| 20 test case trong `evaluation.py` | `data/sample_queries.txt` + test set mới (Part 5) |
| 2 dialogue mẫu trong `dialogue.py` | `data/dialogues.txt` (Part 4) |

## 10. Kế hoạch migration

| Bước | Việc làm | Kết quả | Ước lượng |
|---|---|---|---|
| 1 | Copy 11 file mẫu vào `data/`, thêm `data/README.md` ghi nguồn | Dữ liệu sẵn | 0.5 ngày |
| 2 | Viết `src/data_loader.py` + dataclass schema | Load được | 1–1.5 ngày |
| 3 | Viết validation + test loader | Dữ liệu sạch | 1 ngày |
| 4 | Refactor `KnowledgeBase` dùng `KnowledgeBaseData` | Bỏ global | 1 ngày |
| 5 | Xây index + sửa `get_topic_chapter`, `get_resource`, `get_assignment_info` | Hết lỗi PCFG/Part IV | 1 ngày |
| 6 | Cập nhật `semantic.py` dùng alias từ `entities.txt` | Entity đúng | 0.5–1 ngày |
| 7 | Cập nhật `grammar.py` lấy terminal từ KB | Grammar khớp dữ liệu | 0.5 ngày |
| 8 | Sửa `main.py`, `evaluation.py`, `dialogue.py` dùng API mới | Tích hợp | 0.5–1 ngày |
| 9 | Sinh lại outputs, cập nhật README/REPORT | Hoàn chỉnh | 0.5 ngày |

Tổng: **4–6 ngày**.

## 11. Test plan

### 11.1 Loader tests

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | Load đủ 11 file | Không lỗi |
| 2 | `len(chapters) == 12` | Đúng |
| 3 | `len(weeks) == 15` | Đúng |
| 4 | `weeks["WEEK_15"].chapter is None` | Đúng |
| 5 | `len(resources) == 8` | Đúng |
| 6 | `len(regulations) == 8` | Đúng |
| 7 | `len(faq) == 15` | Đúng |
| 8 | `len(assignment.parts) == 4` | Đúng |
| 9 | `assignment.parts["PART_I"].suggested_outputs == [...]` | Đúng 3 file |
| 10 | `learning_outcomes["LO2.5"]` tồn tại | Đúng |
| 11 | File thiếu → raise lỗi rõ | Đúng |
| 12 | `WEEK_15=CH00` → raise lỗi | Đúng |

### 11.2 KB query tests

| # | Query | Kỳ vọng |
|---|---|---|
| 1 | `Môn NLP có bao nhiêu tín chỉ?` | `3 tín chỉ`, status OK |
| 2 | `CO3085 có mấy tín chỉ?` | `3 tín chỉ` |
| 3 | `Môn học gồm những phần nào?` | 3 phần |
| 4 | `Môn học được đánh giá như thế nào?` | 15/15/30/40% |
| 5 | `Midterm bao nhiêu phút?` | 60 phút, open-book |
| 6 | `Final bao nhiêu phút?` | 90 phút, open-book |
| 7 | `Tuần 3 học gì?` | CH03 + topics |
| 8 | `Chương 4 học vào tuần nào?` | Tuần 04 và 05 |
| 9 | `Chương nào học về CFG?` | CH03 |
| 10 | `PCFG được học ở đâu?` | CH03 + CH06 |
| 11 | `Chương nào học về semantic grammar?` | CH10 |
| 12 | `Chương nào học về knowledge representation?` | CH11 |
| 13 | `Chương nào học về reference?` | CH12 |
| 14 | `BTL cần xuất những file gì?` | 3 file PART I + các file PART II/IV |
| 15 | `Phần IV của BTL là gì?` | Evaluation |
| 16 | `Phần I của BTL là gì?` | Grammar and Parser + requirements |
| 17 | `Bài tập lớn yêu cầu gì?` | goal + 4 phần |
| 18 | `Deadline BTL là khi nào?` | 3 mốc |
| 19 | `Tài liệu về PCFG ở đâu?` | tài liệu cụ thể |
| 20 | `Có bao nhiêu tài liệu tham khảo?` | 8 |
| 21 | `Có được dùng LLM/RAG không?` | LLM_RAG |
| 22 | `Quy định về source code là gì?` | source_code |
| 23 | `Có được chia sẻ bài làm không?` | assignment_sharing |
| 24 | `L.O.2.5 là gì?` | đúng nội dung |
| 25 | `L.O.4.2 liên quan đến gì?` | local discourse context + CH12 |
| 26 | `L.O.4.3 là gì?` | NOT_FOUND |
| 27 | `Tuần 30 học gì?` | INVALID_VALUE |
| 28 | `Chương 15 nói về gì?` | INVALID_VALUE |
| 29 | `Ai dạy môn NLP?` | NOT_FOUND với message giảng viên |
| 30 | `Hôm nay thời tiết thế nào?` | OUT_OF_SCOPE |

### 11.3 Snapshot tests

- Lưu `output/answer.txt` mới và so sánh với baseline đã duyệt.
- Mỗi thay đổi dữ liệu phải làm snapshot đổi có chủ đích.

## 12. Acceptance criteria

- [ ] `src/knowledge_base.py` không còn nội dung môn học hard-code (chỉ còn
      class/method/template).
- [ ] `data/` có đủ 11 file mẫu (hoặc file tương đương) và `data/README.md`.
- [ ] `KnowledgeBase()` load dữ liệu từ `data/`, không import global.
- [ ] `PCFG` trả về CFG + CH03/CH06, không còn chỉ CFG.
- [ ] `Phần IV` trả về PART_IV.
- [ ] `BTL cần xuất những file gì?` trả về đúng danh sách output.
- [ ] `Tài liệu về PCFG ở đâu?` trả về tài liệu cụ thể.
- [ ] `Tuần 30` trả `INVALID_VALUE`, không trả “Vui lòng cho biết tuần cụ thể”.
- [ ] `Ai dạy môn NLP?` trả `NOT_FOUND` với message rõ về giảng viên.
- [ ] `semantic grammar` → CH10, `knowledge representation` → CH11.
- [ ] `GET_INSTRUCTOR` có nhánh xử lý (dù dữ liệu chưa có).
- [ ] Mọi câu trả lời có `status` và `evidence`.
- [ ] Loader validation fail fast với dữ liệu sai.
- [ ] `pytest tests/test_data_loader.py tests/test_knowledge_base.py` pass.
- [ ] `output/answer.txt`, `query.txt`, `semantic.txt`, `intent-entity.txt`
      được sinh lại từ code.

## 13. Rủi ro và lưu ý

- **Dữ liệu mẫu không phải chính thức:** ghi rõ trong README/REPORT; không
  khẳng định đó là thông tin hành chính.
- **Parse text dễ vỡ:** mỗi file có format khác nhau; cần test với file thật,
  không chỉ file mẫu.
- **Alias trùng:** `CFG` là substring của `PCFG`; `semantic` là substring của
  `semantic grammar`. Luôn dùng longest-match + word boundary.
- **Nhiều kết quả:** PCFG ở 2 chương; không chọn bừa một chương.
- **Dữ liệu thiếu field:** `GET_INSTRUCTOR` không có dữ liệu; phải nói rõ thay
  vì bịa hoặc trả generic.
- **Deadline trùng nguồn:** deadline lấy từ milestone của schedule; không
  hard-code thêm trong assignment.
- **Cache JSON cũ:** nếu dùng cache, phải invalidate theo mtime hoặc xóa khi
  build.
- **Không trả lời bằng `FAQ` máy móc:** FAQ là fallback, không thay thế query
  có cấu trúc.

## 14. Phụ lục — checklist dữ liệu cần copy

```text
data/
├── 00_README.txt          (hoặc README.md)
├── course_info.txt
├── schedule.txt
├── topics.txt
├── assignments.txt
├── resources.txt
├── regulations.txt
├── faq.txt
├── entities.txt
├── dialogues.txt
└── sample_queries.txt
```

Nguồn:

```text
D:\_HCMUT\_Nam4\k261\CO3085-Natual-Lannguage-Processing\BTL\NLP_Sample_Data\
```

Sau khi copy, chạy:

```bash
python -c "from src.data_loader import load_all; d = load_all('data'); print(len(d.chapters), len(d.weeks), len(d.resources), len(d.faq))"
```

Kỳ vọng:

```text
12 15 8 15
```
