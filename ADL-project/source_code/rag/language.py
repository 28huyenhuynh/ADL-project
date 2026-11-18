"""
Multilingual questions.

The embedding model (nomic-embed-text) is trained mostly on English. A Vietnamese question
such as "Môn ARTS 309 cần học trước những môn nào?" retrieves the wrong pages (20, 25)
while the same question in English finds the right ones (30, 31). So:

  1. the language of the question is detected (Vietnamese and non-Latin scripts by their
     characters, other cases by the LLM);
  2. a non-English question is translated into English by the LLM, and the English text
     is used for the scope guard, the follow-up rules and the vector search;
  3. the answer is written in the language of the question.

Fixed messages (declines, greeting, "not found") are written by hand for English and
Vietnamese; for other languages the English message is translated by the LLM.
"""

import re

from . import scope

ENGLISH = "English"
VIETNAMESE = "Vietnamese"

# Letters only Vietnamese uses (é, à, ê, ô... are shared with French, so they do not count).
_VI_CHARS = re.compile("[ăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịĩọỏốồổỗộớờởỡợụủũứừửữựỳỵỷỹ]", re.IGNORECASE)
_SCRIPTS = [  # Japanese before Chinese: Japanese text also uses Chinese characters
    (re.compile(r"[぀-ヿ]"), "Japanese"),
    (re.compile(r"[一-鿿]"), "Chinese"),
    (re.compile(r"[가-힯]"), "Korean"),
    (re.compile(r"[฀-๿]"), "Thai"),
    (re.compile(r"[Ѐ-ӿ]"), "Russian"),
    (re.compile(r"[؀-ۿ]"), "Arabic"),
    (re.compile(r"[ऀ-ॿ]"), "Hindi"),
]
_EN_WORDS = set("""the a an is are was what which who whom how many much do does did can could
should would will i my me we our you your for of to in on at and or with about from
there this that any course courses credits major minor""".split())

NOT_FOUND_TEXT = {
    ENGLISH: scope.NOT_FOUND,
    VIETNAMESE: "Mình không tìm thấy thông tin này trong sổ tay ngành.",
}

VI_SUBJECTS = {
    "Mathematics": "Toán học", "Computer Science": "Khoa học Máy tính", "Economics": "Kinh tế học",
    "Engineering": "Kỹ thuật", "Psychology": "Tâm lý học", "Integrated Sciences": "Khoa học Tích hợp",
    "Literature": "Văn học", "History": "Lịch sử", "Vietnam Studies": "Việt Nam học",
    "Social Studies": "Khoa học Xã hội", "Medicine": "Y khoa", "Law": "Luật",
}

_VI = {
    "out_of_scope": ("{s} nằm ngoài phạm vi của mình. Mình chỉ biết Sổ tay ngành Nghệ thuật & Truyền thông "
                     "(AMS) của Đại học Fulbright Việt Nam, nên không thể trả lời về yêu cầu, tín chỉ hay môn học "
                     "của {s}, và mình không muốn đoán. Bạn hãy xem sổ tay ngành {s} hoặc hỏi Phòng Đào tạo "
                     "(Registrar's Office).\n\nNếu bạn muốn hỏi {s} liên quan thế nào tới AMS (ví dụ học song "
                     "song với ngành AMS), hãy hỏi mình và mình sẽ tra trong sổ tay."),
    "off_topic": ("Câu hỏi này nằm ngoài phạm vi của mình. Mình chỉ trả lời về Sổ tay ngành Nghệ thuật & "
                  "Truyền thông (AMS) của Fulbright: yêu cầu ngành chính và ngành phụ, các môn ARTS và điều kiện "
                  "tiên quyết, Capstone, quy định, giảng viên, chuẩn đầu ra và nghề nghiệp. Bạn thử hỏi, ví dụ: "
                  "\"Cần hoàn thành những gì để khai báo ngành AMS?\""),
    "greeting": ("Xin chào! Mình trả lời các câu hỏi về Sổ tay ngành Nghệ thuật & Truyền thông (AMS) của "
                 "Fulbright: yêu cầu ngành chính và ngành phụ, các môn ARTS và điều kiện tiên quyết, Capstone, "
                 "quy định, giảng viên, chuẩn đầu ra và nghề nghiệp. Bạn muốn biết điều gì?"),
    "thanks": "Không có gì! Bạn cứ hỏi thêm về sổ tay ngành AMS nhé.",
}

