# PART 2 — Sửa bộ sinh câu (Generative)

## 1. Mục tiêu

Sau bước này:

1. `output/samples.txt` có **tối đa 10.000 câu** (không tính dòng comment/rỗng).
2. Không còn câu vô nghĩa kiểu `ở đó file deadline muốn có ?`.
3. Không còn dấu `_` trong câu xuất ra.
4. Câu sinh ra phải:
   - parse được bằng parser strict (Part 1),
   - có intent khác `UNKNOWN`,
   - có entity tồn tại thật trong knowledge base (Part 3),
   - trả lời được bằng dữ liệu môn học, không rơi vào fallback “không tìm thấy”.
5. Sinh câu có thể lặp lại được (cùng seed → cùng file), có thống kê coverage theo intent/chương/tuần/topic.
6. `--mode generate` sinh lại `samples.txt` từ code, không chỉnh tay.

## 2. Phạm vi file

| File | Vai trò |
|---|---|
| `src/grammar.py` | Grammar, template, `generate_all_sentences()` |
| `src/preprocessing.py` / `src/lexicon.py` | Tokenize, canonical token, `detokenize()` |
| `src/parser.py` | Xác thực cú pháp câu sinh ra |
| `src/semantic.py` | Xác thực intent/entity |
| `src/knowledge_base.py` | Xác thực entity có dữ liệu trả lời |
| `src/generator.py` (mới) | Pipeline sinh + lọc + chọn mẫu |
| `src/main.py` | Gọi generator trong `save_outputs()` |
| `output/samples.txt` | Kết quả cuối |
| `tests/test_generator.py` (mới) | Test số lượng, chất lượng, determinism |

## 3. Hiện trạng và lỗi gốc

### 3.1 Số lượng vượt 10.000

Trong `src/main.py`, `save_outputs()` làm:

```python
template_sentences = generate_template_sentences()          # 69 câu
grammar_sentences = grammar.generate_all_sentences(10000)   # 10.000 câu
...
for sent, intent in template_sentences: f.write(...)        # 69 dòng
for sent in grammar_sentences: f.write(...)                 # 10.000 dòng
```

Kết quả kiểm tra `output/samples.txt` hiện tại:

| Chỉ số | Giá trị |
|---|---:|
| Tổng số dòng | 10.072 |
| Dòng template | 69 |
| Dòng grammar | 10.000 |
| Dòng comment | 2 |
| Dòng rỗng | 1 |
| **Dòng câu thực tế** | **10.069** |

→ Vượt yêu cầu **69 câu** chỉ vì cộng template lên trên grammar. Giới hạn `max_sentences=10000` chỉ áp dụng cho grammar, không áp dụng cho toàn bộ file.

### 3.2 Câu vô nghĩa

`CFG.generate_sentence()` chọn ngẫu nhiên một production tại mỗi bước:

```python
rule = random.choice(rules)
```

Grammar hiện tại cho phép nhiều tổ hợp không có nghĩa:

```text
WH_WORD -> ở | đâu | bao | có | là | gì | nào
VP      -> VERB ADJ | VERB NUM | VERB NUM NOUN
NP      -> DET | DET NOMINAL | NOMINAL
```

Ví dụ thực tế trong `output/samples.txt`:

```text
ở đó file deadline muốn có ?
1 có ?
học của tuần ?
? đó nói gì ?
1 hỏi 60 ?
```

Nguyên nhân:

- `WH_WORD` là từ đơn rời, không phải cụm hỏi hoàn chỉnh.
- `VP` cho phép ghép động từ với số, tính từ, danh từ tùy ý.
- Không có kiểm tra ngữ nghĩa sau khi sinh.
- `generate_all_sentences()` chỉ kiểm tra `len(words) <= 15`, không kiểm tra câu có nghĩa hay không.
- Không có bước loại câu trùng sau khi chuẩn hóa.
- Không có bước `detokenize()` trước khi ghi file.

### 3.3 Dấu `_` xuất hiện trong câu

Grammar dùng terminal canonical có `_`:

```text
NOUN -> tín_chỉ
NOUN -> môn_học
ASSIGNMENT_NAME -> bài_tập_lớn
COURSE_NAME -> xử_lý_ngôn_ngữ_tự_nhiên
```

`generate_sentence()` trả về chuỗi nối trực tiếp các terminal, không chuyển về dạng tự nhiên. Kết quả:

```text
1 cần gì thời_hạn ?
hỏi ở xử_lý_ngôn_ngữ_tự_nhiên ?
```

Thống kê hiện tại: **6.508 / 10.072 dòng có chứa `_`**.

### 3.4 Template chưa đủ tốt

`generate_template_sentences()`:

```python
courses = ["NLP", "CO3085", "xử lý ngôn ngữ tự nhiên"]
chapters = list(range(1, 13))
weeks = list(range(1, 16))
topics = ["CFG", "PCFG", "Parsing", "Semantic", "POS Tagging", "Feature"]
parts = ["I", "II", "III", "IV"]
los = ["1.1", "2.1", "2.5", "3.3", "4.1", "4.2"]
```

Nhưng khi sinh chỉ dùng:

```python
courses[:2]    # chỉ NLP, CO3085
chapters[:3]   # chỉ chương 1–3
weeks[:3]      # chỉ tuần 1–3
topics[:3]     # chỉ CFG, PCFG, Parsing
parts[:2]      # chỉ I, II
los[:3]        # chỉ 1.1, 2.1, 2.5
```

Hệ quả:

- Không phủ 12 chương, 15 tuần, 4 phần BTL, 16 LO.
- Nhiều template không bao giờ sinh câu.
- `except:` trần che lỗi format, có thể ghi ra template chưa thay placeholder.
- Không kiểm tra câu sinh ra có thật sự trả lời được không.

### 3.5 File trộn hai định dạng

```text
Môn NLP có bao nhiêu tín chỉ?	(intent=GET_COURSE_INFO)
...
1 cần gì thời_hạn ?
```

Một nửa có nhãn intent, một nửa không. Điều này gây khó khi:
- đếm số câu,
- đánh giá coverage,
- dùng file làm test set,
- so sánh baseline.

## 4. Nguyên tắc thiết kế

1. **Chất lượng trước số lượng.** Yêu cầu là “≤ 10.000”, không phải “phải đủ 10.000”. Nếu chỉ có 8.500 câu đạt kiểm tra thì ghi 8.500 câu, không thêm câu rác cho đủ.
2. **Sinh có kiểm soát.** Không sinh ngẫu nhiên toàn bộ grammar rồi lọc; thay vào đó sinh theo **frame/ý định** rồi mới dùng grammar để tạo biến thể.
3. **Một nguồn sự thật.** Slot (chương, tuần, topic, LO, phần BTL) lấy từ knowledge base đã load ở Part 3, không hard-code trong generator.
4. **Tách biểu diễn nội bộ và câu hiển thị.** Terminal canonical dùng `_`; câu xuất ra phải qua `detokenize()`.
5. **Tất cả câu phải chứng minh được.** Mỗi câu lưu metadata: nguồn (template/grammar), intent, entity, template id, seed.
6. **Deterministic.** Dùng `random.Random(seed)` riêng, không dùng `random` toàn cục.

## 5. Kiến trúc đích

```text
KB đã load (Part 3)
        │
        ▼
┌─────────────────────┐
│ 1. Sinh ứng viên    │  template + frame + grammar có ràng buộc
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 2. Chuẩn hóa bề mặt │  detokenize, khoảng trắng, dấu câu, viết hoa
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 3. Kiểm tra cú pháp │  parser strict (Part 1), phải khác ()
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 4. Kiểm tra ngữ nghĩa│ intent != UNKNOWN, entity tồn tại, có câu trả lời
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 5. Loại trùng       │  chuẩn hóa lowercase + bỏ dấu câu + gộp khoảng trắng
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 6. Chọn theo quota  │  cân bằng intent/chương/tuần/topic, cap 10.000
└─────────┬───────────┘
          ▼
   output/samples.txt
```

## 6. Sinh câu theo frame + template

### 6.1 Định nghĩa frame

Mỗi frame là một mẫu câu có slot và điều kiện. Ví dụ:

```python
FRAMES = [
    {
        "id": "COURSE_CREDITS_01",
        "intent": "GET_COURSE_INFO",
        "template": "Môn {course} có bao nhiêu tín chỉ?",
        "slots": {"course": "course_aliases"},
        "requires": ["course.credits"],
    },
    {
        "id": "SCHEDULE_WEEK_01",
        "intent": "GET_SCHEDULE",
        "template": "Tuần {week} học những gì?",
        "slots": {"week": "valid_weeks"},
        "requires": ["schedule[week]"],
    },
    {
        "id": "TOPIC_CHAPTER_01",
        "intent": "GET_TOPIC",
        "template": "Chương nào học về {topic}?",
        "slots": {"topic": "topic_aliases"},
        "requires": ["topic_to_chapter[topic]"],
    },
    {
        "id": "ASSIGNMENT_OUTPUT_01",
        "intent": "GET_ASSIGNMENT",
        "template": "Phần {part} của bài tập lớn cần xuất những file gì?",
        "slots": {"part": "assignment_parts_with_outputs"},
        "requires": ["assignment.parts[part].suggested_outputs"],
    },
    {
        "id": "LO_CONTENT_01",
        "intent": "GET_LO",
        "template": "L.O.{lo} liên quan đến nội dung gì?",
        "slots": {"lo": "valid_lo_ids"},
        "requires": ["learning_outcomes[lo]"],
    },
]
```

Quy tắc:

- Slot chỉ lấy giá trị **có thật** trong KB.
- Nếu frame yêu cầu `suggested_outputs` mà dữ liệu không có → không sinh frame đó.
- Không dùng `try/except` trần để bỏ qua lỗi; lỗi format phải làm test fail.

### 6.2 Sinh biến thể từ grammar có ràng buộc

Có thể dùng grammar để tạo biến thể câu hỏi, nhưng **không dùng grammar rộng hiện tại**. Tạo grammar sinh riêng:

```text
GEN_S -> GEN_COURSE_INFO
       | GEN_SCHEDULE
       | GEN_TOPIC
       | GEN_ASSIGNMENT
       | GEN_DEADLINE
       | GEN_RESOURCE
       | GEN_RULE
       | GEN_LO

GEN_COURSE_INFO -> COURSE_QUESTION
GEN_SCHEDULE    -> WEEK_QUESTION | CHAPTER_WEEK_QUESTION
GEN_TOPIC       -> CHAPTER_TOPIC_QUESTION | TOPIC_CHAPTER_QUESTION
...
```

Mỗi nonterminal sinh chỉ có các tổ hợp đã được kiểm chứng. Grammar rộng vẫn giữ cho parser (Part 1), nhưng generator dùng grammar hẹp.

### 6.3 Sinh từ template có tham số

Với mỗi intent, định nghĩa nhiều cách diễn đạt:

```python
COURSE_INFO_TEMPLATES = [
    "Môn {course} có bao nhiêu tín chỉ?",
    "{course} có mấy tín chỉ?",
    "Cho tôi biết số tín chỉ của môn {course}.",
    "Môn {course} gồm những phần chính nào?",
    "Mô tả ngắn về môn {course}.",
    "Mục tiêu của môn {course} là gì?",
    "Môn {course} được đánh giá như thế nào?",
    "Midterm của môn {course} kéo dài bao lâu?",
    "Final của môn {course} kéo dài bao lâu?",
    "Môn {course} có bao nhiêu giờ tự học?",
]
```

Tương tự cho 8 intent còn lại. Mỗi intent nên có 8–15 template, mỗi template nhân với slot hợp lệ.

### 6.4 Phân bổ quota

Đề xuất phân bổ 10.000 câu (có thể điều chỉnh sau khi đo coverage):

