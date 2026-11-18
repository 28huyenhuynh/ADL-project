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
# Common Vietnamese words written without the letters above ("Xin chào", "Cho hỏi").
_VI_WORDS = {"xin", "chào", "cho", "hỏi", "không", "và", "có", "gì", "nào", "thì", "bao", "nhiêu",
             "môn", "ngành", "học", "tín", "chỉ", "sao", "còn", "của", "anh", "chị", "bạn", "ơi"}
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
    if _VI_CHARS.search(text) or _VI_WORDS & set(re.findall(r"\w+", text.lower())):
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


# Lessons from testing with qwen2.5:1.5b: it copies worked examples and example values
# from the prompt into its output ("What about the minor?" for any "Còn ... thì sao?",
# "ARTS 309 (p. 7)" added to answers). So the prompts contain no examples, and every
# translation is checked by code instead of trusting the model.

# Vietnamese greetings and thanks are answered without any translation.
_VI_GREETING = re.compile(r"^\s*(xin chào|chào( bạn| bot| mình| anh| chị)?|alo|hello|hi)\b[\s!.,?~]*$", re.IGNORECASE)
_VI_THANKS = re.compile(r"^\s*(cảm ơn|cám ơn|thank)\w*( bạn| nhiều| nha| nhé)*[\s!.,?~]*$", re.IGNORECASE)

# The usual Vietnamese follow-up forms, rewritten by rule so the English keeps the
# follow-up signal that scope.py relies on:
#   "Còn ngành AMS thì sao?"           -> "What about <ngành AMS>?"
#   "Còn điều kiện tiên quyết của nó?" -> "And <điều kiện tiên quyết của nó>?"
_VI_WHAT_ABOUT = re.compile(r"^\s*còn\s+(.+?)\s+thì\s+(sao|thế nào|như thế nào)\s*\??\s*$", re.IGNORECASE)
_VI_AND = re.compile(r"^\s*còn\s+(.+?)\s*\??\s*$", re.IGNORECASE)

# Codes and numbers that must survive a translation: "ARTS 309", "CS201", "AMS", "GPA", "3.6".
_KEY_TOKENS = re.compile(r"\b[A-Z]{2,5}\s?\d{3}\b|\b[A-Z]{2,5}\b|\d+(?:[.,]\d+)?")


def fixed_kind(text: str, language: str) -> str | None:
    """'greeting' / 'thanks' for a Vietnamese greeting, so it needs no translation."""
    if language != VIETNAMESE:
        return None
    if _VI_THANKS.match(text):
        return "thanks"
    if _VI_GREETING.match(text):
        return "greeting"
    return None


def _clean(reply: str, fallback: str) -> str:
    line = next((l for l in reply.splitlines() if l.strip()), fallback)
    # Small models often prefix a label ("English: ...") or wrap the text in quotes.
    line = re.sub(r"^\s*(english( translation)?|translation|question)\s*:\s*", "", line, flags=re.IGNORECASE)
    return line.strip().strip('"“”').strip() or fallback


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text).upper()


def _missing_tokens(source: str, translation: str) -> list[str]:
    have = _norm(translation)
    return [t for t in dict.fromkeys(_KEY_TOKENS.findall(source)) if _norm(t) not in have]


def _translate_question(llm, text: str, language: str) -> str:
    reply = llm.invoke(
        f"Translate this {language} question into English. Translate it literally and completely. Keep all "
        f"course codes, abbreviations, names and numbers exactly as written, and keep words that point to "
        f"something said earlier (it, its, that, this course). Output only the English question.\n\n"
        f"{language}: {text}\nEnglish:").strip()
    return _clean(reply, text)


def to_english(llm, text: str, language: str) -> str:
    if language == ENGLISH:
        return text
    if language == VIETNAMESE:
        m = _VI_WHAT_ABOUT.match(text)
        if m:
            return f"What about {_translate_question(llm, m.group(1), language).rstrip('?.')}?"
        m = _VI_AND.match(text)
        if m:
            return f"And {_translate_question(llm, m.group(1), language).rstrip('?.')}?"
    english = _translate_question(llm, text, language)
    if _missing_tokens(text, english):             # a code or number got lost: try once more
        english = _translate_question(llm, text, language)
    missing = _missing_tokens(text, english)
    return (english + " " + " ".join(missing)).strip() if missing else english


def _looks_like(text: str, language: str) -> bool:
    """Rough check that a translation is really in `language` and not still English."""
    if language == VIETNAMESE:
        return bool(_VI_CHARS.search(text))
    words = re.findall(r"[a-z']+", text.lower())
    english = sum(w in _EN_WORDS for w in words)
    return not words or english / len(words) < 0.25


def translate_answer(llm, english: str, language: str) -> str:
    """
    The English answer in the language of the question. The translation is accepted only
    if it is really in that language and keeps every number and course code of the
    English answer (a wrong number is worse than an English answer). One retry; then
    the English answer is returned unchanged.
    """
    if language == VIETNAMESE:
        prompt = ("Dịch câu trả lời sau sang tiếng Việt tự nhiên, gọi người hỏi là \"bạn\". Giữ nguyên mọi mã "
                  "môn học, con số, tên riêng, tên môn học bằng tiếng Anh và các trích dẫn trang trong ngoặc. "
                  "Giữ định dạng danh sách. Không thêm thông tin. Chỉ viết bản dịch.\n\n"
                  f"Tiếng Anh:\n{english}\n\nTiếng Việt:\n")
    else:
        prompt = (f"Translate the following answer into {language}. Keep every course code, number, name, "
                  f"English course title and page citation in brackets exactly as written, keep the program name "
                  f"\"Art and Media Studies (AMS)\" in English, keep the list formatting and add nothing. Output "
                  f"only the translation.\n\nEnglish:\n{english}\n\n{language}:\n")
    for _ in range(2):
        text = llm.invoke(prompt).strip()
        if _acceptable(english, text, language):
            return text
    return None


def untranslated_note(language: str, llm=None) -> str:
    if language == VIETNAMESE:
        return ("(Câu trả lời được giữ bằng tiếng Anh vì bản dịch của mô hình chưa đạt kiểm tra độ chính xác. "
                "Đặt TRANSLATE_MODEL=qwen2.5:3b để dịch tốt hơn.)")
    return "(The answer is kept in English because the translation did not pass the accuracy check.)"


_CJK = re.compile(r"[぀-ヿ一-鿿가-힯]")


def _acceptable(english: str, text: str, language: str) -> bool:
    """A translation is used only if it passes every check. Seen with qwen2.5:1.5b: answers
    left in English, Chinese characters inside Vietnamese, and invented text several times
    longer than the original ("Bạn học môn nào? Môn học: Tiếng Anh ...")."""
    if not text or not _looks_like(text, language) or _missing_tokens(english, text):
        return False
    if language not in ("Chinese", "Japanese", "Korean") and _CJK.search(text):
        return False
    ratio = len(text) / max(len(english), 1)
    return 0.5 <= ratio <= 2.5


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
