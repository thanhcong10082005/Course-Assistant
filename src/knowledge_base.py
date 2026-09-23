"""
Knowledge Base module for Course Assistant
Contains all course information for querying
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


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


@dataclass
class ResourceInfo:
    """Learning resource information"""
    resource_id: str
    title: str
    author: Optional[str]
    year: Optional[int]
    type: str  # TEXTBOOK, REFERENCE
    usage: str


# Course Information
COURSE_INFO = CourseInfo(
    course_id="CO3085",
    name="Xử lý Ngôn ngữ Tự nhiên",
    name_en="Natural Language Processing",
    credits=3,
    ects=6,
    semester="HK261",
    department="Khoa Khoa học và Kỹ thuật Máy tính",
    description="Môn học cung cấp các khái niệm, lý thuyết và kỹ thuật nền tảng của xử lý ngôn ngữ tự nhiên.",
    parts=["Xử lý cú pháp", "Diễn dịch ngữ nghĩa", "Ngữ cảnh và tri thức thế giới"],
    learning_outcomes={
        "LO1": "Tổng quan về tổ chức hệ thống NLP và các ứng dụng",
        "LO2": "Xử lý cú pháp; xây dựng văn phạm đơn giản và phân tích cú pháp",
        "LO3": "Diễn dịch ngữ nghĩa; tạo dạng luận lý và giải quyết nhập nhằng",
        "LO4": "Ngữ nghĩa và tri thức thế giới; xây dựng cơ sở tri thức và hệ thống hỏi đáp đơn giản",
        "LO1.1": "Hiểu cấu trúc hệ thống NLP, ứng dụng và cách đánh giá hệ thống hiểu ngôn ngữ tự nhiên.",
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
    }
)

# Chapter Information
CHAPTERS = {
    "CH01": ChapterInfo(
        chapter_id="CH01",
        name="Introduction to Natural Language Processing",
        part="Introduction",
        keywords=["NLP", "NLU", "text-based", "dialog-based", "evaluation"],
        summary="NLP studies computational methods for processing natural language. Introduces applications, levels of language analysis, representation and understanding.",
        subtopics=["The study of natural language", "Applications of NLU", "Evaluating NLU systems", 
                  "Different levels of language analysis", "Representation and understanding"]
    ),
    "CH02": ChapterInfo(
        chapter_id="CH02",
        name="Linguistic Background - English Syntax",
        part="Syntactic Processing",
        keywords=["syntax", "word", "noun phrase", "verb phrase", "adjective phrase"],
        summary="Reviews basic English syntax, including words, noun phrases, verb phrases, simple sentences.",
        subtopics=["Words", "Simple noun phrases", "Verb phrases and simple sentences",
                  "Noun phrases revisited", "Adjective phrases", "Adverbial phrases"]
    ),
    "CH03": ChapterInfo(
        chapter_id="CH03",
        name="Grammar and Parsing",
        part="Syntactic Processing",
        keywords=["CFG", "parsing", "PCFG", "dependency grammar", "top-down", "bottom-up"],
        summary="Introduces context-free grammar, sentence structure and parsing methods. PCFG and dependency grammar.",
        subtopics=["Context-Free Grammars", "Top-down parser", "Bottom-up chart parser",
                  "Probabilistic CFG", "Dependency Grammar", "Stanford Dependencies"]
    ),
    "CH04": ChapterInfo(
        chapter_id="CH04",
        name="Features and Augmented Grammar",
        part="Syntactic Processing",
        keywords=["feature", "augmented grammar", "lexicon", "unification", "ATN"],
        summary="Extends formal grammar with feature systems and augmented grammar. Covers lexicon, parsing with features.",
        subtopics=["Feature systems and augmented grammars", "Basic feature systems for English",
                  "Lexicon", "Grammar using feature systems", "Parsing with features",
                  "Augmented transition networks", "Unification grammar"]
    ),
    "CH05": ChapterInfo(
        chapter_id="CH05",
        name="Grammar for Natural Language",
        part="Syntactic Processing",
        keywords=["auxiliary", "movement", "question", "relative clause"],
        summary="Focuses on grammar phenomena important for natural language: auxiliary verbs, movement, questions, relative clauses.",
        subtopics=["Auxiliary verbs and verb phrases", "Movement phenomena", 
                  "Handling questions in CFG", "Relative clauses"]
    ),
    "CH06": ChapterInfo(
        chapter_id="CH06",
        name="Ambiguity Resolution - Statistical Methods",
        part="Syntactic Processing",
        keywords=["probability", "POS tagging", "lexical probability", "PCFG", "best-first"],
        summary="Statistical methods for resolving ambiguity at sentence level. Includes probability theory, POS tagging, PCFG.",
        subtopics=["Basic probability theory", "Estimating probabilities", "Part-of-speech tagging",
                  "Lexical probabilities", "Probabilistic CFG", "Best-first parsing"]
    ),
    "CH07": ChapterInfo(
        chapter_id="CH07",
        name="Semantics and Logical Form",
        part="Semantic Interpretation",
        keywords=["semantics", "logical form", "word sense", "thematic role", "speech act"],
        summary="Introduces semantic interpretation and logical forms, word senses, thematic roles, speech acts.",
        subtopics=["Semantics and logical form", "Word senses and ambiguity",
                  "Basic logical form language", "Encoding ambiguity in logical form",
                  "Thematic roles", "Speech acts and embedded sentences"]
    ),
    "CH08": ChapterInfo(
        chapter_id="CH08",
        name="Linking Syntax and Semantics",
        part="Semantic Interpretation",
        keywords=["compositionality", "semantic interpretation", "semantic role"],
        summary="Connects syntactic parsing with semantic interpretation. Discusses compositionality, semantic roles.",
        subtopics=["Semantic interpretation and compositionality",
                  "Grammar and lexicon with semantic interpretation",
                  "Prepositional phrases and verb phrases",
                  "Lexicalized semantic interpretation and semantic roles",
                  "Handling simple questions"]
    ),
    "CH09": ChapterInfo(
        chapter_id="CH09",
        name="Ambiguity Resolution",
        part="Semantic Interpretation",
        keywords=["selectional restriction", "semantic network", "WSD"],
        summary="Knowledge-based and statistical methods for semantic ambiguity resolution.",
        subtopics=["Selectional restriction", "Semantic filtering",
                  "Semantic networks", "Statistical word sense disambiguation"]
    ),
    "CH10": ChapterInfo(
        chapter_id="CH10",
        name="Other Strategies for Semantic Interpretation",
        part="Semantic Interpretation",
        keywords=["grammatical relations", "semantic grammar", "template matching"],
        summary="Alternative approaches to semantic interpretation including grammatical relations, semantic grammars.",
        subtopics=["Grammatical relations", "Semantic grammars",
                  "Template matching", "Semantically driven parsing"]
    ),
    "CH11": ChapterInfo(
        chapter_id="CH11",
        name="Knowledge Representation and Reasoning",
        part="Context and World Knowledge",
        keywords=["knowledge representation", "reasoning", "frame", "QA"],
        summary="Introduces knowledge representation and reasoning and applies them to question answering.",
        subtopics=["Knowledge representation", "Frames",
                  "Handling natural language quantification",
                  "Time and aspectual classes", "Procedural semantics", "Question answering"]
    ),
    "CH12": ChapterInfo(
        chapter_id="CH12",
        name="Discourse Context and Reference",
        part="Context and World Knowledge",
        keywords=["discourse context", "reference", "anaphora", "pronoun", "centering"],
        summary="Introduces local discourse context and reference expressions: pronouns, centering, definite descriptions.",
        subtopics=["Local discourse context and discourse entities",
                  "Anaphora", "Pronouns and centering",
                  "Definite descriptions", "Ellipsis", "Surface anaphora"]
    )
}

# Week Schedule
SCHEDULE = {
    f"WEEK_{str(i).zfill(2)}": {
        "chapter": f"CH{str((i-1)//2 + 1).zfill(2)}" if i <= 12 else f"CH{str(min((i-1)//2 + 1, 12)).zfill(2)}",
        "topics": [],
    }
    for i in range(1, 16)
}

# Override with actual schedule
SCHEDULE["WEEK_01"] = {"chapter": "CH01", "topics": ["Introduction to NLP", "NLU applications"]}
SCHEDULE["WEEK_02"] = {"chapter": "CH02", "topics": ["English syntax", "Noun phrases", "Verb phrases"]}
SCHEDULE["WEEK_03"] = {"chapter": "CH03", "topics": ["CFG", "Top-down parsing", "Bottom-up parsing"]}
SCHEDULE["WEEK_04"] = {"chapter": "CH04", "topics": ["Feature systems", "Augmented grammar"]}
SCHEDULE["WEEK_05"] = {"chapter": "CH04", "topics": ["Augmented transition networks", "Unification"]}
SCHEDULE["WEEK_06"] = {"chapter": "CH05", "topics": ["Auxiliary verbs", "Movement", "Questions in CFG"]}
SCHEDULE["WEEK_07"] = {"chapter": "CH06", "topics": ["Probability theory", "POS tagging", "PCFG"]}
SCHEDULE["WEEK_08"] = {"chapter": "CH06", "topics": ["Best-first parsing", "Ambiguity resolution"]}
SCHEDULE["WEEK_09"] = {"chapter": "CH07", "topics": ["Semantics", "Logical form", "Thematic roles"]}
SCHEDULE["WEEK_10"] = {"chapter": "CH08", "topics": ["Linking syntax and semantics", "Semantic roles"]}
SCHEDULE["WEEK_11"] = {"chapter": "CH09", "topics": ["Selectional restriction", "Semantic networks"]}
SCHEDULE["WEEK_12"] = {"chapter": "CH10", "topics": ["Semantic grammars", "Template matching"]}
SCHEDULE["WEEK_13"] = {"chapter": "CH11", "topics": ["Knowledge representation", "Frames", "QA"]}
SCHEDULE["WEEK_14"] = {"chapter": "CH12", "topics": ["Discourse context", "Anaphora", "Reference"]}
SCHEDULE["WEEK_15"] = {"chapter": "CH00", "topics": ["Integration", "Evaluation", "Demo"]}

# Assignment Information
ASSIGNMENT = AssignmentInfo(
    assignment_id="BTL01",
    title="Intelligent Course Assistant",
    team_size="3-4 sinh viên",
    goal="Xây dựng hệ thống xử lý câu hỏi tự nhiên trong miền thông tin của một môn học.",
    parts=[
        {"id": "PART_I", "name": "Grammar and Parser", "description": "Xây dựng grammar và parser"},
        {"id": "PART_II", "name": "Semantic Interpretation and QA", "description": "Semantic representation và question answering"},
        {"id": "PART_III", "name": "Local Discourse Context", "description": "Xử lý ngữ cảnh hội thoại (tùy chọn)"},
        {"id": "PART_IV", "name": "Evaluation", "description": "Đánh giá hệ thống"}
    ],
    deadlines={
        "checkpoint_1": "Tuần 8 - Grammar và Parser",
        "checkpoint_2": "Tuần 12 - Semantic và QA",
        "final": "Tuần 15 - Nộp BTL và Demo"
    }
)

# Resources
RESOURCES = [
    ResourceInfo("R01", "Natural Language Processing with Python", "Bird, Klein, Loper", 2009, "TEXTBOOK", "Practical NLP"),
    ResourceInfo("R02", "Speech and Language Processing", "Jurafsky, Martin", 2019, "TEXTBOOK", "Broad NLP reference"),
    ResourceInfo("R03", "Introduction to NLP", "Jacob Eisenstein", 2019, "TEXTBOOK", "NLP foundations"),
    ResourceInfo("R04", "Foundation of Statistical NLP", "Manning, Schütze", 2001, "REFERENCE", "Statistical NLP"),
]

# Regulations
REGULATIONS = {
    "attendance": "Sinh viên được khuyến khích tham dự đầy đủ các buổi học.",
    "academic_integrity": "Sinh viên phải tuân thủ nguyên tắc liêm chính học thuật.",
    "ai_usage": "Sinh viên phải khai báo việc sử dụng AI trong báo cáo.",
    "llm_rag": "LLM/RAG có thể được sử dụng như phần mở rộng, không thay thế yêu cầu NLP cốt lõi.",
    "out_of_scope": "Hệ thống chỉ chịu trách nhiệm trong phạm vi dữ liệu môn học."
}

# FAQ
FAQ = {
    "credits": "Môn Xử lý Ngôn ngữ Tự nhiên (CO3085) có 3 tín chỉ.",
    "parts": "Môn học gồm ba phần chính: Xử lý cú pháp; Diễn dịch ngữ nghĩa; Ngữ cảnh và tri thức thế giới.",
    "cfg_chapter": "CFG được trình bày trong Chương 3, Grammar and Parsing.",
    "llm_allowed": "Có thể sử dụng LLM/RAG như một phần mở rộng nếu được cho phép.",
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
    
    def get_course_info(self, attribute: str = None) -> str:
        """Get course information"""
        if attribute == "credits":
            return f"Môn {self.course.name} ({self.course.course_id}) có {self.course.credits} tín chỉ."
        elif attribute == "ects":
            return f"Môn học có {self.course.ects} ECTS."
        elif attribute == "parts":
            return f"Môn học gồm {len(self.course.parts)} phần chính: " + "; ".join(self.course.parts) + "."
        elif attribute == "midterm_duration":
            return f"Midterm có thời lượng {self.course.exam_duration['midterm']} phút."
        elif attribute == "final_duration":
            return f"Final có thời lượng {self.course.exam_duration['final']} phút."
        elif attribute == "description":
            return self.course.description
        elif attribute == "learning_outcomes":
            outcomes = "\n".join([f"- {k}: {v}" for k, v in self.course.learning_outcomes.items()])
            return f"Các mục tiêu học tập:\n{outcomes}"
        else:
            return f"Môn {self.course.name} ({self.course.course_id}), {self.course.credits} tín chỉ."
    
    def get_chapter_info(self, chapter_id: str) -> str:
        """Get chapter information"""
        if chapter_id in self.chapters:
            ch = self.chapters[chapter_id]
            return f"Chương {chapter_id[2:]} - {ch.name}: {ch.summary}"
        return f"Không tìm thấy thông tin Chương {chapter_id}."
    
    def get_topic_chapter(self, topic: str) -> str:
        """Find which chapter covers a topic"""
        topic_lower = topic.lower()
        topic_aliases = {
            'semantic': ['semantic', 'semantics', 'ngữ_nghĩa', 'semantic grammar'],
            'syntax': ['syntax', 'cú_pháp'],
            'parsing': ['parsing', 'parse'],
            'cfg': ['cfg', 'context-free', 'context free'],
            'pcfg': ['pcfg', 'probabilistic'],
        }
        
        for ch_id, ch in self.chapters.items():
            chapter_keywords_lower = [k.lower() for k in ch.keywords]
            if topic_lower in chapter_keywords_lower:
                return f"Chương {ch_id[2:]}: {ch.name} trình bày về {topic}."
            
            # Check aliases
            aliases = topic_aliases.get(topic_lower, [])
            for alias in aliases:
                if alias in chapter_keywords_lower:
                    return f"Chương {ch_id[2:]}: {ch.name} trình bày về {topic}."
            
            # Substring match in chapter name and keywords
            if topic_lower in ch.name.lower() or any(topic_lower in k for k in chapter_keywords_lower):
                return f"Chương {ch_id[2:]}: {ch.name} trình bày về {topic}."
        
        return f"Không tìm thấy chương nào liên quan đến {topic}."
    
    def get_schedule(self, week: str = None) -> str:
        """Get schedule information"""
        if week:
            if week in self.schedule:
                info = self.schedule[week]
                ch = self.chapters.get(info["chapter"], None)
                if ch:
                    return f"Tuần {week[5:]}: Học Chương {info['chapter'][2:]} - {ch.name}. Nội dung: {', '.join(info['topics'])}."
                return f"Không tìm thấy thông tin lịch học cho {week}."
        return "Vui lòng cho biết tuần cụ thể."
    
    def get_chapter_week(self, chapter_id: str) -> str:
        """Find which week a chapter is taught"""
        for week_id, info in self.schedule.items():
            if info.get("chapter") == chapter_id:
                ch = self.chapters.get(chapter_id)
                ch_name = ch.name if ch else chapter_id
                return f"Chương {chapter_id[2:]} ({ch_name}) được học vào {week_id.replace('_', ' ').title()}."
        return f"Không tìm thấy tuần học cho Chương {chapter_id}."
    
    def get_topic_week(self, topic: str) -> str:
        """Find which week a topic is taught"""
        topic_chapter = self.get_topic_chapter(topic)
        # Extract chapter ID
        import re
        match = re.search(r'Chương (\d+)', topic_chapter)
        if match:
            chapter_id = f"CH{match.group(1).zfill(2)}"
            return self.get_chapter_week(chapter_id)
        return f"Không tìm thấy tuần học cho chủ đề {topic}."
    
    def get_assignment_info(self, part: str = None, list_parts: bool = False) -> str:
        """Get assignment information"""
        if list_parts:
            parts_str = "; ".join([f"{p['name']}" for p in self.assignment.parts])
            return f"Bài tập lớn '{self.assignment.title}' gồm các phần: {parts_str}."
        if part:
            part_upper = part.upper()
            for p in self.assignment.parts:
                if part_upper in p["id"].upper():
                    return f"{p['name']}: {p['description']}"
            # Also check for roman numerals in part name
            roman_map = {'I': 'I', 'II': 'II', 'III': 'III', 'IV': 'IV'}
            for roman, full in roman_map.items():
                if full in part_upper:
                    for p in self.assignment.parts:
                        if roman in p["id"]:
                            return f"{p['name']}: {p['description']}"
        return f"Bài tập lớn '{self.assignment.title}' - Nhóm {self.assignment.team_size}."
    
    def get_deadline(self) -> str:
        """Get assignment deadlines"""
        deadlines = "\n".join([f"- {k}: {v}" for k, v in self.assignment.deadlines.items()])
        return f"Thời hạn BTL:\n{deadlines}"
    
    def get_resource(self, topic: str = None) -> str:
        """Get learning resources"""
        if topic:
            topic_lower = topic.lower()
            relevant = []
            for r in self.resources:
                if topic_lower in r.title.lower():
                    relevant.append(f"- {r.title} ({r.author}, {r.year})")
            if relevant:
                return f"Tài liệu về {topic}:\n" + "\n".join(relevant)
        return f"Tài liệu tham khảo: {len(self.resources)} cuốn sách. Xem danh sách đầy đủ trong resources.txt"
    
    def get_regulation(self, rule: str = None) -> str:
        """Get regulations"""
        if rule:
            rule_lower = rule.lower()
            if "ai" in rule_lower or "llm" in rule_lower:
                return self.regulations["ai_usage"]
            if "giả" in rule_lower or "copy" in rule_lower:
                return self.regulations["academic_integrity"]
        return "Các quy định: " + "; ".join(self.regulations.values())
    
    def get_learning_outcome(self, lo_id: str) -> str:
        """Get learning outcome information"""
        if not lo_id:
            return "Vui lòng cho biết mã LO cụ thể (ví dụ: LO1, LO2.1)"
        lo_key = lo_id.upper().replace("LO", "LO")
        if lo_key in self.course.learning_outcomes:
            return f"{lo_key}: {self.course.learning_outcomes[lo_key]}"
        return f"Không tìm thấy thông tin {lo_id}."
    
    def query(self, intent: str, entities: Dict[str, Any]) -> str:
        """
        Query the knowledge base based on intent and entities
        """
        if intent == "GET_COURSE_INFO":
            attr = entities.get("attribute")
            return self.get_course_info(attr)
        
        elif intent == "GET_TOPIC":
            if "chapter" in entities:
                return self.get_chapter_info(entities["chapter"])
            elif "topic" in entities:
                return self.get_topic_chapter(entities["topic"])
        
        elif intent == "GET_SCHEDULE":
            # Check if asking about which week a chapter/topic is taught
            if "chapter" in entities:
                return self.get_chapter_week(entities["chapter"])
            if "topic" in entities:
                return self.get_topic_week(entities["topic"])
            return self.get_schedule(entities.get("week"))
        
        elif intent == "GET_ASSIGNMENT":
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
        
        return "Xin lỗi, tôi không tìm thấy thông tin này trong dữ liệu môn học."


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
