# PART 5 — Đánh giá hệ thống (Evaluation)

## 1. Mục tiêu

Sau bước này:

1. Có **test set 100 case** (khoảng 50–100 theo yêu cầu), phủ đủ 9 intent,
   no-info, invalid value, out-of-scope và context-dependent.
2. Mỗi case có **tiêu chí chấm answer**, không chỉ intent/entity.
3. Evaluation chấm được **status** (`OK`, `NOT_FOUND`, `INVALID_VALUE`,
   `OUT_OF_SCOPE`, `AMBIGUOUS`, `NEEDS_CLARIFICATION`) — đây là thứ phân biệt
   “không có thông tin” với “trả lời sai”.
4. Entity được chấm bằng **precision / recall / F1**, không phải substring trên
   `str(dict)`.
5. Có **context suite** chạy qua `DialogueManager`, chấm cả việc resolve tham
   chiếu (`chương này` → `CH03`) chứ không chỉ câu trả lời cuối.
6. Báo cáo có **error analysis thật**: query, expected, predicted, status,
   root cause, file/rule gây lỗi.
7. `output/evaluation.txt` và `output/evaluation.json` sinh từ **một** runner,
   không còn 5-case report riêng trong `main.save_outputs()`.
8. Kết quả tái lập được: cùng test set + cùng code → cùng số liệu.

## 2. Phạm vi file

| File | Vai trò |
|---|---|
| `data/test_cases.jsonl` (mới) | 100 case, nguồn sự thật |
| `src/evaluation.py` | Runner, metric, report |
| `src/main.py` | Bỏ report 5 case ad-hoc trong `save_outputs()` |
| `output/evaluation.txt` | Report cho người đọc |
| `output/evaluation.json` | Report máy đọc, dùng cho CI/regression |
| `docs/REPORT.md` | Trích số liệu từ report, không chép tay |
| `tests/test_evaluation.py` (mới) | Test metric + runner |

## 3. Hiện trạng

`src/evaluation.py` tại commit `883e0c6`:

- `DEFAULT_TEST_CASES`: 20 case.
  - 17 in-scope.
  - 3 out-of-scope.
- Không có case no-info (tuần 30, chương 15, LO4.3).
- Không có case context-dependent chạy qua dialogue.
- `output/evaluation.txt`:

```text
Total test cases: 20
In-scope tests: 17
Out-of-scope tests: 3

Intent Accuracy: 100.00% (20/20)
Entity Accuracy: 100.00% (20/20)
Answer Accuracy: 15.00% (3/20)
Out-of-Scope Detection: 100.00%
```

Ba con số 100% và 15% này **không phản ánh chất lượng hệ thống**. Chúng là hệ
quả của lỗi harness bên dưới.

## 4. Lỗi gốc của evaluation hiện tại

| # | Vị trí | Lỗi | Hệ quả |
|---|---|---|---|
| E1 | `evaluation.py:142` | `answer_correct = False` mặc định; chỉ tính khi có `expected_answer_contains` | 17/20 case in-scope **luôn** bị tính sai answer. 15% = 3/20 chỉ là 3 case OOS. Đây là lỗi harness, không phải lỗi hệ thống |
| E2 | `DEFAULT_TEST_CASES` | Không case nào có `answer_contains` | Answer accuracy không đo gì cả |
| E3 | `evaluation.py:139` | `expected_entity in str(result['entities'])` | Substring trên repr dict: `"CFG" in "{'topic': 'PCFG'}"` → đúng dù entity sai. `"CH04" in ...` cũng có thể khớp nhầm |
| E4 | `TestCase` | Chỉ 1 `expected_entity` dạng chuỗi | Không chấm được multi-entity (`week=WEEK_03` + `chapter=CH03`) |
| E5 | `evaluate()` | Không chấm status | Không phân biệt `NOT_FOUND` với `INVALID_VALUE`; mọi “không tìm thấy” đều được coi là đúng cho OOS |
| E6 | `out_of_scope_accuracy` | Chỉ đếm `predicted_intent == "UNKNOWN"` | Bỏ qua trường hợp intent đúng nhưng answer sai; không có precision/recall OOS |
| E7 | `load_test_cases_from_file` | Parse format `ID | QUERY | INTENT | ENTITY`, không có status/answer/context | Không dùng được cho test set mới |
| E8 | `evaluate()` | Luôn gọi `process_query()`, không bao giờ gọi `process_dialogue()` | Không test Part 4 |
| E9 | `save_report("output/evaluation.txt")` | Đường dẫn tương đối | Chạy từ thư mục khác sẽ ghi sai chỗ hoặc lỗi |
| E10 | `main.save_outputs()` | Tự chạy 5 query và ghi report riêng | Hai nguồn số liệu: `evaluation.py` (20 case) và `main.py` (5 case) |
| E11 | `generate_report()` | In “Limitations” cố định | Không dựa trên lỗi thật |
| E12 | `run_evaluation()` | `print()` có thể lỗi `UnicodeEncodeError` trên Windows | Đã gặp khi chạy `--mode demo`; cần `PYTHONIOENCODING=utf-8` hoặc ghi file trước |

## 5. Nguyên tắc thiết kế test set

1. **Mỗi case có một “đáp án đúng” kiểm chứng được** từ `data/` (Part 3), không
   dựa vào cảm nhận.
2. **Tách loại câu hỏi.** Không trộn “hệ thống không biết” với “hệ thống trả lời
   sai”. Status là một chiều đánh giá riêng.
3. **Không lấy câu sinh tự động làm test set.** Test set viết tay, đa dạng cách
   diễn đạt, không trùng template trong `samples.txt`.
4. **Có case khó.** Alias dài (`semantic grammar` vs `semantic`), substring
   (`PCFG` vs `CFG`), nhiều kết quả (PCFG ở CH03 + CH06), giá trị ngoài range.