| Intent | Số câu mục tiêu | Ghi chú |
|---|---:|---|
| `GET_COURSE_INFO` | 1.000 | credits, ECTS, parts, description, assessment, exam, hours |
| `GET_SCHEDULE` | 1.800 | 15 tuần × nhiều cách hỏi; hỏi chương → tuần |
| `GET_TOPIC` | 2.500 | 12 chương × subtopics × topic alias |
| `GET_ASSIGNMENT` | 1.500 | yêu cầu, phần, output file, team size |
| `GET_DEADLINE` | 500 | checkpoint/final |
| `GET_RESOURCE` | 1.200 | 8 tài liệu × topic/usage |
| `GET_RULE` | 700 | 8 quy định |
| `GET_LO` | 800 | 16 LO |
| `GET_INSTRUCTOR` | 0 | Chỉ sinh nếu KB có dữ liệu giảng viên |
| **Tổng** | **10.000** | |

Nếu bổ sung giảng viên, lấy 200 câu từ `GET_TOPIC` để tổng không đổi.

Không đưa câu `UNKNOWN`/out-of-scope vào `samples.txt`; các câu này thuộc test set (Part 5).

### 6.5 Đa dạng hóa

Để tránh 10.000 câu na ná nhau:

- Mỗi `(intent, entity)` tối đa 20 câu.
- Mỗi template tối đa 300 câu.
- Mỗi chương/tuần/topic/LO phải có ít nhất 5 câu.
- Ưu tiên template chưa dùng; nếu đã đủ quota thì chuyển sang template khác.
- Kiểm tra phân bố bằng thống kê sau khi sinh.

## 7. Chuẩn hóa bề mặt (detokenize)

### 7.1 Bảng chuyển đổi

| Canonical | Hiển thị |
|---|---|
| `tín_chỉ` | `tín chỉ` |
| `môn_học` | `môn học` |
| `bài_tập_lớn` | `bài tập lớn` |
| `bài_tập` | `bài tập` |
| `tài_liệu` | `tài liệu` |
| `quy_định` | `quy định` |
| `thời_hạn` | `thời hạn` |
| `nội_dung` | `nội dung` |
| `yêu_cầu` | `yêu cầu` |
| `liên_quan` | `liên quan` |
| `sử_dụng` | `sử dụng` |
| `xử_lý_ngôn_ngữ_tự_nhiên` | `xử lý ngôn ngữ tự nhiên` |
| `phần_này` | `phần này` |
| `chương_này` | `chương này` |
| `l.o.2.5` / `lo_2_5` | `L.O.2.5` |
| `co3085` | `CO3085` |
| `nlp` | `NLP` |
| `btl` | `BTL` |
| `cfg` | `CFG` |
| `pcfg` | `PCFG` |
| `pos` | `POS` |

### 7.2 Quy tắc

1. `detokenize()` phải là **hàm duy nhất** chuyển canonical → hiển thị; không tự `.replace("_", " ")` rải rác.
2. Không thay `_` trong ID cần giữ nguyên (ví dụ `PART_I` nếu muốn hiển thị `Phần I` thì map riêng).
3. Sau detokenize:
   - gộp khoảng trắng,
   - bỏ khoảng trắng trước `?`, `!`, `.`, `,`,
   - viết hoa đầu câu,
   - đảm bảo kết thúc bằng `?` nếu là câu hỏi.
4. Kiểm tra `"_" not in sentence` trước khi ghi file.

## 8. Kiểm tra ngữ nghĩa

### 8.1 Điều kiện bắt buộc

Một ứng viên chỉ được giữ nếu **tất cả** điều kiện sau đúng:

| # | Điều kiện | Cách kiểm tra |
|---|---|---|
| 1 | Không chứa `_` | `"_" not in sentence` |
| 2 | Không rỗng, 3–25 token | đếm token |
| 3 | Không có `? ?`, `! !`, `? !` | regex |
| 4 | Không bắt đầu bằng `?`/`!` | regex |
| 5 | Parse được strict | `parser.parse(sentence)` khác `None` |
| 6 | Intent khác `UNKNOWN` | `analyzer.analyze()` |
| 7 | Entity tồn tại trong KB | kiểm tra theo loại |
| 8 | KB trả lời được | `answer.status == OK` |
| 9 | Không phải câu trả lời generic | không chứa “Vui lòng cho biết”, “Xem danh sách đầy đủ” |
| 10 | Không trùng câu đã có | so sánh dạng normalized |
| 11 | Không chứa token lạ | token thuộc lexicon/stopword/số/ID |

