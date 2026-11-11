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


| Nhóm thông tin          | Nội dung                                         | Nguồn trong `src/knowledge_base.py` |
| ----------------------- | ------------------------------------------------ | ---------------------------------- |
| Thông tin chung môn học | Tên, mã, số tín chỉ, mô tả, mục tiêu             | `COURSE_INFO`                      |
| Đề cương                | 12 chương, nội dung và chủ đề từng chương        | `CHAPTERS`                         |
| Lịch học                | 15 tuần, ánh xạ tuần ↔ chương                    | `SCHEDULE`                         |
| Bài tập lớn             | 4 phần (PART_I…PART_IV), yêu cầu, file phải xuất | `ASSIGNMENT`                       |
| Quy định                | 7 nhóm quy định (dùng AI/LLM, bản quyền, …)      | `REGULATIONS`                      |
| Tài liệu tham khảo      | 7 mục sách, slide, ghi chú                       | `RESOURCES`                        |
| Câu hỏi thường gặp      | 7 câu hỏi mẫu                                   | `FAQ`                              |

> **Nguồn dữ liệu:** toàn bộ tri thức môn học do nhóm biên soạn tay dựa trên đề
> cương môn CO3085 và tài liệu giảng viên cung cấp. File `data/course_data.txt`
> là bản tóm tắt dạng văn bản của cùng bộ dữ liệu đó (để đối chiếu nhanh);
> mã nguồn không đọc file này khi chạy. Không sử dụng dữ liệu từ nguồn bên ngoài
> nào khác.




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
| `CONTEXT_DEPENDENT` | Câu hỏi phụ thuộc ngữ cảnh lượt trước | "Nó có liên quan đến parsing không?" |
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
`output/grammar.txt` (386 dòng, 36 non-terminal, 182 terminal). Cấu trúc cốt lõi:

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
NP             → COURSE_REF | CHAPTER_REF | WEEK_REF | TOPIC_NAME
               | ASSIGNMENT_NAME | TECH_NAME | LO_ID | ATTR_NOUN | PART_REF
               | DET NOMINAL | NOMINAL | PRONOUN | QUANT ATTR_NOUN | …

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
COURSE_REF     → COURSE_MOD COURSE_NAME | COURSE_NAME
COURSE_NAME    → "nlp" | "co3085" | "xử_lý_ngôn_ngữ_tự_nhiên"
CHAPTER_NUM    → "1" | "2" | … | "12"
WEEK_NUM       → "1" | "2" | … | "15"
TOPIC_NAME     → "cfg" | "pcfg" | "parsing" | "semantic" | "semantic_grammar"
               | "syntax" | "pos" | "feature" | "grammar" | "tagging"
               | "disambiguation" | …
ASSIGNMENT_NAME→ "btl" | "bài_tập_lớn" | "assignment" | "đồ_án"
LO_ID          → "l.o.1.1" | "l.o.1.2" | … | "l.o.4.2"

# Dấu câu
PUNCT          → "?" | "!"
```

> Trên đây là phần **rút gọn** cho dễ đọc; toàn bộ văn phạm (36 non-terminal,
> 182 terminal, 307 production) nằm trong `output/grammar.txt`.



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
sinh ra nhiều hơn `tra` (0.3), và luật `CHAPTER_REF → "chương" CHAPTER_NUM`
(4.0) nhiều hơn luật `CHAPTER_REF → "chương"` đứng trần (1.0). Nhờ vậy
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



#### 2.3.1 Thuật toán: Earley chart parser

Bộ phân tích cú pháp nằm trong `src/parser.py`, là **Earley chart parser**
(bottom-up, xử lý được nhập bằng tự nhiên của tiếng Việt) đọc trực tiếp văn
phạm từ `CFG`:

```
parse(text):
    tokens ← tokenize_input(text)
    tree   ← _earley_parse(tokens)
    if tree != null:
        return tree                          # phân tích thành công
    fallback ← _parse_fallback(text)         # phân tích theo mẫu
    if fallback != null:
        return fallback
    return null, errors                      # không thuộc văn phạm