5. **Có case hội thoại.** Ít nhất 5 kịch bản mẫu + case clarification.
6. **Có case out-of-scope** để đo false positive của KB.
7. **Cân bằng theo intent**, không để `GET_TOPIC` chiếm 80% test set.
8. **Mỗi case có `notes`** giải thích vì sao đáp án đúng — người chấm sau đọc
   được.

## 6. Thành phần 100 test case

### 6.1 Tổng quan

| Nhóm | Số case | Mục đích |
|---|---:|---|
| A. Single-turn in-scope | 70 | Chấm intent + entity + answer |
| B. No-info / invalid value | 8 | Chấm status, không chấm “đoán bừa” |
| C. Out-of-scope | 6 | Chấm OOS precision/recall |
| D. Context-dependent | 16 | Chấm resolve + answer qua dialogue |
| **Tổng** | **100** | |

### 6.2 A. Single-turn in-scope (70)

| Intent | Số case | Nội dung |
|---|---:|---|
| `GET_COURSE_INFO` | 10 | credits, ECTS, parts, description, objectives, assessment, exam format, hours, course type, semester |
| `GET_SCHEDULE` | 10 | tuần 1–15, chương → tuần, tuần → chương, tuần có activity/milestone |
| `GET_TOPIC` | 14 | 12 chương + alias khó (`semantic grammar`, `knowledge representation`, `reference`, `question answering`) |
| `GET_ASSIGNMENT` | 10 | overview, 4 phần, requirements, outputs, team size, LLM/RAG extension |
| `GET_DEADLINE` | 5 | 3 mốc + cách hỏi khác |
| `GET_RESOURCE` | 7 | 8 tài liệu, topic → resource, study note |
| `GET_RULE` | 7 | 8 quy định, alias (`AI`, `copy`, `thư viện`, `giải thích code`) |
| `GET_LO` | 7 | LO cấp 1, LO cấp 2, LO4.2 → CH12 |
| **Tổng** | **70** | |

Phân bổ chi tiết đề xuất:

#### Course info (10)

| ID | Query | Expected |
|---|---|---|
| C01 | `Môn NLP có bao nhiêu tín chỉ?` | 3 tín chỉ |
| C02 | `CO3085 có mấy tín chỉ?` | 3 tín chỉ |
| C03 | `Môn học có bao nhiêu ECTS?` | 6 ECTS |
| C04 | `Môn học gồm những phần nào?` | 3 phần: Syntactic, Semantic, Context |
| C05 | `Mô tả ngắn về môn NLP.` | description |
| C06 | `Mục tiêu của môn học là gì?` | objectives |
| C07 | `Môn học được đánh giá như thế nào?` | 15/15/30/40% |
| C08 | `Midterm bao nhiêu phút?` | 60 phút, open-book |
| C09 | `Final bao nhiêu phút?` | 90 phút, open-book |
| C10 | `Môn học có bao nhiêu giờ tự học?` | 60 giờ |

#### Schedule (10)

| ID | Query | Expected |
|---|---|---|
| S01 | `Tuần 1 học gì?` | CH01 |
| S02 | `Tuần 3 học gì?` | CH03 + CFG/PCFG/parsing |
| S03 | `Tuần 5 có hoạt động gì?` | activity của tuần 5 |
| S04 | `Tuần 8 có mốc nào?` | milestone checkpoint 1 |
| S05 | `Chương 4 học vào tuần nào?` | tuần 4 **và** 5 |
| S06 | `Chương 12 học tuần nào?` | tuần 14/15 |
| S07 | `Tuần 15 học gì?` | không có chapter mới, có milestone final |
| S08 | `Học phần Syntactic Processing kéo dài mấy tuần?` | khoảng tuần 2–6 |
| S09 | `Tuần 3 có những chủ đề gì?` | 8 topic của CH03 |
| S10 | `Lịch học có bao nhiêu tuần?` | 15 tuần |

#### Topic (14)

| ID | Query | Expected |
|---|---|---|
| T01 | `Chương 1 nói về gì?` | Introduction to NLP |
| T02 | `Chương 4 nói về gì?` | Features and Augmented Grammar |
| T03 | `Chương nào học về CFG?` | CH03 |
| T04 | `PCFG được học ở đâu?` | CH03 **và** CH06 |
| T05 | `Chương nào học về semantic grammar?` | CH10 (không phải CH07) |
| T06 | `Chương nào học về knowledge representation?` | CH11 |
| T07 | `Chương nào học về reference?` | CH12 |
| T08 | `Chương nào học về question answering?` | CH11 |
| T09 | `Chương nào học về selectional restriction?` | CH07/CH08 |
| T10 | `Chương 10 có những phương pháp gì?` | 4 subtopic |
| T11 | `Chương 11 có liên quan đến hỏi đáp không?` | Có, procedural semantics + QA |
| T12 | `Chương 12 nói về gì?` | Discourse Context |
| T13 | `Unification được học ở chương nào?` | CH08 |
| T14 | `Chương nào học về POS tagging?` | CH05/CH06 |

#### Assignment (10)

| ID | Query | Expected |
|---|---|---|
| A01 | `Bài tập lớn yêu cầu xây dựng những gì?` | goal + 4 phần |
| A02 | `BTL gồm những phần nào?` | PART_I..PART_IV |
| A03 | `Phần I của bài tập lớn là gì?` | Grammar and Parser |
| A04 | `Phần IV của bài tập lớn là gì?` | Evaluation (không phải PART_I) |
| A05 | `BTL cần xuất những file gì?` | grammar.txt, samples.txt, parse-results.txt, semantic.txt, intent-entity.txt, query.txt, answer.txt, evaluation.txt |
| A06 | `Phần I cần xuất file gì?` | 3 file của PART I |
| A07 | `Bài tập lớn có phần hỏi đáp không?` | Có, PART_II |
| A08 | `Bài tập lớn làm theo nhóm mấy người?` | 3–4 sinh viên |
| A09 | `Phần II có yêu cầu tối thiểu gì?` | semantic representation, intent, entity, query→answer |
| A10 | `LLM/RAG có bắt buộc không?` | Không bắt buộc, chỉ mở rộng |