DECLINED_SCOPES = {"other_subject", "off_topic", "greeting"}


def detect(text: str, llm=None) -> str:
    """Language name in English ("English", "Vietnamese", "French", ...)."""
    if _VI_CHARS.search(text):
        return VIETNAMESE
    for pattern, name in _SCRIPTS:
        if pattern.search(text):
            return name
    words = re.findall(r"[a-z']+", text.lower())
    if not words or text.isascii() or any(w in _EN_WORDS for w in words):
        return ENGLISH
    if llm is None:
        return ENGLISH
    reply = llm.invoke("What language is the following text written in? Answer with one word, "
                       f"the language name in English.\n\nText: {text}\nLanguage:").strip()
    name = re.sub(r"[^A-Za-z]", "", reply.split()[0]) if reply else ""
    return name.capitalize() or ENGLISH


def to_english(llm, text: str, language: str) -> str:
    if language == ENGLISH:
        return text
    reply = llm.invoke(
        f"Translate the following {language} question into English. Keep course codes (such as ARTS 309), "
        f"names and numbers exactly as they are. Output only the English question.\n\n"
        f"{language}: {text}\nEnglish:").strip()
    line = next((l for l in reply.splitlines() if l.strip()), text)
    # Small models often prefix a label ("English: ...") or wrap the text in quotes.
    line = re.sub(r"^\s*(english( translation)?|translation)\s*:\s*", "", line, flags=re.IGNORECASE)
    return line.strip().strip('"“”').strip() or text


def translate_answer(llm, english: str, language: str):
    """Streams the English answer translated into the language of the question."""
    prompt = (f"Translate the following answer into {language}. Keep course codes (such as ARTS 309), numbers, "
              f"names and page citations such as (p. 7) exactly as they are, and keep the list formatting. "
              f"Output only the translation.\n\nAnswer:\n{english}\n\n{language}:\n")
    return llm.stream(prompt)


def not_found(language: str) -> str:
    return NOT_FOUND_TEXT.get(language, scope.NOT_FOUND)


def _english_message(kind: str, subjects: list[str], question: str) -> str:
    if kind == "other_subject":
        return scope.out_of_scope_message(subjects)
    if kind == "off_topic":
        return scope.off_topic_message()
    return scope.greeting_message("thanks" if kind == "thanks" else question)


def message(kind: str, language: str, subjects: list[str] | None = None, question: str = "", llm=None) -> str:
    """A fixed reply (decline, greeting, thanks) in the language of the question."""
    subjects = subjects or []
    if language == VIETNAMESE:
        if kind == "other_subject":
            names = [VI_SUBJECTS.get(s, s) for s in subjects]
            s = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " và " + names[-1]
            return _VI["out_of_scope"].format(s=s)
        return _VI.get(kind, _VI["greeting"])
    english = _english_message(kind, subjects, question)
    if language == ENGLISH or llm is None:
        return english
    translated = llm.invoke(f"Translate the following text into {language}. Output only the translation.\n\n"
                            f"{english}").strip()
    return translated or english


def normalize_history(history: list[dict] | None) -> list[dict]:
    """
    The browser stores each turn as the user saw it (maybe in Vietnamese) plus the English
    question and how the turn was handled. The scope guard and the follow-up rules work on
    English, and recognise a declined turn by its English wording, so each turn is mapped
    back: English question, and an English decline text for declined turns.
    """
    out = []
    for t in history or []:
        q = t.get("question_en") or t.get("question", "")
        a = t.get("answer", "")
        kind = t.get("scope")
        if kind == "other_subject":
            a = scope.out_of_scope_message(scope.other_subjects(q) or ["This subject"])
        elif kind in ("off_topic", "greeting"):
            a = scope.off_topic_message()
        elif any(a.strip().startswith(nf) for nf in NOT_FOUND_TEXT.values()):
            a = scope.NOT_FOUND
        out.append({"question": q, "answer": a})
    return out
