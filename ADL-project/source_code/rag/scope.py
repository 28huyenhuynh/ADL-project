"""
Scope guard and conversation memory.

Why this exists: the vector search ALWAYS returns the 5 closest chunks, and the
handbook is full of words like "credits", "graduate" and "requirements". So
"How many credits does Mathematics require?" retrieves AMS credit chunks with a
similarity (0.64) as high as a real AMS question (0.66), and the small LLM then
answers with AMS numbers as if they were about Mathematics. A score threshold
cannot separate these, so the question itself is checked before retrieval:

  1. greeting / thanks          -> short friendly reply, no retrieval
  2. names another subject       -> "outside my scope" (unless it also names AMS)
     (Maths, CS, Economics...)
  3. nothing in the handbook is  -> "outside my scope" (decided in pipeline.py
     close enough                   from the best similarity score)

Conversation memory: follow-ups such as "what are its prerequisites?" are
rewritten into a stand-alone search query using the previous question and the
course codes the previous answer mentioned. A follow-up to an out-of-scope
question stays out of scope ("Maths credits?" -> "and its prerequisites?").
"""

import re

NOT_FOUND = "I could not find this in the handbook."

PROGRAM = "the Fulbright Art & Media Studies (AMS) Major Handbook"
SCOPE_TOPICS = ("AMS major and minor requirements, ARTS courses and prerequisites, "
                "the Capstone, policies, faculty, learning outcomes and careers")

# Other disciplines. Each entry: display name -> pattern (case-insensitive unless noted).
# History is only matched as a programme ("history major"), because "art history",
# "film history" and "photography history" are AMS subjects.
OTHER_SUBJECTS = {
    "Mathematics": r"\bmaths?\b|\bmathematic(s|al)?\b|\bapplied math|\bcalculus\b|\balgebra\b|\bstatistics\b|\bgeometry\b",
    "Computer Science": r"\bcomputer sciences?\b|\bcomputing\b|\bprogramming\b|\bcoding\b|\bsoftware engineering\b|\bdata science\b|\bmachine learning\b",
    "Economics": r"\becon(omics?)?\b|\bfinance\b|\baccounting\b|\bbusiness\b|\bmanagement\b",
    "Engineering": r"\bengineering\b|\bengineer\b",
    "Psychology": r"\bpsych(ology)?\b",
    "Integrated Sciences": r"\bintegrated sciences?\b|\bbiology\b|\bchemistry\b|\bphysics\b|\bneuroscience\b",
    "Literature": r"\bliterature major\b|\bmajor in literature\b|\bliterature (minor|program|department|degree)\b",
    "History": r"\bhistory (major|minor|program|department|degree)\b|\b(major|minor|degree) in history\b",
    "Vietnam Studies": r"\bvietnam(ese)? studies\b",
    "Social Studies": r"\bsocial studies\b|\bsocial sciences?\b|\bsociology\b|\bpolitical science\b|\bpublic policy\b",
    "Medicine": r"\bmedicine\b|\bmedical (school|major|degree)\b|\bnursing\b",
    "Law": r"\blaw (school|major|degree)\b|\blegal studies\b",
}
_CS_UPPER = re.compile(r"\bCS\b")   # "CS" only in capitals, so "cs" in other words is ignored

# Courses that exist only in other majors (names taken from the MATH and CS handbooks).
# A question about one of these does not need to name the major to be out of scope.
OTHER_COURSES = {
    "Mathematics": r"\blinear algebra\b|\breal analysis\b|\bdifferential equations?\b|\bdiscrete math(ematics)?\b"
                   r"|\bprobability\b|\boptimi[sz]ation\b|\bstochastic\b|\boperations? research\b|\bmultivariable\b"
                   r"|\bquantitative finance\b",
    "Computer Science": r"\bdata structures?\b|\balgorithms?\b|\boperating systems?\b|\bcomputer networks?\b"
                        r"|\bdatabase systems?\b|\bcomputer security\b|\bcomputer organi[sz]ation\b"
                        r"|\bsoftware construction\b|\bhuman.computer interaction\b|\bprogramming language",
}

# Course codes of other majors: "MATH 201", "CS201", "ECON 105". Two-letter and "HIS" codes
# must be in capitals, so ordinary words ("is", "his") are not mistaken for them.
OTHER_CODES = [
    (re.compile(r"\bMATH\s?-?\d{3}\b", re.IGNORECASE), "Mathematics"),
    (re.compile(r"\bCS\s?-?\d{3}\b"), "Computer Science"),
    (re.compile(r"\bECON\s?-?\d{3}\b", re.IGNORECASE), "Economics"),
    (re.compile(r"\bPSYC?\s?-?\d{3}\b", re.IGNORECASE), "Psychology"),
    (re.compile(r"\bLIT\s?-?\d{3}\b", re.IGNORECASE), "Literature"),
    (re.compile(r"\bHIS\s?-?\d{3}\b"), "History"),
    (re.compile(r"\bSOCI\s?-?\d{3}\b", re.IGNORECASE), "Social Studies"),
    (re.compile(r"\bIS\s?-?\d{3}\b"), "Integrated Sciences"),
    (re.compile(r"\bVS\s?-?\d{3}\b"), "Vietnam Studies"),
    (re.compile(r"\b(?:HCE|ENGR?)\s?-?\d{3}\b", re.IGNORECASE), "Engineering"),
]