#### Deadline (5)

| ID | Query | Expected |
|---|---|---|
| D01 | `Deadline BTL là khi nào?` | 3 mốc |
| D02 | `Khi nào nộp checkpoint 1?` | tuần 8 |
| D03 | `Checkpoint 2 nộp khi nào?` | tuần 12 |
| D04 | `Final nộp khi nào?` | tuần 15 |
| D05 | `Thời hạn nộp bài tập lớn?` | 3 mốc, ghi rõ dữ liệu mẫu |

#### Resource (7)

| ID | Query | Expected |
|---|---|---|
| R01 | `Có bao nhiêu tài liệu tham khảo?` | 8 |
| R02 | `Tài liệu về PCFG ở đâu?` | Jurafsky & Martin, Manning & Schütze, slide Stanford |
| R03 | `Tài liệu tham khảo về statistical NLP là gì?` | Manning & Schütze |
| R04 | `Tài liệu nào liên quan đến Python NLP?` | Bird, Klein, Loper |
| R05 | `Sách tiếng Việt về NLP là gì?` | Phan Thị Tươi, 2012 |
| R06 | `Tài liệu về machine translation?` | Hutchins, 1992 |
| R07 | `Study note nói gì?` | nội dung study note |

#### Rule (7)

| ID | Query | Expected |
|---|---|---|
| U01 | `Có được dùng LLM/RAG không?` | LLM_RAG |
| U02 | `Quy định về sử dụng AI là gì?` | AI_usage |
| U03 | `Có được chia sẻ bài làm không?` | assignment_sharing: không |
| U04 | `Có được dùng thư viện ngoài không?` | external_libraries |
| U05 | `Quy định về source code là gì?` | source_code |
| U06 | `Quy định về liêm chính học thuật?` | academic_integrity |
| U07 | `Có phải tham dự đầy đủ không?` | attendance |

#### LO (7)

| ID | Query | Expected |
|---|---|---|
| L01 | `L.O.2.5 là gì?` | nội dung LO2.5 |
| L02 | `L.O.4.2 liên quan đến nội dung nào?` | local discourse context + CH12 |
| L03 | `L.O.3.3 là gì?` | nội dung LO3.3 |
| L04 | `LO2 gồm những mục nào?` | LO2.1–LO2.5 |
| L05 | `L.O.1.1 là gì?` | nội dung LO1.1 |
| L06 | `L.O.4.1 là gì?` | nội dung LO4.1 |
| L07 | `Môn học có bao nhiêu learning outcome?` | 4 LO chính / 16 entry |

### 6.3 B. No-info / invalid value (8)

| ID | Query | Expected status | Expected answer |
|---|---|---|---|
| N01 | `Tuần 30 học gì?` | `INVALID_VALUE` | “Tuần 30 không nằm trong lịch 15 tuần…” |
| N02 | `Tuần 0 học gì?` | `INVALID_VALUE` | tương tự |
| N03 | `Chương 15 nói về gì?` | `INVALID_VALUE` | “Chương 15 không tồn tại…” |
| N04 | `Chương 0 nói về gì?` | `INVALID_VALUE` | tương tự |
| N05 | `L.O.4.3 là gì?` | `NOT_FOUND` | “Không có LO4.3 trong dữ liệu…” |
| N06 | `L.O.5.1 là gì?` | `NOT_FOUND` | tương tự |
| N07 | `Chương nào học về quantum computing?` | `NOT_FOUND` | “Không tìm thấy topic…” + gợi ý |
| N08 | `Ai dạy môn NLP?` | `NOT_FOUND` | “Dữ liệu môn học hiện không có thông tin giảng viên.” |

Lưu ý: N01–N04 **không** được trả cùng một câu “Vui lòng cho biết tuần cụ thể”
như hiện tại. Đã có `week=WEEK_30` thì phải nói rõ ngoài range.

### 6.4 C. Out-of-scope (6)

| ID | Query | Expected status |
|---|---|---|
| O01 | `Hôm nay thời tiết thế nào?` | `OUT_OF_SCOPE` |
| O02 | `Ai là tổng thống Pháp?` | `OUT_OF_SCOPE` |
| O03 | `Giải bài toán xác suất này giúp tôi.` | `OUT_OF_SCOPE` |
| O04 | `Dịch câu này sang tiếng Anh.` | `OUT_OF_SCOPE` |
| O05 | `Viết code Python cho tôi.` | `OUT_OF_SCOPE` |
| O06 | `Tôi nên ăn gì hôm nay?` | `OUT_OF_SCOPE` |

### 6.5 D. Context-dependent (16 case, 32 turn)

Dùng 5 kịch bản trong `data/dialogues.txt` + 11 kịch bản bổ sung. Mỗi case có
2 turn; cả 2 turn đều được chấm (turn 1 kiểm tra state, turn 2 kiểm tra
resolve).