### 8.2 Kiểm tra entity theo loại

```python
def entities_are_valid(entities, kb):
    if "chapter" in entities:
        return entities["chapter"] in kb.chapters          # CH01..CH12
    if "week" in entities:
        return entities["week"] in kb.schedule              # WEEK_01..WEEK_15
    if "topic" in entities:
        return entities["topic"] in kb.topic_index          # alias có thật
    if "lo" in entities:
        return entities["lo"] in kb.learning_outcomes       # LO1..LO4.2
    if "part" in entities:
        return entities["part"] in kb.assignment.parts      # PART_I..PART_IV
    if "rule" in entities:
        return entities["rule"] in kb.regulations
    return True
```

Lưu ý: `PCFG` là topic hợp lệ; `Tuần 30`, `Chương 15`, `LO4.3` là **không hợp lệ** và phải bị loại khỏi samples (dù vẫn dùng trong test no-info của Part 5).

### 8.3 Kiểm tra câu trả lời

Không chấp nhận câu sinh ra mà KB trả về:

```text
Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu môn học.
Vui lòng cho biết tuần cụ thể.
Tài liệu tham khảo: 4 cuốn sách. Xem danh sách đầy đủ trong resources.txt
Bài tập lớn 'Intelligent Course Assistant' - Nhóm 3-4 sinh viên.
```

Đây là các câu trả lời generic/không đúng trọng tâm. Part 3 sẽ sửa KB để trả lời cụ thể; Part 2 dùng `answer.status` và `answer.evidence` để lọc.

### 8.4 Bộ lọc câu vô nghĩa

Ngoài các điều kiện trên, loại thêm nếu:

- Câu chỉ có 1–2 token.
- Có hai danh từ không liên quan cạnh nhau mà không có giới từ/động từ (heuristic).
- Có `có` + `?` mà không có danh từ/động từ mang nghĩa.
- Có số đứng một mình ở đầu câu (`1 có ?`).
- Có token không nằm trong lexicon, trừ số, ID, tên riêng.
- Câu không chứa ít nhất một trong các từ khóa miền: `môn`, `chương`, `tuần`, `bài tập`, `tài liệu`, `quy định`, `deadline`, `L.O.`, `tín chỉ`, `phần`, `CFG`, `PCFG`, ...

## 9. Định dạng `output/samples.txt`

### 9.1 Khuyến nghị

`output/samples.txt` chỉ chứa **một câu mỗi dòng**, không comment, không header:

```text
Môn NLP có bao nhiêu tín chỉ?
CO3085 có mấy tín chỉ?
Tuần 3 học những gì?
Chương nào học về PCFG?
Phần I của bài tập lớn cần xuất những file gì?
L.O.2.5 liên quan đến nội dung gì?
```

Lý do:

- Đếm số câu đơn giản: `Get-Content samples.txt | Measure-Object -Line`.
- Không lẫn metadata vào dữ liệu.
- Dễ dùng làm input cho parser/evaluation.

Metadata (intent, entity, template id, seed) ghi riêng:

```text
output/samples.meta.jsonl
```

Ví dụ một dòng:

```json
{"sentence":"Tuần 3 học những gì?","intent":"GET_SCHEDULE","entities":{"week":"WEEK_03"},"source":"template","template_id":"SCHEDULE_WEEK_01"}
```

Nếu giảng viên yêu cầu nhãn intent ngay trong `samples.txt`, dùng TSV thống nhất cho **tất cả** các dòng:

```text
Tuần 3 học những gì?	GET_SCHEDULE	WEEK_03
```

Không trộn kiểu có nhãn và không nhãn như hiện tại.

### 9.2 Quy tắc ghi file

```python
def write_samples(path, records):
    assert len(records) <= 10000
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            assert "_" not in r.sentence
            f.write(r.sentence + "\n")
```

- `newline="\n"` để ổn định giữa Windows/Linux.
- Không ghi dòng trống.
- Không ghi comment.
- Không ghi quá 10.000 dòng.

## 10. Thiết kế module `src/generator.py`

### 10.1 API

