# PART 4 — Tích hợp DialogueManager thật sự

## 1. Mục tiêu

Sau bước này:

1. `CourseAssistant.process_dialogue()` dùng `DialogueManager` làm nguồn trạng
   thái duy nhất, không còn dict ad-hoc.
2. Lưu đúng:
   - `last_week`
   - `last_chapter`
   - `last_topic`
   - `last_assignment`
   - `last_part`
   - `last_lo`
3. Resolve được:
   - `phần này`, `phần đó`
   - `nó`
   - `chương này`, `chương đó`
   - `nội dung này`
   - `tuần này`
   - `chương sau`, `chương trước`
   - `còn chương sau?`
4. Nếu không resolve được, hệ thống hỏi lại rõ ràng thay vì trả lời sai.
5. `output/dialogue.txt` được sinh lại từ code hiện tại, dùng 5 kịch bản mẫu
   trong `data/dialogues.txt`.

## 2. Phạm vi file

| File | Vai trò |
|---|---|
| `src/dialogue.py` | `DialogueManager`, state, resolver |
| `src/main.py` | `CourseAssistant.process_dialogue()`, `save_outputs()` |
| `src/semantic.py` | Nhận entity đã resolve, merge với entity hiện tại |
| `src/knowledge_base.py` | Trả lời theo entity đã resolve |
| `data/dialogues.txt` | 5 kịch bản mẫu (từ `NLP_Sample_Data`) |
| `output/dialogue.txt` | Kết quả sinh lại |
| `tests/test_dialogue.py` (mới) | Test resolver + integration |

## 3. Hiện trạng và lỗi gốc

### 3.1 `DialogueManager` tồn tại nhưng không được dùng

`src/dialogue.py` có:

```python
@dataclass
class DialogueState:
    turn: int = 0
    last_intent: str = ""
    last_topic: Optional[str] = None
    last_chapter: Optional[str] = None
    last_week: Optional[str] = None
    entities: Dict[str, DiscourseEntity] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
```

Nhưng `src/main.py` không dùng. `CourseAssistant.process_dialogue()` tự làm:

```python
current_context = context or {}
processed_input = user_input

if 'phần này' in user_input.lower() or ' nó ' in user_input.lower():
    if 'last_topic' in current_context:
        processed_input = user_input.replace('phần này', current_context['last_topic'])
        processed_input = processed_input.replace('nó', current_context['last_topic'])

if 'chương này' in user_input.lower():
    if 'last_chapter' in current_context:
        processed_input = user_input.replace('chương này', current_context['last_chapter'])

result = self.process_query(processed_input)

if result['entities'].get('chapter'):
    current_context['last_chapter'] = result['entities']['chapter']
if result['entities'].get('topic'):
    current_context['last_topic'] = result['entities']['topic']
```

Vấn đề:

- Không lưu `last_week`, `last_assignment`, `last_part`, `last_lo`.
- Thay `phần này` bằng `last_topic` (ví dụ `PARSING`) thay vì entity phù hợp.
- Thay `chương này` bằng `CH04` — semantic analyzer không hiểu `CH04`,
  chỉ hiểu `chương 4`.
- `nó` bị thay bằng `last_topic` ngay cả khi câu hỏi cần `last_chapter`.
- Không có precedence giữa entity hiện tại và entity kế thừa.
- Không có clarification khi thiếu antecedent.
- `DialogueManager` có `resolve_reference()` nhưng không được gọi.

### 3.2 Lỗi thực tế đã tái hiện

Chạy 6 lượt liên tiếp:

```text
U: Tuần 3 học gì?
A: Tuần 03: Học Chương 03 - Grammar and Parsing...
ctx: {}

U: Tài liệu của phần này ở đâu?
A: Tài liệu tham khảo: 4 cuốn sách...
ctx: {}
```

→ `last_week` không được lưu; `phần này` không resolve.

```text
U: Chương 4 nói về gì?
A: Chương 04 - Features and Augmented Grammar...
ctx: {'last_chapter': 'CH04'}

U: Nó có liên quan đến parsing không?
A: Các quy định: Sinh viên được khuyến khích...
ctx: {'last_topic': 'PARSING'}
```

→ `nó` không được resolve trước semantic; `không` kích hoạt `GET_RULE`.