| ID | Lượt | Query | Expected |
|---|---|---|---|
| X01.1 | 1 | `Tuần 3 học gì?` | `GET_SCHEDULE`, `week=WEEK_03`, `chapter=CH03` |
| X01.2 | 2 | `Tài liệu của chương này là gì?` | `GET_RESOURCE`, resolve `chương này → CH03` |
| X02.1 | 1 | `Chương 4 nói về gì?` | `GET_TOPIC`, `chapter=CH04` |
| X02.2 | 2 | `Nó có liên quan đến parsing không?` | `GET_TOPIC`, resolve `nó → CH04`, **không** `GET_RULE` |
| X03.1 | 1 | `Bài tập lớn có phần parser không?` | `GET_ASSIGNMENT`, `part=PART_I` |
| X03.2 | 2 | `Phần này cần xuất file gì?` | `GET_ASSIGNMENT`, resolve `phần này → PART_I`, 3 file |
| X04.1 | 1 | `Chương 11 có hỏi đáp không?` | `GET_TOPIC`, `chapter=CH11` |
| X04.2 | 2 | `Còn chương sau?` | `GET_TOPIC`, resolve `chương sau → CH12` |
| X05.1 | 1 | `L.O.2.5 học về gì?` | `GET_LO`, `lo=LO2.5` |
| X05.2 | 2 | `Nội dung này nằm ở chương nào?` | `GET_TOPIC`, resolve `nội dung này → LO2.5 → CH06` |
| X06.1 | 1 | `Chương 3 nói về gì?` | `GET_TOPIC`, `chapter=CH03` |
| X06.2 | 2 | `Chương 4 nói về gì?` | explicit `CH04`, **không** kế thừa CH03 |
| X07.1 | 1 | `Nó có liên quan đến parsing không?` | `NEEDS_CLARIFICATION` (không antecedent) |
| X07.2 | 2 | `Chương này nói về gì?` | `NEEDS_CLARIFICATION` (state rỗng) |
| X08.1 | 1 | `Tuần 30 học gì?` | `INVALID_VALUE` |
| X08.2 | 2 | `Còn tuần 31?` | `INVALID_VALUE`, resolve `tuần sau → WEEK_31` |
| X09.1 | 1 | `Chương 5 nói về gì?` | `GET_TOPIC`, `chapter=CH05` |
| X09.2 | 2 | `Chương này có những chủ đề gì?` | `GET_TOPIC`, resolve `chương này → CH05` |
| X10.1 | 1 | `Tuần 3 học gì?` | `GET_SCHEDULE`, `week=WEEK_03` |
| X10.2 | 2 | `Tuần này có mốc nào?` | `GET_SCHEDULE`, resolve `tuần này → WEEK_03` |
| X11.1 | 1 | `Phần II của BTL là gì?` | `GET_ASSIGNMENT`, `part=PART_II` |
| X11.2 | 2 | `Phần này có yêu cầu gì?` | `GET_ASSIGNMENT`, resolve `phần này → PART_II` |
| X12.1 | 1 | `Phần I của BTL là gì?` | `GET_ASSIGNMENT`, `part=PART_I` |
| X12.2 | 2 | `Nó cần xuất file gì?` | `GET_ASSIGNMENT`, resolve `nó → PART_I` |
| X13.1 | 1 | `Chương 5 nói về gì?` | `GET_TOPIC`, `chapter=CH05` |
| X13.2 | 2 | `Chương trước là chương nào?` | `GET_TOPIC`, resolve `chương trước → CH04` |
| X14.1 | 1 | `L.O.4.2 liên quan đến gì?` | `GET_LO`, `lo=LO4.2` |
| X14.2 | 2 | `Nội dung này ở chương nào?` | `GET_TOPIC`, resolve `nội dung này → LO4.2 → CH12` |
| X15.1 | 1 | `Tuần 14 học gì?` | `GET_SCHEDULE`, `week=WEEK_14` |
| X15.2 | 2 | `Còn tuần sau?` | `GET_SCHEDULE`, resolve `tuần sau → WEEK_15` |
| X16.1 | 1 | `Chương 12 nói về gì?` | `GET_TOPIC`, `chapter=CH12` |
| X16.2 | 2 | `Nó có trong đề cương không?` | `GET_TOPIC`, resolve `nó → CH12` |

X07 chứng minh hệ thống **không resolve bừa**. X08 chứng minh no-info vẫn giữ
được ngữ cảnh. X09–X16 phủ các cặp tham chiếu còn lại (`chương này`, `tuần này`,
`phần này`, `nó`, `chương trước`, `tuần sau`, `nội dung này`).

Tổng nhóm D: **16 case = 32 turn**. Cộng với 70 + 8 + 6 case single-turn:
**100 case, 116 turn**.

## 7. Schema test case

### 7.1 Định dạng lưu

Khuyến nghị `data/test_cases.jsonl` — một JSON object mỗi dòng, chỉ dùng
stdlib, dễ diff, dễ đọc bằng `json.loads()`.

```json
{"id":"C01","category":"course_info","turns":[{"query":"Môn NLP có bao nhiêu tín chỉ?"}],"expected":[{"intent":"GET_COURSE_INFO","entities":{"course":"CO3085","attribute":"credits"},"status":"OK","answer_contains":["3 tín chỉ"],"answer_excludes":["không tìm thấy"]}],"source":"sample_queries.txt","notes":"Q001"}
```

Case hội thoại:

```json
{"id":"X02","category":"context","turns":[{"query":"Chương 4 nói về gì?"},{"query":"Nó có liên quan đến parsing không?"}],"expected":[{"intent":"GET_TOPIC","entities":{"chapter":"CH04"},"status":"OK","answer_contains":["Features","Augmented Grammar"]},{"intent":"GET_TOPIC","entities":{"chapter":"CH04"},"status":"OK","answer_contains":["Có","parsing"],"answer_excludes":["quy định","liêm chính"]}],"expected_references":[{"turn":2,"phrase":"Nó","antecedent":"CH04"}],"source":"dialogues.txt","notes":"Dialogue 02"}
```

### 7.2 Trường bắt buộc

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | string | Duy nhất, ổn định |
| `category` | enum | `course_info`, `schedule`, `topic`, `assignment`, `deadline`, `resource`, `rule`, `lo`, `no_info`, `out_of_scope`, `context` |
| `turns` | list | Mỗi phần tử `{query}`; >1 là hội thoại |
| `expected` | list | Cùng độ dài `turns`; mỗi turn có `intent`, `entities`, `status`, `answer_contains`, `answer_excludes` |
| `expected_references` | list (optional) | `{turn, phrase, antecedent}` cho context |
| `source` | string | `sample_queries.txt`, `faq.txt`, `dialogues.txt`, `manual` |
| `notes` | string | Giải thích đáp án |