```python
from dataclasses import dataclass, field

@dataclass
class SampleRecord:
    sentence: str
    intent: str
    entities: dict = field(default_factory=dict)
    source: str = "template"       # template | grammar
    template_id: str = ""
    seed: int = 42

@dataclass
class GenerationStats:
    total: int
    by_intent: dict
    by_source: dict
    rejected: dict
    duplicates: int

def generate_samples(kb, parser, analyzer, limit=10000, seed=42) -> tuple[list[SampleRecord], GenerationStats]:
    ...

def write_samples(path: str, records: list[SampleRecord]) -> None:
    ...
```

### 10.2 Các hàm nội bộ

| Hàm | Nhiệm vụ |
|---|---|
| `_iter_frames(kb)` | Sinh frame + slot hợp lệ từ KB |
| `_render(frame, values)` | Thay slot, detokenize |
| `_generate_grammar_variants(frame, rng)` | Sinh biến thể từ grammar hẹp |
| `_validate(sentence, expected_intent, kb, parser, analyzer)` | Kiểm tra 11 điều kiện |
| `_normalize_key(sentence)` | Chuẩn hóa để chống trùng |
| `_select(records, limit)` | Chọn theo quota, đa dạng hóa |
| `_stats(records)` | Thống kê coverage |

### 10.3 Pseudo-code

```python
def generate_samples(kb, parser, analyzer, limit=10000, seed=42):
    rng = random.Random(seed)
    accepted = []
    seen = set()
    rejected = defaultdict(int)
    stats = GenerationStats(0, {}, {}, rejected, 0)

    for frame in _iter_frames(kb):
        if len(accepted) >= limit:
            break
        for values in _slot_combinations(frame, kb, rng):
            sentence = _render(frame, values)
            key = _normalize_key(sentence)
            if key in seen:
                stats.duplicates += 1
                continue
            ok, reason = _validate(sentence, frame["intent"], kb, parser, analyzer)
            if not ok:
                rejected[reason] += 1
                continue
            seen.add(key)
            accepted.append(SampleRecord(
                sentence=sentence,
                intent=frame["intent"],
                entities=_entities_for(frame, values),
                source=frame.get("source", "template"),
                template_id=frame["id"],
                seed=seed,
            ))
            if len(accepted) >= limit:
                break

    accepted = _select(accepted, limit)
    return accepted, _stats(accepted)
```

Điểm quan trọng: vòng lặp dừng khi đủ `limit`, không sinh thừa rồi cắt.

### 10.4 Tích hợp vào `main.save_outputs()`

Thay:

```python
template_sentences = generate_template_sentences()
grammar_sentences = grammar.generate_all_sentences(max_sentences=10000)
# ghi cả hai
```

bằng:

```python
from .generator import generate_samples, write_samples

records, stats = generate_samples(
    kb=assistant.knowledge_base,
    parser=assistant.parser,
    analyzer=assistant.semantic_analyzer,
    limit=10000,
    seed=42,
)
write_samples(os.path.join(output_dir, "samples.txt"), records)
```

`generate_template_sentences()` và `generate_all_sentences()` có thể giữ cho demo/debug, nhưng **không dùng** để tạo file nộp.

## 11. Kế hoạch triển khai

| Bước | Việc làm | Kết quả |
|---|---|---|
| 1 | Chốt `detokenize()` từ Part 1 | Hàm dùng chung |
| 2 | Định nghĩa `SampleRecord`, `GenerationStats` | API rõ ràng |
| 3 | Viết frame + template cho 8 intent | Ứng viên có nghĩa |
| 4 | Viết grammar sinh hẹp | Biến thể hợp lệ |
| 5 | Viết `_validate()` 11 điều kiện | Lọc câu rác |
| 6 | Viết quota + chống trùng | Đa dạng, ≤ 10.000 |
| 7 | Tích hợp `save_outputs()` | File mới |
| 8 | Viết `tests/test_generator.py` | Pass acceptance |
| 9 | Sinh lại `samples.txt`, kiểm tra thủ công 100 câu | Chất lượng |

Ước lượng: **2–3 ngày**.

## 12. Test plan

### 12.1 Unit test