```

Ba pha của Earley được cài đặt trong `_earley_parse()`:

| Pha            | Ý nghĩa                                                        |
| -------------- | -------------------------------------------------------------- |
| **Predictor** | Mở rộng item với mọi production của non-terminal ở vị trí hiện tại |
| **Scanner**    | Nếu ký hiệu tiếp theo là terminal, tiêu thụ token nếu khớp       |
| **Completer**  | Khi một production hoàn tất, "magic completion" cho mọi item đang chờ |

Bảng `complete` lưu các suy diễn `(symbol, start, stop) → [rule]`, bảng `advance`
lưu các span ứng viên cho từng vị trí dấu chấm. Vì văn phạm có nhập bằng, một
ký hiệu có thể có nhiều span; vì vậy `_build_tree()` **backtrack** qua các ứng
viên và chỉ giữ lại cách suy diễn hoàn chỉnh.

Bảng tra cứu (`_build_lookup_tables()`) và chỉ mục văn phạm
(`_build_grammar_index()`) được xây tự động từ văn phạm: danh sách terminal của
mỗi non-terminal, danh sách course name / topic / assignment / learning outcome.
Nhờ vậy **chỉ có một nguồn sự thật duy nhất** cho ngôn ngữ — tránh tình trạng
văn phạm và parser lệch nhau.

#### 2.3.2 Cơ chế dự phòng (fallback)

Không phải câu nào trong tự nhiên cũng khớp văn phạm nghiêm ngặt. Để hệ thống
vẫn trả lời được, khi Earley parser thất bại, parser chuyển sang
`_parse_fallback()`: phân loại từng token theo bảng từ khoá rồi dựng cây theo
mẫu (`WH_WORD` | `NP` | `VP` | `PUNCT`).

Cơ chế này giữ cho **intent accuracy cao** ngay cả khi strict parse thấp — vì
tầng semantic làm việc trên văn bản, không phụ thuộc cây cú pháp.

#### 2.3.3 Kết quả trên tập kiểm thử chính thức

Trên 34 câu hỏi trong `tests/data/sample_queries.txt`:


| Chế độ                    | Số câu | Tỉ lệ   |
| ------------------------- | ------ | ------- |
| Strict (Earley chart)     | 31     | 91.18 % |
| Pattern fallback          | 3      | 8.82 %  |
| Thất bại                  | 0      | 0 %     |

> **Hiện trạng.** Strict parse đã tăng từ 11.76 % lên **91.18 %** nhờ parser mới
> là **Earley chart parser** tổng quát (xem mục 2.3.1). 3 câu còn lại rơi vào
> fallback (`Q026`, `Q027`, `Q028`) là các câu **cố ý nằm ngoài phạm vi** của
> đề bài — "Hôm nay ở TP.HCM có mưa không?", "Ai là tổng thống của Pháp?" và
> "Hãy giải bài tập xác suất này giúp tôi." Trên 31 câu in-scope, strict parse
> đạt **100 %**, và cả 3 câu này vẫn được phục vụ đúng ở tầng semantic.



#### 2.3.4 Định dạng cây cú pháp

Kết quả được ghi ra `output/parse-results.txt` theo dạng cây lồng:

```
(WH_QUESTION (NP (COURSE_REF (COURSE_MOD (môn)) (COURSE_NAME (nlp))))
             (VP (VERB (có)) (NP (QUANT (bao_nhiêu)) (ATTR_NOUN (tín_chỉ))))
             (PUNCT (?)))
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
| "Môn NLP có bao nhiêu tín chỉ?" | `GET_COURSE_INFO(course=CO3085, attribute=credits)` |
| "Tuần 3 học gì?"                | `GET_SCHEDULE(week=WEEK_03)`                     |
| "Chương 4 nói về gì?"           | `GET_TOPIC(chapter=CH04)`                        |
| "Chương nào học về CFG?"        | `GET_TOPIC(topic=CFG)`                           |
| "Deadline BTL là khi nào?"      | `GET_DEADLINE(attribute=deadline, assignment=BTL01)` |
| "Có được dùng LLM không?"       | `GET_RULE(rule=LLM_RAG)`                         |
| "L.O.4.2 là gì?"                | `GET_LO(lo=LO4.2)`                               |




#### 3.1.2 Nhận diện Intent — phương pháp dựa trên luật