### 7.3 Enum status

| Status | Nghĩa | Ví dụ |
|---|---|---|
| `OK` | Trả lời được | tuần 3, tín chỉ |
| `NOT_FOUND` | Trong miền nhưng không có dữ liệu | LO4.3, giảng viên |
| `INVALID_VALUE` | Entity có nhưng giá trị ngoài range | tuần 30, chương 15 |
| `OUT_OF_SCOPE` | Ngoài miền môn học | thời tiết |
| `AMBIGUOUS` | Nhiều kết quả cùng khớp | PCFG ở 2 chương (nếu chọn hỏi lại) |
| `NEEDS_CLARIFICATION` | Thiếu antecedent | `Nó là gì?` khi state rỗng |

`AMBIGUOUS` chỉ dùng nếu hệ thống **hỏi lại**. Nếu hệ thống trả cả hai chương
kèm giải thích thì status là `OK` và `answer_contains` có cả `Chương 3` lẫn
`Chương 6`.

### 7.4 Quy ước `answer_contains`

- Tất cả chuỗi trong `answer_contains` phải xuất hiện (AND), không phân biệt
  hoa/thường, đã chuẩn hóa Unicode NFC.
- `answer_excludes`: không chuỗi nào được xuất hiện.
- Không dùng chuỗi quá ngắn (< 3 ký tự) hoặc quá chung (`"có"`).
- Với câu trả lời dài, chọn 2–4 “key fact”, không chép nguyên câu.

Ví dụ tốt:

```json
"answer_contains": ["3 tín chỉ"]
"answer_contains": ["Chương 10", "semantic grammar"]
"answer_contains": ["tuần 8", "checkpoint"]
```

Ví dụ xấu:

```json
"answer_contains": ["có"]          // quá chung
"answer_contains": ["Xin chào"]    // không phải nội dung
```

## 8. Metrics

### 8.1 Tổng hợp

| Metric | Công thức | Ghi chú |
|---|---|---|
| Intent Accuracy | correct / total | Trên tất cả turn in-scope |
| Entity Precision | TP / (TP + FP) | Micro-average theo entity |
| Entity Recall | TP / (TP + FN) | Micro-average |
| Entity F1 | 2PR/(P+R) | Metric chính cho entity |
| Status Accuracy | correct status / total | Gồm cả no-info/OOS |
| Answer Accuracy | sum(score) / (2 × total) | Score 0/1/2 |
| Answer Exact | score == 2 / total | Chặt hơn |
| Context Resolution Accuracy | correct antecedent / context turns | Chỉ trên suite D |
| Clarification Accuracy | đúng khi cần hỏi lại / case cần hỏi lại | X07 |
| OOS Precision | TP_OOS / predicted_OOS | Tránh từ chối câu đúng |
| OOS Recall | TP_OOS / actual_OOS | Tránh trả lời câu ngoài miền |
| Pass Rate | case có tất cả metric con đúng / total | Chỉ số “sẵn sàng nộp” |

### 8.2 Intent

- Chấm theo từng turn.
- Với context case, intent kỳ vọng là intent **sau khi resolve**, không phải
  intent thô của câu chưa resolve.
- Báo cáo thêm **confusion matrix** cho các cặp nhầm phổ biến
  (`GET_TOPIC ↔ GET_RULE`, `GET_RESOURCE ↔ GET_TOPIC`).

### 8.3 Entity P/R/F1

Định nghĩa:

- **TP**: cặp `(type, value)` có trong cả expected và predicted.
- **FP**: có trong predicted, không có trong expected.
- **FN**: có trong expected, không có trong predicted.

Quy tắc:

1. So sánh **theo `(type, value)`**, không theo chuỗi.
2. Không tính entity phụ nếu test case không yêu cầu (ví dụ `course=CO3085` khi
   hỏi tuần 3).
3. Với multi-entity, chấm từng cặp.
4. Báo cáo P/R/F1 **theo từng entity type**:

| Type | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `week` | | | | |
| `chapter` | | | | |
| `topic` | | | | |
| `part` | | | | |
| `lo` | | | | |
| `assignment` | | | | |
| `attribute` | | | | |
| `rule` | | | | |

5. Với context case, entity kế thừa được resolve **được tính là predicted** nếu
   nó thực sự đi vào KB.

### 8.4 Status

- Chấm chính xác theo enum.
- `INVALID_VALUE` và `NOT_FOUND` là hai status khác nhau; không gộp.
- `OUT_OF_SCOPE` chỉ đúng khi câu thật sự ngoài miền.
- Nếu hệ thống trả `OK` nhưng answer rỗng → status sai.

### 8.5 Answer

Thang điểm 0/1/2:

| Điểm | Điều kiện |
|---:|---|
| 2 | Status đúng **và** tất cả `answer_contains` xuất hiện **và** không có `answer_excludes` **và** không phải câu generic |
| 1 | Status đúng **và** ít nhất một `answer_contains` xuất hiện **và** không mâu thuẫn dữ liệu |
| 0 | Status sai, hoặc không có key fact nào, hoặc có `answer_excludes`, hoặc trả generic/fallback |

Câu generic bị coi là 0 điểm:

```text
Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu môn học.
Vui lòng cho biết tuần cụ thể.
Tài liệu tham khảo: 4 cuốn sách. Xem danh sách đầy đủ trong resources.txt
Bài tập lớn 'Intelligent Course Assistant' - Nhóm 3-4 sinh viên.
```

Ngoại lệ: nếu status kỳ vọng là `NOT_FOUND`/`INVALID_VALUE` thì câu thông báo
rõ ràng **không** bị coi là generic.

