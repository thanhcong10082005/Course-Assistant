"""
Knowledge Base module for Course Assistant.

Knowledge base expansion
------------------------
The knowledge base covers every chapter with its sub-topics, the week it is
taught in and the learning outcomes it serves, every week of the semester,
the four parts of the assignment with their deliverables, the rules of the
course (LLM/RAG, AI usage, academic integrity, copyright, out-of-scope
policy), the resources, and the mapping of the learning outcomes onto the
chapters.  Out-of-scope and context-dependent cases are answered with a
clear, honest message instead of a generic apology.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class CourseInfo:
    """Course information"""
    course_id: str
    name: str
    name_en: str
    credits: int
    ects: int
    semester: str
    department: str
    description: str
    parts: List[str]
    learning_outcomes: Dict[str, str]
    exam_duration: Dict[str, int]  # midterm, final in minutes
    prerequisites: List[str] = field(default_factory=list)
    assessment: Dict[str, str] = field(default_factory=dict)
    instructor: str = ""
    office_hours: str = ""


@dataclass
class ChapterInfo:
    """Chapter/Topic information"""
    chapter_id: str
    name: str
    part: str
    keywords: List[str]
    summary: str
    subtopics: List[str]
    week: Optional[int] = None
    learning_outcomes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)


@dataclass
class WeekSchedule:
    """Weekly schedule information"""
    week_id: str
    chapter: str
    topics: List[str]
    activity: Optional[str] = None
    milestone: Optional[str] = None


@dataclass
class AssignmentInfo:
    """Assignment information"""
    assignment_id: str
    title: str
    team_size: str
    goal: str
    parts: List[Dict[str, str]]
    deadlines: Dict[str, str]
    deliverables: List[str] = field(default_factory=list)
    evaluation_criteria: List[str] = field(default_factory=list)


@dataclass
class ResourceInfo:
    """Learning resource information"""
    resource_id: str
    title: str
    author: Optional[str]
    year: Optional[int]
    type: str  # TEXTBOOK, REFERENCE
    usage: str
    topics: List[str] = field(default_factory=list)
    url: str = ""


# Course Information
COURSE_INFO = CourseInfo(
    course_id="CO3085",
    name="Xử lý Ngôn ngữ Tự nhiên",
    name_en="Natural Language Processing",
    credits=3,
    ects=6,
    semester="HK261",
    department="Khoa Khoa học và Kỹ thuật Máy tính",
    description=(
        "Môn học cung cấp các khái niệm, lý thuyết và kỹ thuật nền tảng của "
        "xử lý ngôn ngữ tự nhiên. Nội dung đi từ mức biểu diễn văn bản, "
        "phân tích cú pháp với văn phạm, giải quyết nhập nhằng bằng xác suất, "
        "đến diễn dịch ngữ nghĩa, biểu diễn tri thức và xử lý ngữ cảnh hội "
        "thoại. Môn học kết thúc bằng một bài tập lớn theo nhóm trong đó sinh "
        "viên xây dựng một hệ thống hỏi đáp tự nhiên cho chính môn học."
    ),
    parts=["Xử lý cú pháp", "Diễn dịch ngữ nghĩa", "Ngữ cảnh và tri thức thế giới"],
    learning_outcomes={
        "LO1": "Tổng quan về tổ chức hệ thống NLP và các ứng dụng",
        "LO2": "Xử lý cú pháp; xây dựng văn phạm đơn giản và phân tích cú pháp",
        "LO3": "Diễn dịch ngữ nghĩa; tạo dạng luận lý và giải quyết nhập nhằng",
        "LO4": "Ngữ nghĩa và tri thức thế giới; xây dựng cơ sở tri thức và hệ thống hỏi đáp đơn giản",
        "LO1.1": "Hiểu cấu trúc hệ thống NLP, ứng dụng và cách đánh giá hệ thống hiểu ngôn ngữ tự nhiên.",
        "LO1.2": "Phân biệt các mức phân tích ngôn ngữ: cú pháp, ngữ nghĩa, diễn dịch và tri thức.",
        "LO1.3": "Mô tả được các ứng dụng điển hình của NLP trong đời sống.",
        "LO2.1": "Kiến thức cơ sở về cú pháp tiếng Anh.",
        "LO2.2": "Kiến thức cơ bản về văn phạm và phân tích cú pháp.",
        "LO2.3": "Kiến thức về nét và văn phạm gia tố.",
        "LO2.4": "Kiến thức tạo văn phạm cho ngôn ngữ tự nhiên và phương pháp parsing.",
        "LO2.5": "Kiến thức xác suất để giải quyết nhập nhằng từ ở mức câu.",
        "LO3.1": "Kiến thức về ngôn ngữ dạng luận lý và tạo dạng luận lý đơn giản.",
        "LO3.2": "Tạo tự động diễn giải ngữ nghĩa cho câu tự nhiên.",
        "LO3.3": "Giải quyết nhập nhằng ngữ nghĩa dựa trên tri thức và thống kê.",
        "LO3.4": "Diễn giải ngữ nghĩa bằng quan hệ văn phạm và văn phạm ngữ nghĩa.",
        "LO4.1": "Biểu diễn tri thức, suy diễn và xây dựng hệ thống hỏi đáp đơn giản.",
        "LO4.2": "Ngữ cảnh diễn ngôn cục bộ và sự tham chiếu.",
    },
    exam_duration={
        "midterm": 60,
        "final": 90
    },
    prerequisites=["Cấu trúc dữ liệu và giải thuật", "Lập trình Python"],
    assessment={
        "attendance": "10% - chuyên cập tham dự",
        "midterm": "30% - bài kiểm tra giữa kỳ (60 phút)",
        "assignment": "30% - bài tập lớn theo nhóm",
        "final": "30% - bài kiểm tra cuối kỳ (90 phút)",
    },
    instructor="TS. Trần Minh Khoa",
    office_hours="Thứ Ba 14h-16h, phòng 402 (hoặc đặt lịch qua email)",
)

# Chapter Information
CHAPTERS = {
    "CH01": ChapterInfo(
        chapter_id="CH01",
        name="Introduction to Natural Language Processing",
        part="Introduction",
        keywords=["NLP", "NLU", "text-based", "dialog-based", "evaluation", "ngôn ngữ tự nhiên"],
        summary=(
            "NLP nghiên cứu các phương pháp tính toán để xử lý ngôn ngữ tự nhiên. "
            "Chương giới thiệu các ứng dụng, các mức phân tích ngôn ngữ, cách biểu "
            "diễn và cách đánh giá một hệ thống hiểu ngôn ngữ tự nhiên."
        ),
        subtopics=[
            "The study of natural language",
            "Applications of NLU",
            "Evaluating NLU systems",
            "Different levels of language analysis",
            "Representation and understanding",
        ],
        week=1,
        learning_outcomes=["LO1.1", "LO1.2", "LO1.3"],
        methods=["Khảo sát tài liệu", "Phân tích ví dụ thực tế"],
    ),
    "CH02": ChapterInfo(
        chapter_id="CH02",
        name="Linguistic Background - English Syntax",
        part="Syntactic Processing",
        keywords=["syntax", "word", "noun phrase", "verb phrase", "adjective phrase", "cú pháp"],
        summary=(
            "Ôn lại kiến thức cú pháp tiếng Anh: từ, cụm danh từ, cụm động từ, "
            "câu đơn giản. Đây là nền tảng để xây dựng văn phạm trong Chương 3."
        ),
        subtopics=[
            "Words",
            "Simple noun phrases",
            "Verb phrases and simple sentences",
            "Noun phrases revisited",
            "Adjective phrases",
            "Adverbial phrases",
        ],
        week=2,
        learning_outcomes=["LO2.1"],
        methods=["Phân tích cú pháp câu tiếng Anh", "Chú thích cấu trúc câu"],
    ),
    "CH03": ChapterInfo(
        chapter_id="CH03",
        name="Grammar and Parsing",
        part="Syntactic Processing",
        keywords=["CFG", "parsing", "PCFG", "dependency grammar", "top-down", "bottom-up",
                  "văn phạm", "phân tích cú pháp"],
        summary=(
            "Giới thiệu văn phạm phi ngữ cảnh (CFG), cấu trúc câu và các phương pháp "
            "phân tích cú pháp: top-down, bottom-up (chart), PCFG và văn phạm phụ thuộc."
        ),
        subtopics=[
            "Context-Free Grammars",
            "Top-down parser",
            "Bottom-up chart parser",
            "Probabilistic CFG",
            "Dependency Grammar",
            "Stanford Dependencies",
        ],
        week=3,
        learning_outcomes=["LO2.2", "LO2.4"],
        methods=["Phân tích cú pháp từ trên xuống", "Phân tích cú pháp từ dưới lên (chart parser)"],
    ),
    "CH04": ChapterInfo(
        chapter_id="CH04",
        name="Features and Augmented Grammar",
        part="Syntactic Processing",
        keywords=["feature", "augmented grammar", "lexicon", "unification", "ATN", "đặc trưng"],
        summary=(
            "Mở rộng văn phạm hình thức bằng hệ đặc trưng: lexicon, hợp nhất đặc trưng, "
            "phân tích cú pháp có đặc trưng, mạng chuyển tiếp tăng cường (ATN) và "
            "văn phạm hợp nhất."
        ),
        subtopics=[
            "Feature systems and augmented grammars",
            "Basic feature systems for English",
            "Lexicon",
            "Grammar using feature systems",
            "Parsing with features",
            "Augmented transition networks",
            "Unification grammar",
        ],
        week=4,
        learning_outcomes=["LO2.2", "LO2.3"],
        methods=["Hợp nhất đặc trưng (unification)", "Mạng chuyển tiếp tăng cường ATN"],
    ),
    "CH05": ChapterInfo(
        chapter_id="CH05",
        name="Grammar for Natural Language",
        part="Syntactic Processing",
        keywords=["auxiliary", "movement", "question", "relative clause", "câu hỏi"],
        summary=(
            "Tập trung vào các hiện tượng ngữ pháp quan trọng với ngôn ngữ tự nhiên: "
            "động từ khuyết thiếu, hiện tượng dịch chuyển, xử lý câu hỏi trong CFG và "
            "mệnh đề quan hệ."
        ),
        subtopics=[
            "Auxiliary verbs and verb phrases",
            "Movement phenomena",
            "Handling questions in CFG",
            "Relative clauses",
        ],
        week=6,
        learning_outcomes=["LO2.4"],
        methods=["Xây dựng văn phạm cho câu hỏi", "Mô hình hóa hiện tượng dịch chuyển"],
    ),
    "CH06": ChapterInfo(
        chapter_id="CH06",
        name="Ambiguity Resolution - Statistical Methods",
        part="Syntactic Processing",
        keywords=["probability", "POS tagging", "lexical probability", "PCFG", "best-first",
                  "xác suất", "giải quyết nhập nhằng"],
        summary=(
            "Các phương pháp thống kê để giải quyết nhập nhằng ở mức câu: lý thuyết xác "
            "suất, ước lượng xác suất, gán nhãn từ loại, xác suất từ vựng, CFG xác suất "
            "và phân tích cú pháp best-first."
        ),
        subtopics=[
            "Basic probability theory",
            "Estimating probabilities",
            "Part-of-speech tagging",
            "Lexical probabilities",
            "Probabilistic CFG",
            "Best-first parsing",
        ],
        week=7,
        learning_outcomes=["LO2.5"],
        methods=["Gán nhãn từ loại (POS tagging)", "Phân tích cú pháp xác suất PCFG",
                 "Phân tích cú pháp best-first"],
    ),
    "CH07": ChapterInfo(
        chapter_id="CH07",
        name="Semantics and Logical Form",
        part="Semantic Interpretation",
        keywords=["semantics", "logical form", "word sense", "thematic role", "speech act",
                  "ngữ nghĩa", "dạng luận lý"],
        summary=(
            "Giới thiệu diễn dịch ngữ nghĩa và dạng luận lý: nghĩa từ và nhập nhằng, "
            "ngôn ngữ dạng luận lý cơ bản, vai trò ngữ nghĩa và hành động lời nói."
        ),
        subtopics=[
            "Semantics and logical form",
            "Word senses and ambiguity",
            "Basic logical form language",
            "Encoding ambiguity in logical form",
            "Thematic roles",
            "Speech acts and embedded sentences",
        ],
        week=9,
        learning_outcomes=["LO3.1", "LO3.2"],
        methods=["Diễn dịch ngữ nghĩa theo dạng luận lý", "Gán vai trò ngữ nghĩa"],
    ),
    "CH08": ChapterInfo(
        chapter_id="CH08",
        name="Linking Syntax and Semantics",
        part="Semantic Interpretation",
        keywords=["compositionality", "semantic interpretation", "semantic role",
                  "liên kết cú pháp ngữ nghĩa"],
        summary=(
            "Kết nối kết quả phân tích cú pháp với diễn dịch ngữ nghĩa: tính đóng "
            "góp ngữ nghĩa, văn phạm và lexicon có diễn dịch, cụm giới từ và cụm động từ."
        ),
        subtopics=[
            "Semantic interpretation and compositionality",
            "Grammar and lexicon with semantic interpretation",
            "Prepositional phrases and verb phrases",
            "Lexicalized semantic interpretation and semantic roles",
            "Handling simple questions",
        ],
        week=10,
        learning_outcomes=["LO3.2", "LO3.4"],
        methods=["Diễn dịch ngữ nghĩa kết hợp cú pháp", "Xử lý câu hỏi đơn giản"],
    ),
    "CH09": ChapterInfo(
        chapter_id="CH09",
        name="Ambiguity Resolution",
        part="Semantic Interpretation",
        keywords=["selectional restriction", "semantic network", "WSD", "hạn chế lựa chọn"],
        summary=(
            "Các phương pháp tri thức và thống kê để giải quyết nhập nhằng ngữ nghĩa: "
            "hạn chế lựa chọn, lọc ngữ nghĩa, mạng ngữ nghĩa và phân giải nghĩa từ "
            "theo thống kê."
        ),
        subtopics=[
            "Selectional restriction",
            "Semantic filtering",
            "Semantic networks",
            "Statistical word sense disambiguation",
        ],
        week=11,
        learning_outcomes=["LO3.3"],
        methods=["Lọc ngữ nghĩa theo hạn chế lựa chọn", "Phân giải nghĩa từ bằng mạng ngữ nghĩa"],
    ),
    "CH10": ChapterInfo(
        chapter_id="CH10",
        name="Other Strategies for Semantic Interpretation",
        part="Semantic Interpretation",
        keywords=["grammatical relations", "semantic grammar", "template matching",
                  "văn phạm ngữ nghĩa"],
        summary=(
            "Các cách tiếp cận thay thế cho diễn dịch ngữ nghĩa: quan hệ ngữ pháp, "
            "văn phạm ngữ nghĩa, so khớp mẫu và phân tích cú pháp điều khiển bởi ngữ nghĩa."
        ),
        subtopics=[
            "Grammatical relations",
            "Semantic grammars",
            "Template matching",
            "Semantically driven parsing",
        ],
        week=12,
        learning_outcomes=["LO3.3", "LO3.4"],
        methods=["Văn phạm ngữ nghĩa", "So khớp mẫu (template matching)",
                 "Phân tích cú pháp điều khiển bởi ngữ nghĩa"],
    ),
    "CH11": ChapterInfo(
        chapter_id="CH11",
        name="Knowledge Representation and Reasoning",
        part="Context and World Knowledge",
        keywords=["knowledge representation", "reasoning", "frame", "QA",
                  "hỏi đáp", "biểu diễn tri thức"],
        summary=(
            "Giới thiệu biểu diễn tri thức và suy diễn rồi áp dụng chúng cho bài toán "
            "hỏi đáp: khung (frame), lượng từ ngôn ngữ tự nhiên, thời gian và phạm vi, "
            "ngữ nghĩa thủ tục và hệ thống hỏi đáp."
        ),
        subtopics=[
            "Knowledge representation",
            "Frames",
            "Handling natural language quantification",
            "Time and aspectual classes",
            "Procedural semantics",
            "Question answering",
        ],
        week=13,
        learning_outcomes=["LO4.1"],
        methods=["Biểu diễn tri thức bằng khung (frame)", "Suy diễn",
                 "Xây dựng hệ thống hỏi đáp đơn giản"],
    ),
    "CH12": ChapterInfo(
        chapter_id="CH12",
        name="Discourse Context and Reference",
        part="Context and World Knowledge",
        keywords=["discourse context", "reference", "anaphora", "pronoun", "centering",
                  "danh chiếu", "ngữ cảnh"],
        summary=(
            "Giới thiệu ngữ cảnh diễn ngôn cục bộ và các biểu thức tham chiếu: đại từ, "
            "centering, mô tả xác định, cấu trúc rút gọn (ellipsis) và tham chiếu bề mặt."
        ),
        subtopics=[
            "Local discourse context and discourse entities",
            "Anaphora",
            "Pronouns and centering",
            "Definite descriptions",
            "Ellipsis",
            "Surface anaphora",
        ],
        week=14,
        learning_outcomes=["LO4.2"],
        methods=["Phân tích centering", "Giải tham chiếu đại từ và mô tả xác định",
                 "Xử lý cấu trúc rút gọn"],
    ),
}

# Week Schedule
SCHEDULE = {
    f"WEEK_{str(i).zfill(2)}": {
        "chapter": f"CH{str((i-1)//2 + 1).zfill(2)}" if i <= 12 else f"CH{str(min((i-1)//2 + 1, 12)).zfill(2)}",
        "topics": [],
        "activity": None,
        "milestone": None,
    }
    for i in range(1, 16)
}

# Override with the actual schedule
SCHEDULE["WEEK_01"] = {"chapter": "CH01", "topics": ["Introduction to NLP", "NLU applications", "Mức phân tích ngôn ngữ"], "activity": "Lý thuyết", "milestone": None}
SCHEDULE["WEEK_02"] = {"chapter": "CH02", "topics": ["English syntax", "Noun phrases", "Verb phrases"], "activity": "Lý thuyết + thực hành", "milestone": None}
SCHEDULE["WEEK_03"] = {"chapter": "CH03", "topics": ["CFG", "Top-down parsing", "Bottom-up parsing"], "activity": "Thực hành", "milestone": "Checkpoint 1: nộp sơ bộ grammar"}
SCHEDULE["WEEK_04"] = {"chapter": "CH04", "topics": ["Feature systems", "Augmented grammar", "Lexicon"], "activity": "Lý thuyết", "milestone": None}
SCHEDULE["WEEK_05"] = {"chapter": "CH04", "topics": ["Augmented transition networks", "Unification"], "activity": "Thực hành", "milestone": None}
SCHEDULE["WEEK_06"] = {"chapter": "CH05", "topics": ["Auxiliary verbs", "Movement", "Questions in CFG"], "activity": "Lý thuyết", "milestone": None}
SCHEDULE["WEEK_07"] = {"chapter": "CH06", "topics": ["Probability theory", "POS tagging", "PCFG"], "activity": "Thực hành", "milestone": None}
SCHEDULE["WEEK_08"] = {"chapter": "CH06", "topics": ["Best-first parsing", "Ambiguity resolution"], "activity": "Thực hành", "milestone": "Checkpoint 1: nộp Grammar và Parser"}
SCHEDULE["WEEK_09"] = {"chapter": "CH07", "topics": ["Semantics", "Logical form", "Thematic roles"], "activity": "Lý thuyết", "milestone": None}
SCHEDULE["WEEK_10"] = {"chapter": "CH08", "topics": ["Linking syntax and semantics", "Semantic roles"], "activity": "Thực hành", "milestone": None}
SCHEDULE["WEEK_11"] = {"chapter": "CH09", "topics": ["Selectional restriction", "Semantic networks", "Word sense disambiguation"], "activity": "Thực hành", "milestone": None}
SCHEDULE["WEEK_12"] = {"chapter": "CH10", "topics": ["Semantic grammars", "Template matching"], "activity": "Thực hành", "milestone": "Checkpoint 2: nộp Semantic và QA"}
SCHEDULE["WEEK_13"] = {"chapter": "CH11", "topics": ["Knowledge representation", "Frames", "Question answering"], "activity": "Lý thuyết + thực hành", "milestone": None}
SCHEDULE["WEEK_14"] = {"chapter": "CH12", "topics": ["Discourse context", "Anaphora", "Reference"], "activity": "Thực hành", "milestone": None}
SCHEDULE["WEEK_15"] = {"chapter": "CH12", "topics": ["Integration", "Evaluation", "Demo"], "activity": "Báo cáo nhóm", "milestone": "Final: nộp BTL và demo"}

# Assignment Information
ASSIGNMENT = AssignmentInfo(
    assignment_id="BTL01",
    title="Intelligent Course Assistant",
    team_size="3-4 sinh viên",
    goal=(
        "Xây dựng hệ thống xử lý câu hỏi tự nhiên trong miền thông tin của một môn học. "
        "Hệ thống phải trả lời được các câu hỏi về lịch học, nội dung chương, bài tập, "
        "tài liệu, quy định và mục tiêu học tập của môn học."
    ),
    parts=[
        {
            "id": "PART_I",
            "name": "Grammar and Parser",
            "description": (
                "Xây dựng văn phạm (grammar) cho câu hỏi tiếng Việt về môn học và xây dựng "
                "bộ phân tích cú pháp (parser) trên văn phạm đó. Hệ thống phải sinh được "
                "tập câu hỏi mẫu và phân tích cú pháp được các câu hỏi thực tế."
            ),
            "deliverables": [
                "grammar.txt (văn phạm dạng text)",
                "samples.txt (tập câu hỏi mẫu sinh từ văn phạm)",
                "parse-results.txt (kết quả phân tích cú pháp)",
            ],
        },
        {
            "id": "PART_II",
            "name": "Semantic Interpretation and QA",
            "description": (
                "Xây dựng bộ phân tích ngữ nghĩa (semantic analyzer) ánh xạ câu hỏi sang "
                "dạng luận lý, và một hệ thống hỏi đáp (question answering) tra cứu được "
                "tri thức về môn học."
            ),
            "deliverables": [
                "semantic.txt (dạng luận lý của các câu hỏi)",
                "intent-entity.txt (bảng ý định - thực thể)",
                "query.txt / answer.txt (cặp câu hỏi - câu trả lời)",
            ],
        },
        {
            "id": "PART_III",
            "name": "Local Discourse Context",
            "description": (
                "Xử lý ngữ cảnh diễn ngôn cục bộ: tham chiếu đại từ, mô tả xác định và cấu "
                "trúc rút gọn trong hội thoại nhiều lượt."
            ),
            "deliverables": [
                "dialogue.txt (hội thoại mẫu kèm ngữ cảnh được sử dụng)",
                "Mã nguồn dialogue manager (quản lý trạng thái hội thoại)",
            ],
        },
        {
            "id": "PART_IV",
            "name": "Evaluation",
            "description": (
                "Đánh giá hệ thống trên một bộ câu hỏi kiểm thử, báo cáo độ chính xác của "
                "nhận dạng ý định (intent), trích xuất thực thể (entity) và tỉ lệ phân "
                "tích cú pháp thành công."
            ),
            "deliverables": [
                "Bộ câu hỏi kiểm thử kèm nhãn ý định và thực thể",
                "Báo cáo đánh giá (docs/baseline.txt, docs/REPORT.md)",
            ],
        },
    ],
    deadlines={
        "checkpoint_1": "Tuần 8 - Grammar và Parser",
        "checkpoint_2": "Tuần 12 - Semantic và QA",
        "final": "Tuần 15 - Nộp BTL và Demo",
    },
    deliverables=[
        "Mã nguồn hệ thống (Python, không phụ thuộc thư viện NLP bên ngoài)",
        "Báo cáo kỹ thuật mô tả thiết kế và kết quả đánh giá",
        "Slide trình bày trước lớp",
        "Bộ câu hỏi kiểm thử kèm nhãn ý định và thực thể",
        "Transcript hội thoại mẫu minh họa xử lý ngữ cảnh",
    ],
    evaluation_criteria=[
        "Độ bao phủ văn phạm và tỉ lệ phân tích cú pháp thành công",
        "Độ chính xác nhận dạng ý định trên bộ câu hỏi kiểm thử",
        "Độ chính xác trích xuất thực thể (canonical value)",
        "Chất lượng câu trả lời và khả năng xử lý ngữ cảnh nhiều lượt",
        "Chất lượng mã nguồn và tài liệu hướng dẫn",
    ],
)

# Resources
RESOURCES = [
    ResourceInfo("R01", "Natural Language Processing with Python", "Bird, Klein, Loper", 2009, "TEXTBOOK",
                 "Thực hành với Python; phù hợp cho phần semantic và QA",
                 ["semantic", "question answering", "python nlp"], "https://www.nltk.org/book/"),
    ResourceInfo("R02", "Speech and Language Processing", "Jurafsky, Martin", 2019, "TEXTBOOK",
                 "Giáo trình chuẩn, tham khảo rộng cho toàn bộ môn học",
                 ["syntax", "semantic", "probability", "parsing"], "https://web.stanford.edu/~jurafsky/slp3/"),
    ResourceInfo("R03", "Introduction to NLP", "Jacob Eisenstein", 2019, "TEXTBOOK",
                 "Nền tảng về tổ chức hệ thống NLP và các ứng dụng",
                 ["nlp", "evaluation", "discourse"], "https://www.cs.cmu.edu/~jeffe/"),
    ResourceInfo("R04", "Foundation of Statistical NLP", "Manning, Schütze", 2001, "REFERENCE",
                 "Thống kê cho NLP: xác suất, PCFG, POS tagging",
                 ["statistical nlp", "pcfg", "tagging", "probability"], ""),
    ResourceInfo("R05", "Speech and Language Processing (2nd ed.)", "Jurafsky, Martin", 2007, "REFERENCE",
                 "Phiên bản cũ, nhiều ví dụ về văn phạm ngữ nghĩa",
                 ["semantic grammar", "word sense"], ""),
    ResourceInfo("R06", "Bài giảng và slide của giảng viên", "TS. Trần Minh Khoa", 2026, "SLIDES",
                 "Slide trình bày và bài tập về nhà theo tuần",
                 ["nlp", "syntax", "semantic", "discourse"], ""),
    ResourceInfo("R07", "Ghi chú bài giảng và ví dụ thực hành", "Nhóm học", 2026, "NOTES",
                 "Ghi chú tóm tắt và bài tập mở rộng do nhóm biên soạn",
                 ["reference"], ""),
]

# Regulations
REGULATIONS = {
    "attendance": "Sinh viên được khuyến khích tham dự đầy đủ các buổi học.",
    "academic_integrity": (
        "Sinh viên phải tuân thủ nguyên tắc liêm chính học thuật: không sao chép bài "
        "làm của nhau, phải trích dẫn nguồn khi sử dụng tài liệu của người khác và "
        "chịu trách nhiệm về toàn bộ nội dung nộp."
    ),
    "ai_usage": (
        "Sinh viên được phép dùng công cụ AI hỗ trợ (LLM, RAG) nhưng phải khai báo rõ "
        "ràng trong báo cáo: mục đích sử dụng, phạm vi áp dụng và phần nào do AI sinh ra. "
        "Việc không khai báo được xem là vi phạm liêm chính học thuật."
    ),
    "llm_rag": (
        "LLM/RAG có thể được sử dụng như một phần mở rộng, nhưng không được thay thế "
        "yêu cầu NLP cốt lõi của bài tập lớn. Phần lõi (grammar, parser, semantic, "
        "QA) phải do sinh viên tự xây dựng và giải thích được."
    ),
    "copyright": (
        "Không sử dụng tài liệu có bản quyền không được phép; khi trích dẫn tài liệu "
        "tham khảo phải ghi rõ tác giả, năm xuất bản và nguồn."
    ),
    "policy": (
        "Mọi hoạt động trong môn học tuân thủ quy định chung của trường về đạo đức học "
        "thuật, bảo mật thông tin và trách nhiệm bảo mật dữ liệu."
    ),
    "out_of_scope": (
        "Hệ thống chỉ chịu trách nhiệm trong phạm vi dữ liệu môn học. Các yêu cầu ngoài "
        "phạm vi (giải bài tập khác, dịch thuật, tin tức, thời tiết...) sẽ bị từ chối."
    ),
}

# FAQ
FAQ = {
    "credits": "Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ (tương đương 6 ECTS).",
    "parts": "Môn học gồm ba phần chính: Xử lý cú pháp; Diễn dịch ngữ nghĩa; Ngữ cảnh và tri thức thế giới.",
    "cfg_chapter": "CFG được trình bày trong Chương 3, Grammar and Parsing.",
    "llm_allowed": "Có thể sử dụng LLM/RAG như một phần mở rộng nếu được khai báo rõ trong báo cáo.",
    "midterm": "Bài kiểm tra giữa kỳ kéo dài 60 phút.",
    "final": "Bài kiểm tra cuối kỳ kéo dài 90 phút.",
    "team_size": "Bài tập lớn thực hiện theo nhóm 3-4 sinh viên.",
}

# Aliases: a topic name may be written in several ways.
TOPIC_ALIASES: Dict[str, List[str]] = {
    "CFG": ["cfg", "context free grammar", "context-free grammar", "văn phạm phi ngữ cảnh"],
    "PCFG": ["pcfg", "probabilistic cfg", "probabilistic context free grammar", "văn phạm xác suất"],
    "PARSING": ["parsing", "parse", "parser", "phân tích cú pháp"],
    "SEMANTIC": ["semantic", "semantics", "ngữ nghĩa"],
    "SEMANTIC_GRAMMAR": ["semantic grammar", "văn phạm ngữ nghĩa"],
    "SYNTAX": ["syntax", "cú pháp"],
    "POS": ["pos", "part of speech"],
    "POS_TAGGING": ["pos tagging", "gán nhãn từ loại", "tagging"],
    "FEATURE": ["feature", "đặc trưng"],
    "GRAMMAR": ["grammar", "ngữ pháp", "văn phạm"],
    "WORD_DISAMBIGUATION": ["disambiguation", "wsd", "phân giải nghĩa từ"],
    "REFERENCE": ["reference", "danh chiếu"],
    "QUESTION_ANSWERING": ["question answering", "hỏi đáp"],
    "SELECTIONAL_RESTRICTION": ["selectional restriction", "hạn chế lựa chọn"],
    "STATISTICAL_NLP": ["statistical nlp", "nlp thống kê", "thống kê"],
    "PYTHON_NLP": ["python nlp", "nlp với python"],
    "ANAPHORA": ["anaphora", "đồng chiếu"],
    "CENTERING": ["centering"],
    "DEPENDENCY": ["dependency", "dependency grammar", "văn phạm phụ thuộc"],
    "DISCOURSE": ["discourse", "diễn ngôn"],
    "KNOWLEDGE_REPRESENTATION": ["knowledge representation", "biểu diễn tri thức"],
    "REASONING": ["reasoning", "suy diễn"],
    "LOGICAL_FORM": ["logical form", "dạng luận lý"],
    "THEMATIC_ROLE": ["thematic role", "thematic roles", "vai trò ngữ nghĩa"],
    "WORD_SENSE": ["word sense", "nghĩa từ"],
    "AMBIGUITY": ["ambiguity", "nhập nhằng"],
    "BEST_FIRST": ["best first", "best-first parsing"],
    "TOP_DOWN": ["top down", "top-down"],
    "BOTTOM_UP": ["bottom up", "bottom-up"],
    "UNIFICATION": ["unification", "hợp nhất"],
    "LEXICON": ["lexicon", "từ vựng"],
    "ATN": ["atn", "augmented transition network"],
}

# Topic -> chapter, used when the chapter cannot be derived from the
# keywords of the chapters.
TOPIC_TO_CHAPTER: Dict[str, str] = {
    "CFG": "CH03",
    "PCFG": "CH03",
    "PARSING": "CH03",
    "GRAMMAR": "CH03",
    "FEATURE": "CH04",
    "ATN": "CH04",
    "UNIFICATION": "CH04",
    "LEXICON": "CH04",
    "SYNTAX": "CH02",
    "TOP_DOWN": "CH03",
    "BOTTOM_UP": "CH03",
    "BEST_FIRST": "CH06",
    "STATISTICAL_NLP": "CH06",
    "POS": "CH06",
    "POS_TAGGING": "CH06",
    "AMBIGUITY": "CH06",
    "SEMANTIC": "CH07",
    "LOGICAL_FORM": "CH07",
    "THEMATIC_ROLE": "CH07",
    "WORD_SENSE": "CH07",
    "SEMANTIC_GRAMMAR": "CH10",
    "SELECTIONAL_RESTRICTION": "CH09",
    "WORD_DISAMBIGUATION": "CH09",
    "DEPENDENCY": "CH03",
    "KNOWLEDGE_REPRESENTATION": "CH11",
    "REASONING": "CH11",
    "QUESTION_ANSWERING": "CH11",
    "REFERENCE": "CH12",
    "DISCOURSE": "CH12",
    "ANAPHORA": "CH12",
    "CENTERING": "CH12",
    "PYTHON_NLP": "CH01",
}

# Learning outcome -> the chapters that serve it.
LO_TO_CHAPTERS: Dict[str, List[str]] = {
    "LO1": ["CH01"],
    "LO1.1": ["CH01"],
    "LO1.2": ["CH01"],
    "LO1.3": ["CH01"],
    "LO2": ["CH02", "CH03", "CH04", "CH05", "CH06"],
    "LO2.1": ["CH02"],
    "LO2.2": ["CH03", "CH04"],
    "LO2.3": ["CH04"],
    "LO2.4": ["CH03", "CH05"],
    "LO2.5": ["CH06"],
    "LO3": ["CH07", "CH08", "CH09", "CH10"],
    "LO3.1": ["CH07"],
    "LO3.2": ["CH07", "CH08"],
    "LO3.3": ["CH09", "CH10"],
    "LO3.4": ["CH08", "CH10"],
    "LO4": ["CH11", "CH12"],
    "LO4.1": ["CH11"],
    "LO4.2": ["CH12"],
}


class KnowledgeBase:
    """
    Knowledge Base for Course Assistant
    Provides methods to query course information
    """

    def __init__(self):
        self.course = COURSE_INFO
        self.chapters = CHAPTERS
        self.schedule = SCHEDULE
        self.assignment = ASSIGNMENT
        self.resources = RESOURCES
        self.regulations = REGULATIONS
        self.faq = FAQ

    # ------------------------------------------------------------------
    # Course information
    # ------------------------------------------------------------------
    def get_course_info(self, attribute: str = None) -> str:
        """Get course information"""
        if attribute == "credits":
            return (
                f"Môn {self.course.name} ({self.course.course_id}) có "
                f"{self.course.credits} tín chỉ, tương đương {self.course.ects} ECTS."
            )
        elif attribute == "ects":
            return f"Môn học có {self.course.ects} ECTS."
        elif attribute == "parts":
            return (
                f"Môn học gồm {len(self.course.parts)} phần chính: "
                + "; ".join(self.course.parts) + "."
            )
        elif attribute == "midterm_duration":
            return f"Midterm có thời lượng {self.course.exam_duration['midterm']} phút."
        elif attribute == "final_duration":
            return f"Final có thời lượng {self.course.exam_duration['final']} phút."
        elif attribute == "duration":
            return (
                f"Midterm kéo dài {self.course.exam_duration['midterm']} phút và "
                f"Final kéo dài {self.course.exam_duration['final']} phút."
            )
        elif attribute == "description":
            return self.course.description
        elif attribute == "learning_outcomes":
            outcomes = "\n".join(
                [f"- {k}: {v}" for k, v in self.course.learning_outcomes.items()]
            )
            return f"Các mục tiêu học tập:\n{outcomes}"
        elif attribute == "assessment":
            rows = "\n".join([f"- {k}: {v}" for k, v in self.course.assessment.items()])
            return f"Cách đánh giá môn học:\n{rows}"
        elif attribute == "prerequisites":
            return "Môn học yêu cầu: " + ", ".join(self.course.prerequisites) + "."
        else:
            return (
                f"Môn {self.course.name} ({self.course.course_id}), "
                f"{self.course.credits} tín chỉ, học kỳ {self.course.semester}."
            )

    # ------------------------------------------------------------------
    # Chapters
    # ------------------------------------------------------------------
    def get_chapter_info(self, chapter_id: str) -> str:
        """Get chapter information"""
        if chapter_id in self.chapters:
            ch = self.chapters[chapter_id]
            number = chapter_id[2:]
            lines = [
                f"Chương {number} - {ch.name}",
                f"Thuộc phần: {ch.part}.",
                f"Nội dung: {ch.summary}",
                "Các chủ đề chính: " + "; ".join(ch.subtopics) + ".",
            ]
            if ch.week:
                lines.append(f"Chương này được học vào tuần {ch.week}.")
            if ch.methods:
                lines.append("Phương pháp chính: " + "; ".join(ch.methods) + ".")
            if ch.learning_outcomes:
                lines.append(
                    "Phục vụ mục tiêu học tập: " + ", ".join(ch.learning_outcomes) + "."
                )
            return "\n".join(lines)
        return f"Không tìm thấy thông tin Chương {chapter_id}."

    def get_topic_chapter(self, topic: str) -> str:
        """Find which chapter covers a topic"""
        topic_key = (topic or "").strip()
        canonical = topic_key.upper().replace(" ", "_")

        # 1. Explicit mapping.
        target = TOPIC_TO_CHAPTER.get(canonical)
        if target is None:
            for alias_key, aliases in TOPIC_ALIASES.items():
                if topic_key.lower() in aliases:
                    target = TOPIC_TO_CHAPTER.get(alias_key)
                    break

        # 2. Fall back on the keywords of the chapters.
        if target is None:
            aliases = TOPIC_ALIASES.get(canonical, [])
            needles = [topic_key.lower()] + aliases
            for ch_id, ch in self.chapters.items():
                haystack = [k.lower() for k in ch.keywords] + [ch.name.lower()]
                for needle in needles:
                    if any(needle in item for item in haystack):
                        target = ch_id
                        break
                if target:
                    break

        if target and target in self.chapters:
            ch = self.chapters[target]
            return f"Chương {target[2:]}: {ch.name} trình bày về {topic_key}."

        return f"Không tìm thấy chương nào liên quan đến {topic_key}."

    def get_topic_detail(self, topic: str) -> str:
        """A detailed answer about a topic (chapter + sub-topics)."""
        topic_key = (topic or "").strip()
        canonical = topic_key.upper().replace(" ", "_")
        chapter_id = TOPIC_TO_CHAPTER.get(canonical)
        if chapter_id is None:
            for alias_key, aliases in TOPIC_ALIASES.items():
                if topic_key.lower() in aliases:
                    chapter_id = TOPIC_TO_CHAPTER.get(alias_key)
                    break
        if chapter_id and chapter_id in self.chapters:
            ch = self.chapters[chapter_id]
            return (
                f"Chủ đề {topic_key} thuộc Chương {chapter_id[2:]} - {ch.name}.\n"
                f"Nội dung liên quan: " + "; ".join(ch.subtopics) + "."
            )
        return self.get_topic_chapter(topic_key)

    # ------------------------------------------------------------------
    # Schedule
    # ------------------------------------------------------------------
    def get_schedule(self, week: str = None) -> str:
        """Get schedule information"""
        if week:
            if week in self.schedule:
                info = self.schedule[week]
                ch = self.chapters.get(info["chapter"], None)
                lines = []
                if ch:
                    lines.append(
                        f"Tuần {week[5:]}: Học Chương {info['chapter'][2:]} - {ch.name}."
                    )
                else:
                    lines.append(f"Tuần {week[5:]}: ôn tập và tổng kết.")
                lines.append("Nội dung: " + ", ".join(info["topics"]) + ".")
                if info.get("activity"):
                    lines.append(f"Hoạt động: {info['activity']}.")
                if info.get("milestone"):
                    lines.append(f"Mốc: {info['milestone']}.")
                return "\n".join(lines)
            return f"Không tìm thấy thông tin lịch học cho {week}."

        lines = ["Lịch học môn học (15 tuần):"]
        for week_id in sorted(self.schedule):
            info = self.schedule[week_id]
            ch = self.chapters.get(info["chapter"])
            ch_name = ch.name if ch else "Ôn tập"
            lines.append(
                f"- Tuần {week_id[5:]}: Chương {info['chapter'][2:]} - {ch_name} "
                f"({', '.join(info['topics'])})"
            )
        return "\n".join(lines)

    def get_chapter_week(self, chapter_id: str) -> str:
        """Find which week a chapter is taught"""
        for week_id in sorted(self.schedule):
            info = self.schedule[week_id]
            if info.get("chapter") == chapter_id:
                ch = self.chapters.get(chapter_id)
                ch_name = ch.name if ch else chapter_id
                return (
                    f"Chương {chapter_id[2:]} ({ch_name}) được học vào "
                    f"Tuần {week_id[5:]}."
                )
        # Fall back on the `week` attribute of the chapter.
        ch = self.chapters.get(chapter_id)
        if ch and ch.week:
            return f"Chương {chapter_id[2:]} được học vào Tuần {ch.week}."
        return f"Không tìm thấy tuần học cho Chương {chapter_id}."

    def get_topic_week(self, topic: str) -> str:
        """Find which week a topic is taught"""
        topic_key = (topic or "").strip()
        canonical = topic_key.upper().replace(" ", "_")
        chapter_id = TOPIC_TO_CHAPTER.get(canonical)
        if chapter_id is None:
            for alias_key, aliases in TOPIC_ALIASES.items():
                if topic_key.lower() in aliases:
                    chapter_id = TOPIC_TO_CHAPTER.get(alias_key)
                    break
        if chapter_id is None:
            chapter_id = self._chapter_from_keywords(topic_key)
        if chapter_id:
            return self.get_chapter_week(chapter_id)
        return f"Không tìm thấy tuần học cho chủ đề {topic_key}."

    def _chapter_from_keywords(self, topic: str) -> Optional[str]:
        """The chapter whose keywords mention the topic."""
        needles = [topic.lower()] + TOPIC_ALIASES.get(topic.upper().replace(" ", "_"), [])
        for ch_id, ch in self.chapters.items():
            haystack = [k.lower() for k in ch.keywords] + [ch.name.lower()]
            for needle in needles:
                if any(needle in item for item in haystack):
                    return ch_id
        return None

    # ------------------------------------------------------------------
    # Assignment
    # ------------------------------------------------------------------
    def get_assignment_info(self, part: str = None, list_parts: bool = False) -> str:
        """Get assignment information"""
        if list_parts:
            parts_str = "; ".join([f"{p['name']}" for p in self.assignment.parts])
            return (
                f"Bài tập lớn '{self.assignment.title}' gồm {len(self.assignment.parts)} "
                f"phần: {parts_str}."
            )
        if part:
            part_upper = part.upper()
            for p in self.assignment.parts:
                if part_upper in p["id"].upper():
                    return self._format_part(p)
            # Also check for roman numerals in part name
            roman_map = {'I': 'I', 'II': 'II', 'III': 'III', 'IV': 'IV'}
            for roman, full in roman_map.items():
                if full in part_upper:
                    for p in self.assignment.parts:
                        if roman in p["id"]:
                            return self._format_part(p)
        return (
            f"Bài tập lớn '{self.assignment.title}' - Nhóm {self.assignment.team_size}. "
            f"Mục tiêu: {self.assignment.goal}"
        )

    @staticmethod
    def _format_part(part: Dict[str, str]) -> str:
        """The description of one part plus the files it has to deliver."""
        lines = [f"{part['name']}: {part['description']}"]
        deliverables = part.get("deliverables")
        if deliverables:
            lines.append("File cần xuất: " + "; ".join(deliverables) + ".")
        return "\n".join(lines)

    def get_assignment_deliverables(self, part: str = None) -> str:
        """The files that a given part of the assignment has to deliver."""
        if part:
            part_upper = part.upper()
            for p in self.assignment.parts:
                if part_upper in p["id"].upper():
                    deliverables = p.get("deliverables") or []
                    if deliverables:
                        return (
                            f"Phần {p['id']} ({p['name']}) cần xuất các file: "
                            + "; ".join(deliverables) + "."
                        )
                    return f"Phần {p['id']} ({p['name']}) không có yêu cầu file riêng."
        return "Sản phẩm cần nộp của bài tập lớn: " + "; ".join(
            self.assignment.deliverables
        ) + "."

    def get_assignment_full(self) -> str:
        """The complete description of the assignment."""
        lines = [
            f"Bài tập lớn: {self.assignment.title}",
            f"Nhóm: {self.assignment.team_size}",
            f"Mục tiêu: {self.assignment.goal}",
            "Các phần:",
        ]
        for p in self.assignment.parts:
            lines.append(f"- {p['id']} - {p['name']}: {p['description']}")
        lines.append("Sản phẩm cần nộp: " + "; ".join(self.assignment.deliverables) + ".")
        lines.append("Tiêu chí đánh giá: " + "; ".join(self.assignment.evaluation_criteria) + ".")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Deadline
    # ------------------------------------------------------------------
    def get_deadline(self) -> str:
        """Get assignment deadlines"""
        deadlines = "\n".join(
            [f"- {k}: {v}" for k, v in self.assignment.deadlines.items()]
        )
        return f"Thời hạn BTL:\n{deadlines}"

    # ------------------------------------------------------------------
    # Resource
    # ------------------------------------------------------------------
    def get_resource(self, topic: str = None) -> str:
        """Get learning resources"""
        if topic:
            topic_key = (topic or "").strip()
            canonical = topic_key.upper().replace(" ", "_")
            needles = [topic_key.lower()] + TOPIC_ALIASES.get(canonical, [])
            relevant = []
            for r in self.resources:
                haystack = [r.title.lower()] + [t.lower() for t in r.topics]
                if any(needle in item for item in haystack for needle in needles):
                    relevant.append(f"- {r.title} ({r.author}, {r.year}) - {r.usage}")
            if relevant:
                return (
                    f"Tài liệu về {topic_key}:\n" + "\n".join(relevant)
                )
            # No specific document: recommend the general reference list.
            return (
                f"Không có tài liệu riêng cho {topic_key}. "
                f"Các tài liệu tham khảo tổng quát:\n"
                + "\n".join(f"- {r.title} ({r.author}, {r.year})" for r in self.resources)
            )
        return (
            f"Tài liệu tham khảo: {len(self.resources)} mục.\n"
            + "\n".join(
                f"- {r.title} ({r.author}, {r.year}) [{r.type}]: {r.usage}"
                for r in self.resources
            )
        )

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------
    def get_regulation(self, rule: str = None) -> str:
        """Get regulations"""
        if rule:
            rule_upper = rule.upper()
            if "LLM" in rule_upper or "RAG" in rule_upper:
                return self.regulations["llm_rag"]
            if "ACADEMIC" in rule_upper:
                return self.regulations["academic_integrity"]
            if "COPYRIGHT" in rule_upper:
                return self.regulations["copyright"]
            if "POLICY" in rule_upper:
                return self.regulations["policy"]
            if "AI" in rule_upper:
                return self.regulations["ai_usage"]
        return (
            "Các quy định của môn học:\n"
            + "\n".join(f"- {k}: {v}" for k, v in self.regulations.items())
        )

    def get_all_regulations(self) -> str:
        """Every regulation of the course."""
        return (
            "Các quy định của môn học:\n"
            + "\n".join(f"- {k}: {v}" for k, v in self.regulations.items())
        )

    # ------------------------------------------------------------------
    # Learning outcomes
    # ------------------------------------------------------------------
    def get_learning_outcome(self, lo_id: str) -> str:
        """Get learning outcome information"""
        if not lo_id:
            return "Vui lòng cho biết mã LO cụ thể (ví dụ: LO1, LO2.1)"
        lo_key = lo_id.upper().replace("LO", "LO")
        if lo_key in self.course.learning_outcomes:
            lines = [f"{lo_key}: {self.course.learning_outcomes[lo_key]}"]
            chapters = LO_TO_CHAPTERS.get(lo_key)
            if chapters:
                names = "; ".join(
                    f"Chương {c[2:]} - {self.chapters[c].name}"
                    for c in chapters if c in self.chapters
                )
                lines.append(f"Được phục vụ bởi: {names}.")
            return "\n".join(lines)
        return f"Không tìm thấy thông tin {lo_id}."

    def get_lo_chapter(self, lo_id: str) -> str:
        """The chapter that serves a given learning outcome."""
        lo_key = (lo_id or "").upper().replace("LO", "LO")
        chapters = LO_TO_CHAPTERS.get(lo_key)
        if not chapters:
            return f"Không tìm thấy chương nào phục vụ {lo_id}."
        names = "; ".join(
            f"Chương {c[2:]} - {self.chapters[c].name}"
            for c in chapters if c in self.chapters
        )
        return f"{lo_key} được phục vụ bởi: {names}."

    # ------------------------------------------------------------------
    # Instructor
    # ------------------------------------------------------------------
    def get_instructor(self) -> str:
        """Information about the teacher."""
        return (
            f"Giảng viên phụ trách môn {self.course.name} ({self.course.course_id}) là "
            f"{self.course.instructor}. Giờ gặp trực tiếp: {self.course.office_hours}."
        )

    # ------------------------------------------------------------------
    # Fallback answers
    # ------------------------------------------------------------------
    def ask_for_clarification(self) -> str:
        """The answer used when the query needs more context."""
        return (
            "Tôi cần thêm ngữ cảnh để trả lời câu hỏi này. "
            "Bạn có thể cho biết câu hỏi trước đó nói về chương hoặc phần nào không?"
        )

    def unknown_answer(self) -> str:
        """The answer used when the intent could not be determined."""
        return (
            "Xin lỗi, tôi không hiểu câu hỏi này. Vui lòng hỏi về thông tin môn học "
            "NLP như lịch học, nội dung chương, bài tập, tài liệu, hoặc quy định."
        )

    def out_of_scope_answer(self) -> str:
        """The answer used for a question outside the scope of the course."""
        return self.regulations["out_of_scope"]

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------
    def query(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        Query the knowledge base based on intent and entities
        """
        entities = entities or {}

        if intent == "GET_COURSE_INFO":
            attr = entities.get("attribute")
            return self.get_course_info(attr)

        elif intent == "GET_TOPIC":
            if "chapter" in entities:
                return self.get_chapter_info(entities["chapter"])
            if "topic" in entities:
                return self.get_topic_detail(entities["topic"])
            if "lo" in entities:
                # "Nội dung này nằm ở chương nào?" -- the learning outcome
                # is resolved from the dialogue context.
                return self.get_lo_chapter(entities["lo"])

        elif intent == "GET_SCHEDULE":
            # Check if asking about which week a chapter/topic is taught
            if "week" in entities:
                return self.get_schedule(entities["week"])
            if "chapter" in entities:
                return self.get_chapter_week(entities["chapter"])
            if "topic" in entities:
                return self.get_topic_week(entities["topic"])
            return self.get_schedule(None)

        elif intent == "GET_ASSIGNMENT":
            if entities.get("ask_deliverables"):
                answer = self.get_assignment_deliverables(entities.get("part"))
                if answer:
                    return answer
            return self.get_assignment_info(
                part=entities.get("part"),
                list_parts=entities.get("list_parts", False)
            )

        elif intent == "GET_DEADLINE":
            return self.get_deadline()

        elif intent == "GET_RESOURCE":
            return self.get_resource(entities.get("topic"))

        elif intent == "GET_RULE":
            return self.get_regulation(entities.get("rule"))

        elif intent == "GET_LO":
            return self.get_learning_outcome(entities.get("lo"))

        elif intent == "GET_INSTRUCTOR":
            return self.get_instructor()

        elif intent == "CONTEXT_DEPENDENT":
            return self.ask_for_clarification()

        elif intent == "UNKNOWN":
            if entities.get("scope") == "OUT_OF_SCOPE":
                return self.out_of_scope_answer()
            return self.unknown_answer()

        return self.unknown_answer()


def main():
    """Test knowledge base"""
    kb = KnowledgeBase()

    print("Knowledge Base Test")
    print("=" * 60)

    print("\n1. Course Info:")
    print(kb.get_course_info("credits"))

    print("\n2. Chapter Info:")
    print(kb.get_chapter_info("CH03"))

    print("\n3. Topic Search:")
    print(kb.get_topic_chapter("CFG"))

    print("\n4. Schedule:")
    print(kb.get_schedule("WEEK_03"))

    print("\n5. Assignment:")
    print(kb.get_assignment_info("PART_I"))

    print("\n6. Deadline:")
    print(kb.get_deadline())

    print("\n7. Resource:")
    print(kb.get_resource("NLP"))

    print("\n8. Regulation:")
    print(kb.get_regulation("ai"))


if __name__ == "__main__":
    main()