**Phương pháp:** khớp từ khoá + biểu thức chính quy (regex) **có trọng số** —
mỗi luật là một cặp `(intent, regex, điểm)`; điểm cao hơn thắng.

*Pseudocode:*

```
function extract_intent(text, tokens, entities):
    normalized ← normalize_text(text)

    # Bước 1: phát hiện ngoài phạm vi trước tiên
    if lexicon.is_out_of_scope(normalized):          # thời tiết, bóng đá, giá vàng, …
        return UNKNOWN
    if re.search(r"giải (bài tập|đề|bài)(?! lớn)", normalized):
        return UNKNOWN
    if re.search(r"(làm hộ|viết code cho tôi|dịch (văn bản|sang))", normalized):
        return UNKNOWN

    # Bước 2: chấm điểm các luật trong INTENT_RULES
    scores ← {}
    for (intent, pattern, score) in INTENT_RULES:
        if re.search(pattern, normalized):
            scores[intent] ← scores[intent] + score

    # Bước 3: điểm cộng theo entity đã trích, dùng để phá thế hoà
    if entities.rule:              scores[GET_RULE]       += 40
    if entities.resource
       and not entities.chapter:   scores[GET_RESOURCE]   += 30
    if entities.lo:                scores[GET_LO]         += 60
    if entities.chapter
       and not entities.resource:   scores[GET_TOPIC]      += 25
    if entities.assignment
       or entities.part:            scores[GET_ASSIGNMENT] += 25

    # Bước 4: nếu câu chứa tham chiếu ngữ cảnh mà không có hội thoại đang mở
    if has_reference(text) and not has_active_session():
        return CONTEXT_DEPENDENT

    return intent có điểm cao nhất, nếu điểm > 0; ngược lại UNKNOWN
```

**Vì sao cần chấm điểm thay vì thứ tự ưu tiên cứng?** Nhiều từ khoá xung đột.
Ví dụ *"Tài liệu nào liên quan đến PCFG?"* chứa cả `tài liệu` (→ GET_RESOURCE) lẫn
`pcfg` (→ GET_TOPIC). Chấm điểm cho phép nhiều tín hiệu cùng tồn tại; các điểm cộng
theo entity ở Bước 3 mới là thứ phá thế hoà, thay vì phải cố đặt một thứ tự
tuần tự cố định.

#### 3.1.3 Nhận diện Entity

*Pseudocode:*

