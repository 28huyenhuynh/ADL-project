"""
A fake pipeline for working on the interface without Ollama (MOCK=1 python app.py).
It retrieves nothing real; it only imitates the shape and speed of real answers.
"""

import time


class MockPipeline:
    llm_model = "mock"

    def retrieve(self, question, history=None):
        return [
            {"source": "AMS_MajorHandbook.pdf", "page": 9, "score": 0.74,
             "content": "Major Requirements (48 credits): ARTS 101 Introduction to Visual Studies (4 credits). Three Foundational (100-level) courses (12 credits), two of which must be chosen from ARTS 102, ARTS 103, ARTS 105. Intermediate (200-level) courses (12 credits). Advanced (300-level) courses (12 credits)"},
            {"source": "AMS_MajorHandbook.pdf", "page": 11, "score": 0.57,
             "content": "ARTS 401/402: Capstone Project. Eligibility criteria for enrollment in ARTS 401: Capstone I include a minimum major GPA of 3.6, completion of all 100-level requirements, and approval of a successful application"},
        ]

    def prepare(self, question, history=None):
        from . import scope
        plan = scope.resolve(question, history)
        if plan["action"] == "refuse":
            return {"sources": [], "query": question, "refusal": plan["message"],
                    "reason": "other_subject" if plan["subjects"] else "greeting"}
        return {"sources": self.retrieve(question), "query": plan["query"], "refusal": None, "reason": "answer"}

    def stream(self, question, plan, history=None):
        if plan.get("refusal"):
            yield plan["refusal"]
            return
        answer = ("The Art and Media Studies major requires **48 credits** (p. 9):\n"
                  "- ARTS 101 Introduction to Visual Studies\n"
                  "- three Foundational courses, two of them from ARTS 102, 103 or 105\n"
                  "- 12 credits of Intermediate and 12 credits of Advanced courses\n"
                  "- Capstone I and II, or two more Art and Media Studies courses")
        for word in answer.split(" "):
            time.sleep(0.03)
            yield word + " "