Answer Accuracy = `sum(score) / (2 × N) × 100%`.

### 8.6 Context resolution

- `resolved_antecedent == expected_antecedent` → đúng.
- Nếu hệ thống không resolve nhưng vẫn trả lời đúng nhờ entity explicit → tính
  là **không đạt context resolution**, nhưng answer vẫn có thể đúng.
- Case cần clarification (X07) phải trả `NEEDS_CLARIFICATION`, không được
  `OK` với antecedent bịa.

### 8.7 OOS

- `OOS Precision = TP / (TP + FP)`: trong các câu bị từ chối, bao nhiêu thật sự
  ngoài miền. Precision thấp = hệ thống từ chối câu đúng.
- `OOS Recall = TP / (TP + FN)`: trong các câu ngoài miền, bao nhiêu bị phát
  hiện. Recall thấp = hệ thống trả lời câu ngoài miền.
- Báo cáo cả hai; không chỉ một con số “100%”.

### 8.8 Pass Rate

Một case được coi là **pass** nếu:

- status đúng,
- intent đúng,
- entity F1 = 1.0 (với case có entity),
- answer score = 2,
- với context: antecedent đúng.

Pass Rate là chỉ số chính để quyết định “đủ điều kiện nộp”.

## 9. Error taxonomy

Mỗi lỗi được gán **một** root cause chính, kèm file/rule.

| Mã | Nhóm | Mô tả | File thường gặp |
|---|---|---|---|
| E1 | Tokenization | Compound bị tách, dấu câu bị bỏ, NFC/NFD | `preprocessing.py` |
| E2 | Grammar / Parse | Câu đúng bị từ chối, câu sai được nhận | `grammar.py`, `parser.py` |
| E3 | Intent | Nhầm intent do keyword trùng | `semantic.py` |
| E4 | Entity alias | Substring match, thiếu alias, không longest-match | `semantic.py`, `knowledge_base.py` |
| E5 | Data missing | KB thiếu field/record | `data/*.txt`, `data_loader.py` |
| E6 | Lookup logic | So khớp sai, chọn bừa, không xử lý multi-result | `knowledge_base.py` |
| E7 | Answer template | Trả sai trọng tâm, format tiếng Anh, nối chuỗi sai | `knowledge_base.py` |
| E8 | No-info policy | Dùng chung câu cho mọi trường hợp, không phân biệt status | `knowledge_base.py` |
| E9 | Dialogue | Không resolve, resolve sai, không lưu state | `dialogue.py`, `main.py` |
| E10 | Output | File không sinh lại được, sai format | `main.py` |
| E11 | Evaluation harness | Metric sai, case thiếu tiêu chí | `evaluation.py` |
| E12 | Environment | Encoding Windows, đường dẫn tương đối | `main.py`, `evaluation.py` |

## 10. Lỗi thật tại baseline và root cause

Các lỗi dưới đây đã tái hiện tại commit `883e0c6`. Chúng phải trở thành
**regression case** trong test set mới.

| # | Query | Kết quả baseline | Kỳ vọng | Root cause |
|---|---|---|---|---|
| 1 | `BTL cần xuất những file gì?` | `Bài tập lớn 'Intelligent Course Assistant' - Nhóm 3-4 sinh viên.` | 8 output file theo phần | E5 + E6 + E7: KB thiếu `suggested_outputs`, không có sub-intent `outputs` |
| 2 | `Phần IV của BTL là gì?` | `Grammar and Parser: ...` | Evaluation | E6: `'I' in 'PART_IV'` |
| 3 | `Tài liệu về PCFG ở đâu?` | `Tài liệu tham khảo: 4 cuốn sách...` | Tài liệu cụ thể | E4 + E6: `'cfg' in 'pcfg'`, không có topic→resource |
| 4 | `Tuần 30 học gì?` | `Vui lòng cho biết tuần cụ thể.` | `INVALID_VALUE` | E8: không validate range |
| 5 | `Ai dạy môn NLP?` | `Xin lỗi, tôi không tìm thấy...` | `NOT_FOUND` + lý do giảng viên | E5 + E8: không có nhánh `GET_INSTRUCTOR` |
| 6 | `Chương nào học về semantic grammar?` | `Chương 07... SEMANTIC` | CH10 | E4: alias ngắn thắng alias dài |
| 7 | `Chương nào học về knowledge representation?` | `Xin lỗi...` | CH11 | E4: thiếu alias |
| 8 | `PCFG được học ở đâu?` | `Chương 03... CFG` | CH03 + CH06 | E4 + E6 |
| 9 | `Chương 4 học vào tuần nào?` | `... Week 04.` | `... Tuần 04.` | E7: format tiếng Anh |
| 10 | `Nó có liên quan đến parsing không?` (sau `Chương 4`) | `GET_RULE` + toàn bộ quy định | `GET_TOPIC` + CH04 | E9 + E3: `không` kích hoạt rule |
| 11 | `Phần này cần xuất file gì?` (sau BTL parser) | title/team size | PART_I + 3 file | E9 + E5 |
| 12 | `Tài liệu của phần này ở đâu?` (sau `Tuần 3`) | 4 sách generic | tài liệu CH03/CFG | E9: không lưu `last_week` |
| 13 | `Hôm nay thời tiết thế nào?` | Vẫn trả parse tree | `OUT_OF_SCOPE` | E2: fallback parser nhận mọi input |
| 14 | `asdf qwerty zzz` | Vẫn trả parse tree | `()` | E2 |
| 15 | `1 2 3 4 5` | Vẫn trả parse tree | `()` | E2 |

Lưu ý: lỗi 13–15 thuộc Part 1; evaluation phải có case để **khóa** hành vi mới,
tránh tái phát.

## 11. Thiết kế runner

### 11.1 API