# Words that tie a question to this handbook. A question with a STRONG anchor is in
# scope even if it also names another subject ("Can AMS students minor in CS?").
AMS_STRONG = (
    r"\bAMS\b|\barts?\b|\bmedia\b|\bfilms?\b|\bfilmmaking\b|\bcinema\b|\bvisual\b|\bARTS\s?-?\d{3}"
    r"|\bcurat\w*|\bphotograph\w*|\bstudio\b|\bperform\w*|\btheat(er|re)\b|\bdance\b"
    r"|\bdrawing\b|\bpainting\b|\bsculpture\b|\banimation\b|\bdocumentar\w*"
)
# Weak anchors ("the major", "the handbook") only count when no other subject is named:
# "What do I need to declare Computer Science as my major?" is still about CS.
AMS_WEAK = r"\bhandbook\b|\b(this|the|my|our|your) (major|minor|program|programme|department)\b"
AMS_ANCHOR = re.compile(AMS_STRONG + "|" + AMS_WEAK, re.IGNORECASE)
AMS_STRONG_ANCHOR = re.compile(AMS_STRONG, re.IGNORECASE)

GREETING = re.compile(
    r"^\s*(hi|hello|hey|hiya|yo|greetings|good (morning|afternoon|evening)|xin ch[aà]o|ch[aà]o"
    r"|thanks?( you)?( so much| a lot)?|thank you|ok(ay)?|cool|great|bye|goodbye)\b[\s!.,?~]*$",
    re.IGNORECASE,
)
THANKS = re.compile(r"\bthank|\bthanks\b", re.IGNORECASE)

COURSE_CODE = re.compile(r"\bARTS\s?-?(\d{3})\b", re.IGNORECASE)

# Signals that a question leans on the previous turn.
FOLLOW_UP = re.compile(
    r"^\s*(and|also|what about|how about|then|so|but|or)\b"
    r"|\b(it|its|it's|this|that|these|those|they|them|their|the same|the course|that course|this course"
    r"|the class|that class|the one|the former|the latter|there)\b",
    re.IGNORECASE,
)

# Refusal answers are recognised by these openings, so they are not fed back to the LLM
# as "facts" and an out-of-scope topic can be carried into its follow-ups.
OUT_OF_SCOPE_MARK = "is outside my scope"
OFF_TOPIC_MARK = "That question is outside my scope"


def other_subjects(text: str) -> list[str]:
    found = [name for name, pattern in OTHER_SUBJECTS.items() if re.search(pattern, text, re.IGNORECASE)]

    def add(name):
        if name not in found:
            found.append(name)

    if _CS_UPPER.search(text):
        add("Computer Science")
    for pattern, name in OTHER_CODES:
        if pattern.search(text):
            add(name)
    for name, pattern in OTHER_COURSES.items():
        if re.search(pattern, text, re.IGNORECASE):
            add(name)
    return found


def mentions_ams_strongly(text: str) -> bool:
    return bool(AMS_STRONG_ANCHOR.search(text))


def mentions_ams(text: str) -> bool:
    return bool(AMS_ANCHOR.search(text))


def is_follow_up(question: str) -> bool:
    return bool(FOLLOW_UP.search(question)) or len(question.split()) <= 3


def is_refusal(answer: str) -> bool:
    a = (answer or "").strip()
    return a.startswith(NOT_FOUND) or OUT_OF_SCOPE_MARK in a or a.startswith(OFF_TOPIC_MARK)


def _join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def out_of_scope_message(subjects: list[str]) -> str:
    s = _join(subjects)
    return (f"{s} {OUT_OF_SCOPE_MARK}. I only know {PROGRAM}, so I cannot tell you about "
            f"{s} requirements, credits or courses, and I would rather not guess. "
            f"Please check the {s} handbook or ask the Registrar's Office.\n\n"
            f"If you meant how {s} relates to AMS (for example, combining it with an AMS major), "
            f"ask me that and I will look in the handbook.")


def off_topic_message() -> str:
    return (f"{OFF_TOPIC_MARK}. I only answer questions about {PROGRAM}: {SCOPE_TOPICS}. "
            f"Try asking, for example, \"What do I need to declare the AMS major?\"")


def greeting_message(question: str) -> str:
    if THANKS.search(question):
        return "You are welcome. Ask me anything else about the AMS Major Handbook."
    return (f"Hello. I answer questions about {PROGRAM}: {SCOPE_TOPICS}. "
            f"What would you like to know?")


def last_answered(history: list[dict] | None) -> dict | None:
    """The most recent turn that was a real (non-refused) answer."""
    for turn in reversed(history or []):
        if not is_refusal(turn.get("answer", "")):
            return turn
    return None