```
function extract_entities(text, intent):
    normalized ← normalize_text(text)
    entities ← {}

    # Định danh miền — tra bằng LEXICON, chiến lược LONGEST-MATCH
    # (nguồn sự thật duy nhất: models/lexicon.json)
    matches ← lexicon.lookup(
        normalized,
        priority_groups = ["assignment_part", "part_of_assignment", "assignment",
                           "learning_outcome", "chapter", "week", "rule",
                           "attribute", "topic", "course", "resource",
                           "instructor"],
    )
    for match in matches:                 # giữ match đầu tiên (dài/ưu tiên cao nhất)
        entities[match.entity_type] ← match.canonical

    # Mã mục tiêu học tập: lexicon chỉ biết mã có thật, cần quét riêng
    if re.search(r"\blo_(\d)(?:_(\d+))?", normalized):
        entities["lo"] ← "LO" + phần chính + "." + phần phụ (mặc định ".1")

    # Số chương / tuần nằm ngoài phạm vi vẫn tạo ra entity có dạng hợp lệ
    # ("Chương 99 nói về gì?") để KB trả lời "không tìm thấy" thay vì đoán.
    if re.search(r"chương\s*(\d+)", normalized):
        entities["chapter"] ← "CH" + số.zfill(2)
    if re.search(r"tuần\s*(\d+)", normalized):
        entities["week"] ← "WEEK_" + số.zfill(2)

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

> **Vì sao dùng lexicon thay vì so khớp từ khoá?** Vì bề mặt tiếng Việt có
> thể chứa bề mặt khác: `"semantic grammar"` phải thắng `"semantic"`,
> `"statistical nlp"` phải thắng `"nlp"`. Chiến lược **longest-match** giải quyết
> trọn vẹn lớp bug "chuỗi con cướp entity" thay vì phải viết thứ tự ưu tiên
> thủ công cho từng cặp bề mặt.



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

Tổng cộng `models/lexicon.json` chứa **207 bề mặt từ** trong **12 nhóm entity**
(`course` · `chapter` · `week` · `topic` · `assignment` · `assignment_part` ·
`part_of_assignment` · `rule` · `attribute` · `resource` · `learning_outcome` ·
`instructor`), cộng thêm **10 bề mặt tham chiếu ngữ cảnh** và **50 mẫu ngoài
phạm vi**.

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
      Earley chart parser theo văn phạm CFG → cây cú pháp
      (fallback: dựng cây theo mẫu nếu không khớp văn phạm)
  │
  ▼
[3] SEMANTIC REPRESENTATION
      cây cú pháp / văn bản → dạng logic  GET_INTENT(...)
  │
  ▼
[4] INTENT / ENTITY
      intent  : khớp luật có trọng số + điểm cộng theo entity
      entity  : nhận diện & chuẩn hoá qua lexicon (longest-match)
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
│  │   CFG Grammar ──► Earley Chart Parser ──► Parse Tree          │  │
│  │   (36 non-terminal, 182 terminal)      (fallback: pattern)     │  │
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




### 4.6 Trạng thái hiện tại

`DialogueManager` đã được **nối hoàn toàn** vào pipeline chính của
`CourseAssistant.process_dialogue()` (và `process_query()` dùng chung trạng
thái thụ động). Hiện tại:

- Toàn bộ 6 ca hội thoại `DIALOGUE_01` – `DIALOGUE_05` **pass** (trước đây
  là `xfail`).
- `process_query()` phân biệt hai chế độ: **câu đơn lẻ** (có tham chiếu →
  `CONTEXT_DEPENDENT`, hệ thống hỏi lại) và **phiên hội thoại** (tham chiếu
  được giải theo trạng thái → trả lời bình thường).
- Hàng rào `xfail` trong `tests/known_issues.py` đã được dọn sạch — không còn
  `xfail`/`XPASS` nào trong bộ test.

---



## 5. Kết quả và phân tích



### 5.1 Đánh giá hệ thống



#### 5.1.1 Tập kiểm thử

Tập kiểm thử lấy từ dữ liệu mẫu chính thức của bài tập
(`tests/data/sample_queries.txt`, **34 câu**), bao phủ các nhóm truy vấn:


| Nhóm                       | Số câu | Mô tả                                                                        |
| -------------------------- | ------ | ---------------------------------------------------------------------------- |
| Câu hỏi hợp lệ trong miền  | 28     | Hỏi thông tin chung, chương, tuần, chủ đề, bài tập, quy định, tài liệu, L.O. |
| Câu hỏi ngoài phạm vi      | 3      | Không liên quan tới môn học                                                  |
| Câu hỏi phụ thuộc ngữ cảnh | 3      | Cần thông tin từ lượt trước                                                  |


Bộ test còn có thêm **5 kịch bản hội thoại** (`tests/data/dialogues.txt`) mô tả
các mẫu tham chiếu ngữ cảnh cục bộ.

Ngoài 34 câu chính thức, hệ thống còn được đánh giá trên **tổng cộng 57 câu**
(34 chính thức + 15 câu biến thể do nhóm tự viết + 8 câu hội thoại nhiều lượt) —
xem mục 5.1.4.

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
| Intent accuracy                 | 34/34   | **100.00 %** |
| Entity accuracy (có bảng alias) | 34/34   | **100.00 %** |
| Entity accuracy (khớp thô)      | 32/34   | 94.12 %     |
| **Intent + Entity accuracy**    | 34/34   | **100.00 %** |
| Strict parse (Earley chart)     | 31/34   | **91.18 %** |
| Pattern fallback parse          | 3/34    | 8.82 %      |
| Parse failure                   | 0/34    | 0 %         |
| **Bộ test (`pytest`)**          | 158 pass | 0 failed, 0 xfailed |

> Các chỉ số trên là số liệu mới nhất (đo tự động bằng
> `python scripts/baseline.py`). Trước đó: intent 88.24 %, entity 55.88 %,
> intent+entity 52.94 %, strict parse 11.76 %, và 23 test `xfail`.


**Chất lượng bộ sinh câu (10 000 câu):**


| Chỉ số                     | Kết quả    |
| -------------------------- | ---------- |
| Câu chứa dấu `_`           | 0 / 10 000 |
| Câu rò non-terminal        | 0 / 10 000 |
| Câu mở bằng động từ        | 0 / 10 000 |
| Câu thiếu dấu câu kết thúc | 0 / 10 000 |




#### 5.1.4 Phân tích theo từng intent

**Hiện tại không còn câu hỏi nào bị sai intent trên tập kiểm thử.**

Bốn lỗi intent đã được xử lý như sau:


| Câu hỏi                                   | Intent đúng       | Intent cũ           | Nguyên nhân và cách sửa                                                       |
| ----------------------------------------- | ----------------- | -------------------- | -------------------------------------------------------------------------------- |
| "Hãy giải bài tập xác suất này giúp tôi." | UNKNOWN           | GET_ASSIGNMENT       | Thêm mẫu ngoài phạm vi vào `models/lexicon.json` + kiểm tra `is_out_of_scope` trước khi chấm điểm intent |
| "Nó có liên quan đến parsing không?"      | CONTEXT_DEPENDENT | GET_RULE             | Thêm intent `CONTEXT_DEPENDENT`; `DialogueManager.has_reference()` phát hiện đại từ |
| "Còn chương sau?"                         | CONTEXT_DEPENDENT | GET_TOPIC            | Thêm intent `CONTEXT_DEPENDENT`; nhận diện cấu trúc rút gọn (ellipsis)         |
| "Phần này cần xuất file gì?"              | CONTEXT_DEPENDENT | GET_ASSIGNMENT       | Thêm intent `CONTEXT_DEPENDENT`; nhận diện mô tả xác định ("phần này")          |

Ngoài ra, 13 lỗi trích xuất entity đã được khắc phục nhờ cơ chế **longest-match**
của `src/lexicon.py`: `"pcfg"` không còn bị `"cfg"` chiếm mất, `"semantic grammar"`
không còn bị `"semantic"` chiếm mất, `"statistical nlp"` / `"python nlp"` không còn
bị `"nlp"` chiếm mất, `"môn học"` được ánh xạ về `course=CO3085`, và phần của bài
tập được suy luận được từ keyword (`"parser"` → `PART_I`, `"hỏi đáp"` → `PART_II`).

**Nhận xét quan trọng:** 34/34 intent đúng **không đồng nghĩa** với 100 % mọi
thứ. Khi đo đồng thời intent *và* entity, độ chính xác tổng thể là
**100.00 %** trên tập 34 câu này; nhưng đây vẫn là một tập nhỏ, được biên soạn
cho môn học, nên **không** nên suy rộng cho mọi câu hỏi tiếng Việt. Báo cáo này
trình bày cả hai số để tránh hiểu sai.

#### 5.1.5 Kết quả evaluation tổng hợp

```bash
$ python scripts/baseline.py
======================================================================
COURSE ASSISTANT - BASELINE METRICS
======================================================================