```text
U: Bài tập lớn có phần parser không?
A: Bài tập lớn 'Intelligent Course Assistant' - Nhóm 3-4 sinh viên.
ctx: {}

U: Phần này cần xuất file gì?
A: Bài tập lớn 'Intelligent Course Assistant' - Nhóm 3-4 sinh viên.
ctx: {}
```

→ Không lưu `last_part`; `phần này` không resolve; KB cũng thiếu output.

### 3.3 `DialogueManager` hiện tại còn thiếu

- `resolve_reference()` chỉ xử lý `definite_phrase` và `pronoun`, không xử lý
  `chương sau`, `nội dung này`, `còn chương sau?`.
- Không có `last_part`, `last_assignment`, `last_lo`.
- Không cập nhật `last_mentioned_at`/`salience` khi entity được nhắc lại.
- Không có `ResolutionResult` (antecedent, confidence, clarification).
- `update_context()` chỉ thêm entity, không xóa/giảm salience entity cũ.
- `reference_patterns["pronoun"]` có `"bạn"`, `"tôi"`, `"mình"` — đây là
  đại từ nhân xưng hội thoại, không phải tham chiếu ngữ nghĩa; dễ resolve sai.
- `reference_patterns["ellipsis"]` có `"ở đâu"`, `"là gì"`, `"có không"` —
  đây là dấu hiệu câu hỏi, không phải ellipsis.

## 4. Thiết kế đích

### 4.1 Trạng thái hội thoại mở rộng

```python
@dataclass
class DialogueState:
    turn: int = 0
    last_intent: str = ""
    last_query: str = ""
    last_answer: str = ""

    last_week: Optional[str] = None          # WEEK_03
    last_chapter: Optional[str] = None       # CH03
    last_topic: Optional[str] = None         # PCFG, SEMANTIC_GRAMMAR
    last_assignment: Optional[str] = None    # BTL01
    last_part: Optional[str] = None          # PART_I
    last_lo: Optional[str] = None            # LO2.5
    last_resource: Optional[str] = None      # R01

    entities: dict[str, DiscourseEntity] = field(default_factory=dict)
    history: list[Turn] = field(default_factory=list)
```

`DiscourseEntity`:

```python
@dataclass
class DiscourseEntity:
    entity_type: str          # week | chapter | topic | assignment | part | lo
    value: str                # WEEK_03 | CH03 | PCFG | PART_I | LO2.5
    display: str              # "tuần 3" | "chương 3" | "PCFG" | "phần I"
    mention: str              # câu người dùng đã nói
    introduced_at: int
    last_mentioned_at: int
    salience: float = 1.0
```

Quy tắc salience:

- Entity mới: `salience = 1.0`.
- Entity được nhắc lại: `salience = min(1.0, salience + 0.3)`,
  `last_mentioned_at = turn`.
- Mỗi turn: tất cả entity cũ giảm `salience *= 0.9`.
- Khi resolve `nó`, chọn entity có `salience` cao nhất trong các loại phù hợp.

### 4.2 `ResolutionResult`

```python
@dataclass
class ResolutionResult:
    resolved_query: str
    entities: dict[str, str]          # entity kế thừa
    reference_type: str               # pronoun | demonstrative | definite | ellipsis | ordinal
    antecedent: Optional[str]         # giá trị được resolve
    confidence: float                 # 0..1
    needs_clarification: bool = False
    clarification: str = ""
```

### 4.3 Luồng xử lý

```text
raw query
   │
   ▼
preprocess (tokenize, normalize)
   │
   ▼
DialogueManager.resolve_reference(query, state)
   │  - phát hiện cụm tham chiếu
   │  - tìm antecedent theo loại + salience
   │  - trả resolved_query + inherited entities
   ▼
SemanticAnalyzer.analyze(resolved_query)
   │  - entity hiện tại (explicit) được ưu tiên
   ▼
merge(explicit_entities, inherited_entities)
   │  - explicit thắng nếu cùng key
   ▼
KnowledgeBase.query(intent, merged_entities)
   │
   ▼
DialogueManager.update_context(query, intent, merged_entities, answer)
   │  - cập nhật last_*
   │  - thêm history
   ▼
answer + state
```