```python
@dataclass
class Turn:
    query: str

@dataclass
class ExpectedTurn:
    intent: str
    entities: dict[str, str]
    status: str
    answer_contains: list[str]
    answer_excludes: list[str]

@dataclass
class TestCase:
    id: str
    category: str
    turns: list[Turn]
    expected: list[ExpectedTurn]
    expected_references: list[dict]
    source: str
    notes: str

@dataclass
class TurnResult:
    query: str
    predicted_intent: str
    predicted_entities: dict
    predicted_status: str
    predicted_answer: str
    resolved_reference: str | None
    intent_ok: bool
    entity_tp: int
    entity_fp: int
    entity_fn: int
    status_ok: bool
    answer_score: int
    reference_ok: bool | None
    error_code: str | None
    error_detail: str | None

@dataclass
class CaseResult:
    case: TestCase
    turns: list[TurnResult]
    passed: bool

@dataclass
class EvaluationReport:
    total_cases: int
    total_turns: int
    metrics: dict
    by_category: dict
    by_intent: dict
    entity_by_type: dict
    errors: list[CaseResult]
    cases: list[CaseResult]
```

### 11.2 Loader

```python
def load_cases(path: str) -> list[TestCase]:
    cases = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            data = json.loads(line)
            validate_case(data, lineno)
            cases.append(TestCase(**data))
    return cases
```

`validate_case()` phải kiểm tra:

- `id` duy nhất,
- `len(turns) == len(expected)`,
- `status` thuộc enum,
- `answer_contains` không rỗng với status `OK`,
- `expected_references` turn hợp lệ.

Fail fast, không bỏ qua case lỗi.

### 11.3 Chạy

```python
def run_case(assistant, case):
    results = []
    assistant.reset_dialogue()          # state mới cho mỗi case
    for i, turn in enumerate(case.turns):
        if len(case.turns) == 1:
            out = assistant.process_query(turn.query)
        else:
            answer, state = assistant.process_dialogue(turn.query)
            out = assistant.last_result      # gồm intent/entities/status
        results.append(score_turn(turn, out, case.expected[i]))
    return CaseResult(case, results, all_turns_pass(results))
```

Điểm quan trọng:

- Mỗi case bắt đầu với state rỗng.
- Case 1 turn dùng `process_query()`; case nhiều turn dùng `process_dialogue()`.
- `out` phải có `status`; nếu API hiện tại chưa có, Part 3 thêm vào.
- Không dùng `str(dict)` để chấm entity.

### 11.4 CLI

```bash
python -m src.evaluation \
  --cases data/test_cases.jsonl \
  --out output/evaluation.txt \
  --json output/evaluation.json \
  --strict
```

- `--strict`: exit code 1 nếu pass rate < ngưỡng hoặc có case fail.
- Mặc định đọc `data/test_cases.jsonl`, ghi `output/evaluation.txt`.
- Không phụ thuộc thư mục hiện tại: dùng `pathlib.Path(__file__).parent.parent`.

### 11.5 Tích hợp `main.py`

Xóa đoạn 5-query report trong `save_outputs()`. Thay bằng:

```python
from .evaluation import run_evaluation

run_evaluation(
    cases_path=os.path.join(base_dir, "data", "test_cases.jsonl"),
    out_path=os.path.join(output_dir, "evaluation.txt"),
    json_path=os.path.join(output_dir, "evaluation.json"),
)
```

Chỉ còn **một** nguồn số liệu.

## 12. Report template

`output/evaluation.txt`:

```text
======================================================================
COURSE ASSISTANT EVALUATION REPORT
======================================================================
Generated: 2026-11-08T10:00:00
Commit: <git short hash>
Test set: data/test_cases.jsonl (100 cases, 116 turns)

1. OVERALL
----------------------------------------------------------------------
Pass Rate:                  __.__%  (__/100)
Intent Accuracy:            __.__%  (__/116)
Entity Precision:           __.__%
Entity Recall:              __.__%
Entity F1:                  __.__
Status Accuracy:            __.__%  (__/116)
Answer Accuracy:            __.__%  (score __/226)
Answer Exact (score=2):     __.__%  (__/116)
Context Resolution:         __.__%  (__/16)
Clarification Accuracy:     __.__%  (__/2)
OOS Precision:              __.__%
OOS Recall:                 __.__%

2. BY CATEGORY
----------------------------------------------------------------------
Category            Cases  Pass   Intent  Status  Answer  F1
course_info            10   __%     __%     __%     __%  __
schedule               10   __%     __%     __%     __%  __
topic                  14   __%     __%     __%     __%  __
assignment             10   __%     __%     __%     __%  __
deadline                5   __%     __%     __%     __%  __
resource                7   __%     __%     __%     __%  __
rule                    7   __%     __%     __%     __%  __
lo                      7   __%     __%     __%     __%  __
no_info                 8   __%     __%     __%     __%  __
out_of_scope            6   __%     __%     __%     __%  __
context                16   __%     __%     __%     __%  __

3. BY INTENT
----------------------------------------------------------------------
Intent                    N   Intent  Status  Answer  F1
GET_COURSE_INFO          __     __%     __%     __%  __
...

4. ENTITY BY TYPE
----------------------------------------------------------------------
Type          TP   FP   FN   Precision  Recall   F1
week          __   __   __       __%     __%   __
chapter       __   __   __       __%     __%   __
topic         __   __   __       __%     __%   __
part          __   __   __       __%     __%   __
lo            __   __   __       __%     __%   __
assignment    __   __   __       __%     __%   __
attribute     __   __   __       __%     __%   __
rule          __   __   __       __%     __%   __

5. ERROR ANALYSIS
----------------------------------------------------------------------
E1 Tokenization:             __
E2 Grammar/Parse:            __
E3 Intent:                   __
E4 Entity alias:             __
E5 Data missing:             __
E6 Lookup logic:             __
E7 Answer template:          __
E8 No-info policy:           __
E9 Dialogue:                 __
E10 Output:                  __
E11 Evaluation harness:      __
E12 Environment:             __

6. FAILED CASES (first 20)
----------------------------------------------------------------------
[C01] Môn NLP có bao nhiêu tín chỉ?
  Expected: intent=GET_COURSE_INFO status=OK contains=["3 tín chỉ"]
  Predicted: intent=GET_COURSE_INFO status=OK
  Answer: ...
  Error: E7 — answer thiếu "3 tín chỉ"
  Notes: ...

...

7. REGRESSION CHECK
----------------------------------------------------------------------
Previously fixed:
  [x] PCFG -> CH03 + CH06
  [x] Phần IV -> PART_IV
  [x] Tuần 30 -> INVALID_VALUE
  [ ] ...

8. LIMITATIONS
----------------------------------------------------------------------
- Rule-based, không học từ dữ liệu.
- Test set viết tay, không phủ hết cách diễn đạt.
- ...
```