Official test set (tests/data/sample_queries.txt): 34 cases
  Intent accuracy:        34/34 = 100.00%
  Entity accuracy (alias-aware): 34/34 = 100.00%
  Entity accuracy (raw match):   32/34 = 94.12%
  Intent + Entity accuracy: 34/34 = 100.00%

Parser (on the official test set):
  Strict Earley chart parse: 31/34 = 91.18%
  Pattern fallback:        3/34 = 8.82%
  Failure:                 0/34 = 0.00%

Sentence generation:
  Sentences generated:      10000
  Containing '_':            0
  Containing 'WH_PHRASE':    0
  Bad leading token:         0
  Missing end punctuation:   0
```



#### 5.1.6 Đánh giá trên bộ 57 câu kiểm thử mở rộng

Ngoài 34 câu chính thức, nhóm xây dựng thêm hai nhóm câu để kiểm tra hệ thống
đúng hơn: **15 câu biến thể** (cùng ý nhưng cách diễn đạt khác — phát hiện
trường hợp hệ thống chỉ "nhớ" đúng câu chữ của đề bài) và **8 câu hội thoại
nhiều lượt** (chứng minh ngữ cảnh hội thoại thực sự được dùng).

```bash
$ python -m src.evaluation
=====================================================================
COURSE ASSISTANT - EVALUATION REPORT
=====================================================================