Điểm quan trọng: **resolve trước semantic**. Nếu resolve sau, semantic sẽ thấy
`nó`/`không` và phân loại sai (như lỗi `GET_RULE` hiện tại).

### 4.4 Quy tắc resolve từng loại

| Cụm | Loại | Antecedent ưu tiên | Fallback | Nếu không có |
|---|---|---|---|---|
| `chương này`, `chương đó` | definite | `last_chapter` | `last_topic` → chapter qua KB | `NEEDS_CLARIFICATION` |
| `tuần này`, `tuần đó` | definite | `last_week` | `last_chapter` → week qua KB | `NEEDS_CLARIFICATION` |
| `phần này`, `phần đó` | definite | Nếu `last_intent == GET_ASSIGNMENT` → `last_part`; ngược lại `last_topic` | `last_chapter` | `NEEDS_CLARIFICATION` |
| `nó` | pronoun | `last_chapter` nếu câu hỏi về chương/nội dung; `last_topic` nếu câu hỏi về topic; `last_part` nếu câu hỏi về BTL | entity salience cao nhất | `NEEDS_CLARIFICATION` |
| `nội dung này` | definite | `last_topic` | `last_chapter` | `NEEDS_CLARIFICATION` |
| `bài này`, `bài tập này` | definite | `last_assignment` | `last_part` | `NEEDS_CLARIFICATION` |
| `chương sau` | ordinal | `last_chapter` + 1 | — | `NOT_FOUND` nếu > 12 |
| `chương trước` | ordinal | `last_chapter` - 1 | — | `NOT_FOUND` nếu < 1 |
| `còn chương sau?` | ellipsis | `last_chapter` + 1 | — | `NEEDS_CLARIFICATION` |
| `ở đâu`, `là gì`, `có không` | **không phải reference** | — | — | — |

Lưu ý:

- `"bạn"`, `"tôi"`, `"mình"` không phải antecedent ngữ nghĩa; bỏ khỏi danh sách
  pronoun.
- `"ở đâu"`, `"là gì"`, `"có không"` là dấu hiệu câu hỏi, không phải ellipsis;
  bỏ khỏi `reference_patterns`.
- `"nó"` phải xét ngữ cảnh câu hỏi:
  - `Nó có liên quan đến parsing không?` → chương/topic.
  - `Nó cần xuất file gì?` → part/assignment.
  - `Nó học vào tuần nào?` → chapter.
- Nếu câu hỏi có entity explicit (ví dụ `Chương 4 ...`), không resolve `nó`
  từ context; explicit thắng.

### 4.5 Resolve theo loại câu hỏi

```python
def _preferred_types(query: str, intent_hint: str | None) -> list[str]:
    q = query.lower()
    if "file" in q or "output" in q or "xuất" in q:
        return ["part", "assignment"]
    if "tuần" in q:
        return ["week", "chapter"]
    if "chương" in q:
        return ["chapter", "topic"]
    if "tài liệu" in q:
        return ["topic", "chapter"]
    if "quy định" in q:
        return ["rule"]
    if "l.o." in q or "lo" in q:
        return ["lo", "chapter"]
    return ["chapter", "topic", "week", "part", "assignment", "lo"]
```

### 4.6 Rewrite query

Không thay bằng canonical ID trần. Thay bằng **dạng hiển thị tự nhiên**:

```python
REPLACEMENTS = {
    "chapter": lambda v: f"chương {int(v[2:])}",
    "week": lambda v: f"tuần {int(v[5:])}",
    "part": lambda v: f"phần {v.split('_')[1]}",
    "lo": lambda v: f"L.O.{v[2:]}",
    "topic": lambda v: v.replace("_", " ").lower(),
    "assignment": lambda v: "bài tập lớn",
}
```

Ví dụ:

```text
"Tài liệu của chương này ở đâu?"
-> "Tài liệu của chương 3 ở đâu?"
```

Không rewrite thành:

```text
"Tài liệu của CH03 ở đâu?"   # semantic không hiểu
```

### 4.7 Merge entity

```python
def merge_entities(explicit: dict, inherited: dict) -> dict:
    merged = dict(inherited)
    merged.update(explicit)   # explicit thắng
    return merged
```

Quy tắc:

- Nếu câu hiện tại nói `Chương 4`, không kế thừa `last_chapter = CH03`.
- Nếu câu hiện tại nói `PCFG`, không kế thừa `last_topic = CFG`.
- Nếu câu hiện tại không nói chapter nhưng resolve `chương này`, dùng inherited.
- Không kế thừa `week` khi câu hỏi là `GET_RESOURCE` nếu đã resolve `chapter`;
  tránh entity rác.

### 4.8 Cập nhật state sau mỗi turn

| Intent | Cập nhật |
|---|---|
| `GET_SCHEDULE` + `week` | `last_week = week`; `last_chapter = week.chapter` (nếu có) |
| `GET_SCHEDULE` + `chapter` | `last_chapter = chapter`; `last_week` = tuần đầu tiên của chapter |
| `GET_TOPIC` + `chapter` | `last_chapter = chapter`; nếu có topic, `last_topic = topic` |
| `GET_TOPIC` + `topic` | `last_topic = topic`; `last_chapter` = chapter khớp đầu tiên (nếu duy nhất) |
| `GET_ASSIGNMENT` + `part` | `last_assignment = BTL01`; `last_part = part` |
| `GET_ASSIGNMENT` + `list_parts` | `last_assignment = BTL01` |
| `GET_LO` + `lo` | `last_lo = lo`; nếu LO map chapter, `last_chapter = chapter` |
| `GET_RESOURCE` + `topic` | `last_topic = topic`; không đổi `last_chapter` nếu không rõ |
| `GET_DEADLINE` | `last_assignment = BTL01` |
| `UNKNOWN` | không cập nhật entity, chỉ tăng turn |

Không xóa entity cũ ngay; dùng salience decay. Khi resolve, nếu salience thấp
hơn ngưỡng (ví dụ < 0.3), coi như không có antecedent.

## 5. Refactor `src/dialogue.py`

### 5.1 API mới

```python
class DialogueManager:
    def __init__(self, kb=None):
        self.state = DialogueState()
        self.kb = kb

    def reset(self) -> None: ...

    def resolve_reference(self, query: str) -> ResolutionResult:
        ...

    def update_context(
        self,
        query: str,
        intent: str,
        entities: dict,
        answer: str,
    ) -> None:
        ...

    def get_state_summary(self) -> dict:
        ...

    def get_history(self, limit: int = 5) -> list[dict]:
        ...
```

### 5.2 `resolve_reference()` pseudo-code

```python
def resolve_reference(self, query: str) -> ResolutionResult:
    q = query.lower()
    result = ResolutionResult(
        resolved_query=query,
        entities={},
        reference_type="",
        antecedent=None,
        confidence=0.0,
    )

    # 1. Ordinal: chương sau / chương trước
    if "chương sau" in q or "còn chương sau" in q:
        if not self.state.last_chapter:
            return self._clarify(query, "Bạn đang nói đến chương nào?")
        nxt = int(self.state.last_chapter[2:]) + 1
        if nxt > 12:
            return self._not_found(query, "Không có chương sau chương 12.")
        return self._resolved(query, "chapter", f"CH{nxt:02d}", "ordinal", 1.0)

    if "chương trước" in q:
        ...

    # 2. Definite phrases
    for phrase, etype in [
        ("chương này", "chapter"), ("chương đó", "chapter"),
        ("tuần này", "week"), ("tuần đó", "week"),
        ("phần này", "part"), ("phần đó", "part"),
        ("nội dung này", "topic"), ("bài này", "assignment"),
    ]:
        if phrase in q:
            value = self._pick(etype)
            if value:
                return self._resolved(query, etype, value, "definite", 0.9)
            return self._clarify(query, f"Bạn đang nói đến {etype} nào?")

    # 3. Pronoun "nó"
    if re.search(r"\bnó\b", q):
        etype = self._infer_type_from_query(q)
        value = self._pick(etype)
        if value:
            return self._resolved(query, etype, value, "pronoun", 0.7)
        return self._clarify(query, "Bạn đang nói đến đối tượng nào?")

    return result
```

### 5.3 `_pick()` theo salience + loại

```python
def _pick(self, etype: str) -> str | None:
    candidates = [
        e for e in self.state.entities.values()
        if e.entity_type == etype and e.salience >= 0.3
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda e: (e.salience, e.last_mentioned_at)).value
```