def resolve(question: str, history: list[dict] | None) -> dict:
    """
    Decides what to do with a question, before any retrieval.

    Returns {"action": "answer" | "refuse", "query": str, "message": str | None,
             "subjects": list[str], "follow_up": bool}
    `query` is the stand-alone text used for the vector search.
    """
    q = question.strip()
    history = history or []

    if GREETING.match(q):
        return {"action": "refuse", "query": q, "message": greeting_message(q), "kind": "thanks" if THANKS.search(q) else "greeting", "subjects": [], "follow_up": False, "context": None}

    subjects = other_subjects(q)
    if subjects and not mentions_ams_strongly(q):
        return {"action": "refuse", "query": q, "message": out_of_scope_message(subjects), "kind": "other_subject",
                "subjects": subjects, "follow_up": False, "context": None}

    follow = bool(history) and is_follow_up(q) and not COURSE_CODE.search(q) and not subjects

    if follow:
        topic = _topic_turn(history)
        topic_q = topic["question"] if topic else ""
        prev_subjects = other_subjects(topic_q) if topic_q and not mentions_ams_strongly(topic_q) else []
        # The conversation is on another subject: a follow-up ("and its prerequisites?")
        # is about that subject too, unless it now names AMS.
        if prev_subjects and not mentions_ams_strongly(q):
            return {"action": "refuse", "query": q, "message": out_of_scope_message(prev_subjects), "kind": "other_subject",
                    "subjects": prev_subjects, "follow_up": True, "context": None}

        base_q, codes = None, []
        if prev_subjects:
            # "Maths credits?" (refused) -> "What about AMS then?": keep the topic of the
            # refused question but drop the other subject, so the search is about AMS credits.
            stripped = strip_subjects(topic_q)
            if _content_words(stripped) >= 2:
                base_q = stripped
        if base_q is None:
            base = last_answered(history)
            if not base:
                return {"action": "answer", "query": q, "message": None, "subjects": [], "follow_up": False, "context": None}
            base_q = base["question"]
            # What "it" refers to: the course in the last question, else courses in the last answer.
            codes = _codes(base_q) or _codes(base.get("answer", ""))[:2]
        query = " ".join([base_q, q] + codes).strip()
        return {"action": "answer", "query": query, "message": None, "subjects": [], "follow_up": True,
                "context": base_q}

    return {"action": "answer", "query": q, "message": None, "subjects": [], "follow_up": False, "context": None}


_STOP = set("""a an and also about are as at be but can could do does for from how i if in is it its
me my of on or so tell than that the their them then there these they this those to was what when
where which who why will with would you your""".split())


def _content_words(text: str) -> int:
    return sum(1 for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP)


def _topic_turn(history: list[dict]) -> dict | None:
    """The turn that set the current topic: the last turn, except that refusals which were
    only carried over from an earlier question ("and its prerequisites?" after "Maths
    credits?") are skipped back to the question that actually named the subject."""
    for turn in reversed(history):
        q = turn.get("question", "")
        if other_subjects(q) and not mentions_ams_strongly(q):
            return turn
        if OUT_OF_SCOPE_MARK in turn.get("answer", ""):
            continue
        return turn
    return None


def _codes(text: str) -> list[str]:
    seen = []
    for c in COURSE_CODE.findall(text or ""):
        code = f"ARTS {c}"
        if code not in seen:
            seen.append(code)
    return seen


def strip_subjects(text: str) -> str:
    for pattern in OTHER_SUBJECTS.values():
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    text = _CS_UPPER.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


_NUMBER = re.compile(r"(?<![\w.])\d[\d,.]*\d|(?<![\w.])\d(?![\w])")
_PAGE_REF = re.compile(r"\((?:p\.|pages?)\s?[\d,\s&and.p]+\)", re.IGNORECASE)


def ungrounded_numbers(answer: str, sources: list[dict], question: str = "") -> list[str]:
    """
    Numbers in the answer that appear in none of the retrieved passages. A small model
    sometimes invents figures ("a total of 120 credits") even with the right context;
    those are the most harmful hallucinations in a handbook bot, so they are flagged.
    Page citations "(p. 9)" are ignored.
    """
    context = " ".join(s.get("content", "") for s in sources) + " " + question
    context_numbers = {n.replace(",", "") for n in _NUMBER.findall(context)}
    found = []
    for n in _NUMBER.findall(_PAGE_REF.sub(" ", answer)):
        key = n.rstrip(".").replace(",", "")
        if key and key not in context_numbers and n not in found:
            found.append(n.rstrip("."))
    return found


def history_for_prompt(history: list[dict] | None, turns: int, max_chars: int = 600) -> list[dict]:
    """Recent real answers only (refusals would teach the model to refuse), trimmed."""
    kept = [t for t in (history or []) if t.get("question") and not is_refusal(t.get("answer", ""))]
    return [{"question": t["question"], "answer": t["answer"][:max_chars]} for t in kept[-turns:]] if turns > 0 else []