1. SỐ LƯỢNG CÂU KIỂM THỬ
   Tổng: 57 câu
     - sample_queries.txt (chính thức) : 34 câu
     - Câu biến thể (nhóm tự bổ sung)  : 15 câu
     - Câu hội thoại nhiều lượt        :  8 câu

2. SỐ LƯỢNG CÂU TRẢ LỜI ĐÚNG
   Intent đúng        : 57/57 = 100.00%
   Entity đúng        : 57/57 = 100.00%
   Intent + Entity     : 100.00%
   Câu trả lời đúng    : 57/57 = 100.00%
   Ngoài phạm vi       : 100.00%

3. ĐỘ CHÍNH XÁC THEO TỪNG INTENT
   GET_COURSE_INFO      7/7   100.0%
   GET_SCHEDULE         5/5   100.0%
   GET_TOPIC           17/17  100.0%
   GET_ASSIGNMENT       7/7   100.0%
   GET_DEADLINE         1/1   100.0%
   GET_RESOURCE         4/4   100.0%
   GET_RULE             3/3   100.0%
   GET_INSTRUCTOR       1/1   100.0%
   GET_LO               4/4   100.0%
   CONTEXT_DEPENDENT    3/3   100.0%
   UNKNOWN              5/5   100.0%
```

| Chỉ số (57 câu)                  | Kết quả              |
| -------------------------------- | -------------------- |
| Intent accuracy                  | 57/57 — **100.00 %** |
| Entity accuracy (alias-aware)    | 57/57 — **100.00 %** |
| **Intent + Entity accuracy**     | 57/57 — **100.00 %** |
| Câu trả lời đúng                | 57/57 — **100.00 %** |
| Phát hiện câu ngoài phạm vi      | **100.00 %**         |

So sánh entity trong báo cáo đánh giá là **alias-aware**: nhãn chính thức
`MIDTERM` được chấp nhận khi pipeline trích ra `midterm_duration`, nhãn
`CO3085` được chấp nhận khi pipeline trích ra `NLP`. Đây chính là lý do cột
"Entity accuracy (khớp thô)" ở mục 5.1.3 thấp hơn: đó là hệ quả của cách
so sánh thô, không phải của hệ thống.

> **Lưu ý về cách đọc:** 100 % là độ chính xác trên **bộ 57 câu kiểm thử** —
> không phải độ phủ trên tiếng Việt nói chung. Báo cáo này nêu rõ điều này ở
> cả Mục 5 và Mục 6 để tránh hiểu sai.

#### 5.1.7 Ví dụ hệ thống trả lời đúng


| Câu hỏi                         | Dạng logic                                       | Câu trả lời                                                                                         |
| ------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| "Môn NLP có bao nhiêu tín chỉ?" | `GET_COURSE_INFO(course=CO3085, attribute=credits)` | "Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ, tương đương 6 ECTS." |
| "Tuần 3 học gì?"                | `GET_SCHEDULE(week=WEEK_03)`                     | "Tuần 03: Học Chương 03 - Grammar and Parsing." |
| "Chương nào học về CFG?"        | `GET_TOPIC(topic=CFG)`                           | "Chủ đề CFG thuộc Chương 03 - Grammar and Parsing." |
| "L.O.4.2 là gì?"                | `GET_LO(lo=LO4.2)`                               | "LO4.2: Ngữ cảnh diễn ngôn cục bộ và sự tham chiếu." |




### 5.2 Một vài hạn chế



#### 5.2.1 Hạn chế về độ bao phủ của văn phạm và parser

**Hiện trạng:** strict parse đạt **91.18 %** (31/34 câu); 3 câu còn
lại rơi vào fallback và 0 câu thất bại.

**Nguyên nhân của 3 câu chưa parse strict:** cả ba đều **cố ý nằm ngoài phạm
vi** của đề bài — *"Hôm nay ở TP.HCM có mưa không?"* (`Q026`), *"Ai là tổng
thống của Pháp?"* (`Q027`) và *"Hãy giải bài tập xác suất này giúp tôi."*
(`Q028`). Chúng không thuộc miền câu hỏi môn học nên văn phạm không mô hình hoá.

**Hệ quả:** cây phân tích cú pháp trong báo cáo có thể không đúng với 3 câu
đó. Tuy nhiên **intent và entity vẫn đúng** nhờ tầng semantic làm việc trực tiếp
trên văn bản và cơ chế fallback của parser. Trên **31 câu in-scope**, strict
parse đạt **100 %**.

**Hướng khắc phục:** bổ sung quy tắc cho vị từ phức tạp và danh từ ghép trong
`src/grammar.py`; Earley parser sẽ tự động hấp thụ các quy tắc mới mà không
cần sửa mã parser.

#### 5.2.2 Hạn chế về trích xuất thực thể

**Hiện trạng:** entity accuracy **100.00 %** (alias-aware) trên tập 34
câu — khớp thô 94.12 % (2 câu dùng nhãn canonical khác tên trong đề bài).

**Đã khắc phục:** toàn bộ lỗi "khớp chồng lấn" và "tranh chấp miền" đã được
xử lý bằng cơ chế **longest-match** của `src/lexicon.py` và bảng ưu tiên nhóm:

- "PCFG" không còn bị "CFG" chiếm mất; "semantic grammar" không còn bị
  "semantic" chiếm mất.
- "Tài liệu về statistical NLP" được gán `topic=STATISTICAL_NLP` thay vì
  `course=NLP`; "Python NLP" được gán `topic=PYTHON_NLP`.
- Suy luận `part` đã có: "Bài tập lớn có phần parser không?" → `PART_I`;
  "… có phần hỏi đáp không?" → `PART_II`.
- Thực thể quy tắc đã có: `rule=LLM_RAG`, `rule=AI_USAGE`.

**Hạn chế còn lại:** lexicon vẫn là bảng tra **thủ công**; một bề mặt từ mới
(cách viết khác) sẽ không được nhận diện. Hướng khắc phục: bổ sung đơn vị
từ vựng (morphology) để sinh biến thể tự động từ gốc từ vựng.

#### 5.2.3 Hạn chế về xử lý ngữ cảnh hội thoại

**Hiện trạng:** `DialogueManager` **đã được nối đầy đủ** vào
pipeline. Cả 5 hội thoại mẫu (`DIALOGUE_01` – `DIALOGUE_05`) đều pass; 3 câu
kiểm thử thuộc nhóm context-dependent đều được phân loại đúng là
`CONTEXT_DEPENDENT` kèm thực thể referent gợi ý.

**Hạn chế còn lại:** bộ tham chiếu hiện là **cố định** (đại từ, mô tả xác định,
cấu trúc rút gọn, quan hệ "kế tiếp") đúng như đề bài yêu cầu. Hệ thống chưa
theo dõi **salience** thật sự, chưa xử lý tham chiếu *bridging* (ví dụ "cuốn sách
đó" khi cuốn sách chưa từng được nhắc) và chưa giải quyết tham chiếu mơ hồ
("cái đó", "thứ kia") khi có nhiều ứng viên.

**Hướng khắc phục:** triển khai đầy đủ mô hình **Centering** (đã có trong kiến
thức môn học ở Chương 12) để xếp hạng ứng viên theo độ nổi bật.

#### 5.2.4 Hạn chế về phương pháp nhận diện intent

Phương pháp dựa trên luật có ưu điểm là **minh bạch, không cần dữ liệu huấn
luyện, giải thích được** (đây là điểm giảng viên đánh giá cao), nhưng:

- Chỉ bao phủ được các mẫu câu đã định nghĩa.
- Mâu thuẫn từ khoá được xử lý bằng **chấm điểm có trọng số** và điểm cộng
  theo entity — hiệu quả hơn thứ tự ưu tiên cứng, nhưng vẫn phải chọn trọng số
  bằng tay.
- Không mở rộng tự động khi gặp cách diễn đạt mới.

**Hướng khắc phục (phương án dự phòng):** bổ sung một mô hình phân loại đa lớp
(học máy thống kê) trên đặc trưng n-gram, dùng luật làm đường dẫn fallback khi
độ tin cậy thấp. Nhóm chọn hướng **Classical/Statistical NLP** nên đây là hướng
mở rộng tự nhiên, không phải LLM.

#### 5.2.5 Hạn chế về độ bao phủ knowledge base

**Hiện trạng:** knowledge base đã mở rộng từ vài chục dòng lên
thành dữ liệu có cấu trúc cho **12 chương** (mỗi chương có tóm tắt, chủ đề con,
tuần học, phương pháp, mục tiêu học tập), **15 tuần**, **4 phần bài tập lớn**
(kèm file phải xuất), **7 tài liệu tham khảo**, **7 nhóm quy định** và
**17 mục tiêu học tập**.

**Hạn chế còn lại:**

- Chỉ hỗ trợ truy vấn đơn giản theo `(intent, entities)`, không có suy luận nhiều
  bước.
- Chưa có cơ chế **trả lời khi thiếu thông tin theo ngữ cảnh** — hiện tại mọi
  truy vấn không có kết quả đều trả về cùng một thông báo.
- Nội dung knowledge base vẫn là bản tóm tắt, chưa bao phủ hết đề cương môn
  học đầy đủ.

---



## 6. Kết luận



### 6.1 Kết luận

Hệ thống **Course Assistant** đã hiện thực được chuỗi xử lý NLP hoàn chỉnh trong miền môn học, từ ngôn ngữ tự nhiên đến câu trả lời.

**Về mặt phương pháp**, hệ thống thể hiện được đầy đủ các kỹ thuật NLP được yêu
cầu: xây dựng văn phạm CFG có trọng số, sinh câu, phân tích cú pháp bằng **Earley
chart parser**, biểu diễn ngữ nghĩa dạng logic form, nhận diện intent bằng luật
có trọng số, trích xuất entity có chuẩn hoá qua lexicon với chiến lược
**longest-match**, truy vấn knowledge base theo tham số, và xử lý tham chiếu ngữ
cảnh cục bộ (đại từ, mô tả xác định, cấu trúc rút gọn, quan hệ "kế tiếp").

**Điểm mạnh đáng chú ý** là tính **minh bạch và tái lập được**: mọi quyết định
của hệ thống đều có thể truy vết (rule nào khớp, entity nào được trích, query
gì được gửi tới KB); mọi con số trong báo cáo đều do script sinh ra chứ không
phải ước lượng tay.

**Sau khi hoàn thiện các nâng cấp lớn**, các hạn chế đã ghi nhận ở phiên bản
trước đều được khắc phục: strict parse 11.76 % → **91.18 %**, intent accuracy
88.24 % → **100.00 %**, entity accuracy 55.88 % → **100.00 %**, intent+entity
52.94 % → **100.00 %**, và bộ test từ *"89 pass + 23 xfail"* → **"158 pass,
0 xfail"**. Những hạn chế *còn lại* đã được đo lại và ghi rõ trong mục 5.2 —
không phải lỗi ẩn.

### 6.2 Hướng cải tiến

Các hướng cải tiến được xếp theo mức độ ưu tiên:

| # | Hướng                                          | Lý do / giá trị                                        |
| - | ---------------------------------------------- | ------------------------------------------------------ |
| 1 | Bổ sung quy tắc văn phạm cho câu hỏi ngoài phạm vi thiết kế | Mở rộng strict parse ra ngoài 31 câu in-scope   |
| 2 | Sinh biến thể từ vựng tự động cho lexicon      | Bỏ nỗi thủ công nhập từng bề mặt từ                    |
| 3 | Triển khai Centering cho xếp hạng ứng viên tham chiếu | Xử lý tham chiếu mơ hồ khi có nhiều ứng viên           |
| 4 | Suy luận nhiều bước trong knowledge base       | Trả lời các câu cần kết hợp 2 thông tin               |
| 5 | Bộ câu hỏi kiểm thử mở rộng (100+ câu)         | Tránh overfitting trên tập 34 câu                      |
| 6 | Mô hình phân loại n-gram thống kê (dự phòng)   | Mở rộng độ bao phủ intent theo hướng Statistical NLP   |

---

*Báo cáo bài tập lớn CO3085 — Trợ lý hỗ trợ học tập thông minh (Course Assistant)*
*Hướng thực hiện: Classical / Statistical NLP (dựa trên luật)*