### 5.4 `_resolved()` rewrite query

```python
def _resolved(self, query, etype, value, rtype, confidence):
    display = self._display(etype, value)
    resolved_query = self._replace_reference(query, display)
    return ResolutionResult(
        resolved_query=resolved_query,
        entities={etype: value},
        reference_type=rtype,
        antecedent=value,
        confidence=confidence,
    )
```

`_replace_reference()` chỉ thay cụm tham chiếu đầu tiên, không thay toàn bộ
câu, để giữ ngữ pháp.

### 5.5 `update_context()` nâng salience

```python
def update_context(self, query, intent, entities, answer):
    self.state.turn += 1
    self.state.last_intent = intent
    self.state.last_query = query
    self.state.last_answer = answer

    for e in self.state.entities.values():
        e.salience *= 0.9

    for etype, value in entities.items():
        if etype not in {"week", "chapter", "topic", "assignment", "part", "lo"}:
            continue
        existing = self.state.entities.get(etype)
        if existing and existing.value == value:
            existing.last_mentioned_at = self.state.turn
            existing.salience = min(1.0, existing.salience + 0.3)
        else:
            self.state.entities[etype] = DiscourseEntity(
                entity_type=etype,
                value=value,
                display=self._display(etype, value),
                mention=query,
                introduced_at=self.state.turn,
                last_mentioned_at=self.state.turn,
                salience=1.0,
            )

    self._update_last_fields(intent, entities)
    self.state.history.append({
        "turn": self.state.turn,
        "query": query,
        "intent": intent,
        "entities": dict(entities),
        "answer": answer,
    })
```

### 5.6 `_update_last_fields()`

```python
def _update_last_fields(self, intent, entities):
    if "week" in entities:
        self.state.last_week = entities["week"]
        chapter = self.kb.chapter_by_week.get(entities["week"]) if self.kb else None
        if chapter:
            self.state.last_chapter = chapter
    if "chapter" in entities:
        self.state.last_chapter = entities["chapter"]
    if "topic" in entities:
        self.state.last_topic = entities["topic"]
    if "assignment" in entities:
        self.state.last_assignment = entities["assignment"]
    if "part" in entities:
        self.state.last_part = entities["part"]
        self.state.last_assignment = "BTL01"
    if "lo" in entities:
        self.state.last_lo = entities["lo"]
```

## 6. Refactor `CourseAssistant.process_dialogue()`

### 6.1 API

Giữ tương thích với `run_interactive()`:

```python
def process_dialogue(self, user_input: str, context: dict | None = None) -> tuple[str, dict]:
```

Nhưng `context` chỉ là **view** của `DialogueManager.state`; nguồn sự thật là
manager.

Khuyến nghị thêm:

```python
def __init__(...):
    ...
    self.dialogue = DialogueManager(kb=self.knowledge_base)

def process_dialogue(self, user_input, context=None):
    if context is not None:
        self.dialogue.state = DialogueState(**context)  # hoặc restore
    result = self.dialogue.resolve_reference(user_input)
    if result.needs_clarification:
        return result.clarification, self.dialogue.get_state_summary()

    sem = self.semantic_analyzer.analyze(result.resolved_query)
    merged = merge_entities(sem.entities, result.entities)
    answer = self.knowledge_base.query(sem.intent.value, merged)
    self.dialogue.update_context(user_input, sem.intent.value, merged, answer.text)
    return answer.text, self.dialogue.get_state_summary()
```

Lưu ý: nếu giữ `context` dict, phải map đúng các key `last_week`,
`last_chapter`, `last_topic`, `last_assignment`, `last_part`, `last_lo`.

### 6.2 Không resolve khi có entity explicit

```python
if sem.entities:
    merged = dict(result.entities)
    merged.update(sem.entities)   # explicit thắng
```

Nếu câu hỏi là `Chương 4 nói về gì?`, không resolve `nó`/`chương này` từ
context cũ.

### 6.3 Xử lý `needs_clarification`

Trả về câu hỏi lại, không gọi KB:

```text
Bạn đang nói đến chương nào? (Ví dụ: "Chương 4 nói về gì?")
```

Không trả `UNKNOWN` chung chung.

## 7. Sinh `output/dialogue.txt`

### 7.1 Nguồn kịch bản