`output/evaluation.json` chứa cùng số liệu + toàn bộ `CaseResult` để CI so sánh.

## 13. Kế hoạch triển khai

| Bước | Việc làm | Kết quả | Ước lượng |
|---|---|---|---|
| 1 | Chốt schema JSONL + enum status | `data/test_cases.jsonl` | 0.5 ngày |
| 2 | Viết 70 case in-scope | Nhóm A | 1 ngày |
| 3 | Viết 8 case no-info + 6 OOS | Nhóm B/C | 0.5 ngày |
| 4 | Viết 16 case context (32 turn) | Nhóm D | 0.5 ngày |
| 5 | Refactor `evaluation.py`: loader, metric, status | Runner mới | 1 ngày |
| 6 | Viết `score_turn()`, entity P/R/F1 | Metric đúng | 0.5 ngày |
| 7 | Viết report text + JSON | Output | 0.5 ngày |
| 8 | Tích hợp `main.save_outputs()`, xóa report 5 case | Một nguồn | 0.25 ngày |
| 9 | Viết `tests/test_evaluation.py` | Pass | 0.5 ngày |
| 10 | Chạy baseline, ghi lỗi thật vào report | Số liệu | 0.5 ngày |

Tổng: **3–4 ngày** (sau khi Part 1–4 xong).

## 14. Test plan cho chính evaluation

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | Load 100 case | Không lỗi |
| 2 | `len(cases) == 100` | Đúng |
| 3 | `len(turns) == 116` | Đúng |
| 4 | Mọi case có `expected` cùng độ dài `turns` | Đúng |
| 5 | Mọi status thuộc enum | Đúng |
| 6 | `id` duy nhất | Đúng |
| 7 | Entity F1 của `{"topic":"CFG"}` vs expected `{"topic":"PCFG"}` | 0.0, không phải 1.0 |
| 8 | Answer score với câu generic | 0 |
| 9 | Answer score với đủ key fact | 2 |
| 10 | Case X07 trả `NEEDS_CLARIFICATION` | Đúng |
| 11 | Case X02.2 không trả `GET_RULE` | Đúng |
| 12 | Report có đủ section | Đúng |
| 13 | Chạy 2 lần cho cùng JSON | Hash giống |
| 14 | `--strict` exit 1 khi có case fail | Đúng |

## 15. Acceptance criteria

- [ ] `data/test_cases.jsonl` có **100 case**, phủ 11 category.
- [ ] Có ít nhất **8 case no-info/invalid**, **6 case out-of-scope**,
      **16 case context (32 turn)**.
- [ ] Mọi case in-scope có `answer_contains` (không còn answer accuracy giả).
- [ ] Entity chấm bằng P/R/F1 theo `(type, value)`, không substring.
- [ ] Có metric `Status Accuracy` và phân biệt `NOT_FOUND` / `INVALID_VALUE`.
- [ ] Có metric `Context Resolution Accuracy` cho suite D.
- [ ] Có `OOS Precision` và `OOS Recall`.
- [ ] Report có per-category, per-intent, entity-by-type, error taxonomy.
- [ ] Có ít nhất 10 lỗi thật trong mục “Failed cases” với root cause.
- [ ] `output/evaluation.txt` và `output/evaluation.json` sinh từ **một** runner.
- [ ] `main.save_outputs()` không còn tự viết report 5 case.
- [ ] `pytest tests/test_evaluation.py` pass.
- [ ] Chạy lại cho cùng số liệu (deterministic).
- [ ] Pass Rate được ghi rõ; không tuyên bố 100% nếu chưa đạt.

## 16. Rủi ro và lưu ý

- **Test set quá dễ:** nếu chỉ lấy câu mẫu trong `sample_queries.txt`, pass rate
  sẽ cao giả tạo. Phải thêm cách diễn đạt khác và case khó.
- **Test set quá khó:** nếu đặt kỳ vọng ngoài khả năng rule-based, pass rate
  thấp không phản ánh đúng. Ghi rõ giới hạn trong report.
- **Chấm answer bằng substring:** dễ false positive. Dùng `answer_contains` +
  `answer_excludes` + status + kiểm tra generic.
- **Entity phụ:** không chấm `course=CO3085` khi câu hỏi không yêu cầu, tránh
  làm nhiễu P/R.
- **Context case chạy chung state:** phải reset state mỗi case, nếu không case
  sau sẽ bị ảnh hưởng case trước.
- **Report tự động ghi đè:** nên lưu baseline đã duyệt để so sánh regression.
- **Số liệu trong README/REPORT:** phải trích từ `output/evaluation.json`, không
  chép tay.
- **Windows encoding:** luôn mở file với `encoding="utf-8"`; khi `print()` dùng
  `PYTHONIOENCODING=utf-8` hoặc chỉ ghi file.
- **Đừng tối ưu metric:** mục tiêu là hệ thống đúng, không phải pass rate đẹp.