| # | Test | Kỳ vọng |
|---|---|---|
| 1 | `len(records) <= 10000` | Đúng |
| 2 | `"_" not in sentence` với mọi record | Đúng |
| 3 | Không có câu trùng sau normalize | `len(seen) == len(records)` |
| 4 | Mọi câu parse được | `parser.parse()` khác `None` |
| 5 | Mọi intent khác `UNKNOWN` | Đúng |
| 6 | Mọi entity hợp lệ | Đúng |
| 7 | Mọi answer có `status == OK` | Đúng |
| 8 | Cùng seed → cùng output | Hash giống |
| 9 | Không có câu bắt đầu bằng `?` | Đúng |
| 10 | Không có `? ?` / `! !` | Đúng |

### 12.2 Kiểm tra coverage

```python
assert stats.by_intent["GET_TOPIC"] >= 2000
assert stats.by_intent["GET_SCHEDULE"] >= 1500
assert len({r.entities.get("week") for r in records}) >= 15
assert len({r.entities.get("chapter") for r in records}) >= 12
assert len({r.entities.get("lo") for r in records}) >= 16
```

### 12.3 Kiểm tra thủ công

Lấy ngẫu nhiên 100 câu (seed cố định), đọc và đánh dấu:

- 0 câu vô nghĩa.
- 0 câu sai ngữ pháp.
- 0 câu có `_`.
- 0 câu trả lời generic.
- 0 câu trùng ý hoàn toàn.

Ghi kết quả vào `docs/generation-review.md`.

### 12.4 So sánh baseline

| Chỉ số | Baseline | Mục tiêu |
|---|---:|---:|
| Số câu | 10.069 | ≤ 10.000 |
| Câu có `_` | 6.508 | 0 |
| Câu vô nghĩa (mẫu 100) | > 30 | 0 |
| Câu parse được | 100% (nhờ fallback) | 100% (strict) |
| Câu có intent hợp lệ | không đo | 100% |
| Câu trả lời được | không đo | 100% |

## 13. Acceptance criteria

- [ ] `output/samples.txt` có **≤ 10.000 dòng câu**, không tính comment/rỗng.
- [ ] Không còn dòng nào chứa `_`.
- [ ] Không còn câu vô nghĩa trong 100 câu kiểm tra ngẫu nhiên.
- [ ] 100% câu parse được bằng parser strict.
- [ ] 100% câu có intent khác `UNKNOWN`.
- [ ] 100% entity tồn tại trong KB.
- [ ] 100% câu có câu trả lời cụ thể, không rơi vào fallback.
- [ ] Không có câu trùng sau chuẩn hóa.
- [ ] Cùng seed sinh lại cho cùng file (hash ổn định).
- [ ] Có thống kê coverage theo intent/chương/tuần/topic/LO.
- [ ] `pytest tests/test_generator.py` pass.
- [ ] `--mode generate` sinh lại file, không chỉnh tay.

## 14. Rủi ro và lưu ý

- **Parser strict quá chặt:** nếu Part 1 làm parser từ chối nhiều câu đúng, generator sẽ thiếu câu. Cần chạy song song Part 1 và Part 2, bổ sung lexicon/grammar thay vì nới lỏng validator.
- **KB chưa đủ dữ liệu:** nếu Part 3 chưa xong, nhiều frame không sinh được (ví dụ `suggested_outputs`). Làm Part 3 trước hoặc dùng interface KB tạm.
- **Quota cứng gây lặp:** nếu một intent không đủ biến thể, đừng sinh câu rác cho đủ; giảm quota và ghi rõ trong báo cáo.
- **Câu đúng cú pháp nhưng sai ngữ nghĩa:** validator dựa trên intent/entity/KB là chốt chặn chính; không chỉ dựa vào parser.
- **Đa dạng quá mức:** 10.000 câu có thể vượt nhu cầu; ưu tiên phủ entity hơn là số lượng.
- **Không dùng `random` toàn cục:** nếu các module khác cũng gọi `random`, kết quả sẽ không tái lập.
- **Không ghi metadata vào `samples.txt`:** nếu cần nhãn, dùng file riêng hoặc TSV thống nhất.