Dùng 5 kịch bản trong `data/dialogues.txt`:

```text
DIALOGUE 01
U1: Tuần 3 học gì?
U2: Tài liệu của chương này là gì?
EXPECTED_REFERENCE: "chương này" -> CH03

DIALOGUE 02
U1: Chương 4 nói về gì?
U2: Nó có liên quan đến parsing không?
EXPECTED_REFERENCE: "Nó" -> CH04

DIALOGUE 03
U1: Bài tập lớn có phần parser không?
U2: Phần này cần xuất file gì?
EXPECTED_REFERENCE: "Phần này" -> PART_I_GRAMMAR_PARSER

DIALOGUE 04
U1: Chương 11 có hỏi đáp không?
U2: Còn chương sau?
EXPECTED_REFERENCE: "chương sau" -> CH12

DIALOGUE 05
U1: L.O.2.5 học về gì?
U2: Nội dung này nằm ở chương nào?
EXPECTED_REFERENCE: "Nội dung này" -> LO2.5
```

### 7.2 Định dạng file

```text
DIALOGUE EXAMPLES
=================

DIALOGUE 01
-----------
Turn 1
User: Tuần 3 học gì?
Intent: GET_SCHEDULE
Entities: {"week": "WEEK_03", "chapter": "CH03"}
Answer: Tuần 03 học Chương 03 - Grammar and Parsing. Nội dung: ...

Turn 2
User: Tài liệu của chương này là gì?
Resolved reference: "chương này" -> CH03 (confidence=0.90)
Resolved query: Tài liệu của chương 3 là gì?
Intent: GET_RESOURCE
Entities: {"chapter": "CH03", "topic": "CFG"}
Answer: Tài liệu về CFG/parsing: ...

State after turn: last_week=WEEK_03, last_chapter=CH03, last_topic=CFG
```

Yêu cầu:

- Có `Resolved reference` và `Resolved query` để chứng minh resolve.
- Có `Intent`, `Entities`, `Answer`.
- Có `State after turn` với các `last_*`.
- Không chỉnh tay; sinh bằng `python -m src.main --mode generate`.

### 7.3 Thêm case clarification

Thêm một dialogue:

```text
DIALOGUE 06
U1: Nó có liên quan đến parsing không?
A1: Bạn đang nói đến chương/topic nào? ...
```

Mục đích: chứng minh hệ thống không resolve bừa khi không có antecedent.

### 7.4 Thêm case no-info

```text
DIALOGUE 07
U1: Tuần 30 học gì?
A1: Tuần 30 không nằm trong lịch 15 tuần của môn học.
U2: Còn tuần 31?
A2: Tuần 31 không nằm trong lịch 15 tuần của môn học.
```

## 8. Test plan

### 8.1 Unit test resolver

| # | Query | State trước | Kỳ vọng |
|---|---|---|---|
| 1 | `Tài liệu của chương này ở đâu?` | `last_chapter=CH03` | resolved `chương 3`, entity `chapter=CH03` |
| 2 | `Nó có liên quan đến parsing không?` | `last_chapter=CH04` | resolved `chương 4`, entity `chapter=CH04`, intent `GET_TOPIC` |
| 3 | `Phần này cần xuất file gì?` | `last_part=PART_I` | resolved `phần I`, entity `part=PART_I` |
| 4 | `Còn chương sau?` | `last_chapter=CH11` | resolved `chương 12`, entity `chapter=CH12` |
| 5 | `Chương trước?` | `last_chapter=CH01` | `NOT_FOUND` / clarification |
| 6 | `Nội dung này nằm ở chương nào?` | `last_lo=LO2.5` | entity `lo=LO2.5`, answer CH06 |
| 7 | `Nó là gì?` | state rỗng | `NEEDS_CLARIFICATION` |
| 8 | `Chương này nói về gì?` | state rỗng | `NEEDS_CLARIFICATION` |
| 9 | `Chương 4 nói về gì?` | `last_chapter=CH03` | explicit `CH04`, không kế thừa CH03 |
| 10 | `Tuần này học gì?` | `last_week=WEEK_03` | entity `week=WEEK_03` |

### 8.2 Integration test 5 kịch bản

| Dialogue | Turn 2 kỳ vọng |
|---|---|
| 01 | `GET_RESOURCE`, entity `chapter=CH03`, answer tài liệu CFG/parsing |
| 02 | `GET_TOPIC`, entity `chapter=CH04`, answer về parsing với features |
| 03 | `GET_ASSIGNMENT`, entity `part=PART_I`, answer 3 output file |
| 04 | `GET_TOPIC`/`GET_SCHEDULE`, entity `chapter=CH12`, answer discourse context |
| 05 | `GET_TOPIC`, entity `lo=LO2.5`, answer CH06 |

### 8.3 Regression test

- `Nó có liên quan đến parsing không?` **không còn** `GET_RULE`.
- `Tài liệu của phần này ở đâu?` **không còn** trả generic 4 sách.
- `Phần này cần xuất file gì?` **không còn** trả title/team size.
- `Tuần 30` **không còn** “Vui lòng cho biết tuần cụ thể”.

### 8.4 Test state

```python
def test_state_after_turn():
    dm = DialogueManager(kb)
    dm.update_context("Tuần 3 học gì?", "GET_SCHEDULE", {"week": "WEEK_03"}, "...")
    assert dm.state.last_week == "WEEK_03"
    assert dm.state.last_chapter == "CH03"
```

## 9. Kế hoạch triển khai

| Bước | Việc làm | Kết quả |
|---|---|---|
| 1 | Mở rộng `DialogueState`, `DiscourseEntity` | Đủ slot |
| 2 | Viết `ResolutionResult` + `resolve_reference()` | Resolve đúng |
| 3 | Viết `_pick`, `_display`, `_replace_reference` | Rewrite tự nhiên |
| 4 | Viết `update_context()` + salience | State đúng |
| 5 | Refactor `CourseAssistant.process_dialogue()` | Dùng manager |
| 6 | Merge entity explicit > inherited | Không ghi đè |
| 7 | Sinh `output/dialogue.txt` từ 5 kịch bản + 2 case | Output mới |
| 8 | Viết `tests/test_dialogue.py` | Pass |

Ước lượng: **2–3 ngày**.

## 10. Acceptance criteria

- [ ] `CourseAssistant.process_dialogue()` gọi `DialogueManager`, không dùng
      dict ad-hoc làm nguồn chính.
- [ ] `last_week`, `last_chapter`, `last_topic`, `last_assignment`, `last_part`,
      `last_lo` được lưu sau mỗi turn.
- [ ] `chương này`, `nó`, `phần này`, `nội dung này`, `chương sau` resolve đúng
      trong 5 kịch bản mẫu.
- [ ] `Nó có liên quan đến parsing không?` sau `Chương 4` trả `GET_TOPIC` +
      `CH04`, không trả `GET_RULE`.
- [ ] `Phần này cần xuất file gì?` sau `BTL có phần parser` trả `PART_I` + 3 file.
- [ ] `Tài liệu của chương này` sau `Tuần 3` trả tài liệu CH03/CFG, không generic.
- [ ] Không có antecedent → hỏi lại, không trả lời bừa.
- [ ] `output/dialogue.txt` sinh lại từ code, có `Resolved reference`,
      `Resolved query`, `State after turn`.
- [ ] `pytest tests/test_dialogue.py` pass.

## 11. Rủi ro và lưu ý

- **Resolve quá tay:** `nó` có thể trỏ đến nhiều entity; nếu confidence thấp,
  hỏi lại thay vì đoán.
- **State cũ:** salience decay giúp tránh dùng entity quá cũ, nhưng có thể làm
  mất antecedent hợp lệ; cần ngưỡng 0.3 và test.
- **Rewrite query làm mất ngữ pháp:** chỉ thay cụm tham chiếu, không thay cả câu.
- **Entity explicit vs inherited:** explicit luôn thắng; nếu không, câu
  `Chương 4 nói về gì?` sau `Chương 3` sẽ bị kế thừa sai.
- **`phần này` mơ hồ:** trong ngữ cảnh BTL → `last_part`; ngoài BTL → `last_topic`;
  cần test cả hai.
- **`chương sau` vượt 12:** trả `NOT_FOUND`, không wrap về chương 1.
- **Đồng bộ output:** `output/dialogue.txt` phải sinh từ cùng code với
  `--mode demo`/`interactive`; không viết tay.
