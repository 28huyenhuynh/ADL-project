# Out-of-scope evaluation

Questions answered by the **Applied Mathematics** and **Computer Science** handbooks, asked to the
**AMS** chatbot. The AMS bot cannot know these answers, so the correct behaviour is to decline.
Controls check that AMS questions (including ones that mention another subject) are still answered.

Model `qwen2.5:1.5b`, embedding `nomic-embed-text`, top-k 5, scope thresholds 0.6/0.68.

## Summary

| Mode | Other-major questions declined | Answered anyway | …of which repeat an AMS fact | Controls answered |
|---|---|---|---|---|
| guarded | 25/25 | 0 | 0 | 25/25 |

*baseline* = same index and model, without the scope guard, with the original prompt and
follow-up rule. *Repeat an AMS fact* = the answer contains the AMS figure the question is a trap
for (e.g. 48 credits or GPA 3.6), i.e. an AMS fact presented as another major's.

## Other-major questions and controls

| # | Category | Question | True answer (source) | Guarded | Baseline answer |
|---|---|---|---|---|---|
| O1 | Named major, same shape as an AMS question | How many credits are required for the Applied Mathematics major? | 56 credits of major requirements. (MATH_MajorHandbook.pdf p. 9) | ✅ declined | — |
| O2 | Named major, same shape as an AMS question | How many credits does the Computer Science major require? | 56 credits of major requirements. (CS_MajorHandbook.pdf p. 7) | ✅ declined | — |
| O3 | Named major, same shape as an AMS question | Maths require how many credits to graduate? | At least 128 credits in total (56 of them major requirements). (MATH_MajorHandbook.pdf p. 10) | ✅ declined | — |
| O4 | Named major, same shape as an AMS question | What are the requirements for a minor in Applied Mathematics? | At least 6 MATH courses, at least three at 200-level or above and at least one at 300-level. (MATH_MajorHandbook.pdf p. 10) | ✅ declined | — |
| O5 | Named major, same shape as an AMS question | What do I need to complete to declare Computer Science as my major? | At least two Computer Science courses (MATH 202 Discrete Math also counts). (CS_MajorHandbook.pdf p. 7) | ✅ declined | — |
| O6 | Named major, same shape as an AMS question | What do I need to declare the Applied Mathematics major? | Complete at least 2 MATH courses. (MATH_MajorHandbook.pdf p. 10) | ✅ declined | — |
| O7 | Named major, same shape as an AMS question | What is the minimum GPA to enroll in the Computer Science capstone? | A minimum major GPA of 3.5 and an approved application. (CS_MajorHandbook.pdf p. 9) | ✅ declined | — |
| O8 | Named major, same shape as an AMS question | What kind of project is the Applied Mathematics capstone? | An optional one-year research project in the last year of study. (MATH_MajorHandbook.pdf p. 13) | ✅ declined | — |
| O9 | Named major, same shape as an AMS question | What are the program learning outcomes of the Computer Science major? | Core and Major learning outcomes listed in the CS handbook. (CS_MajorHandbook.pdf p. 4) | ✅ declined | — |
| O10 | Named major, same shape as an AMS question | What careers can Computer Science graduates pursue? | Graduate studies and career paths section of the CS handbook. (CS_MajorHandbook.pdf p. 5) | ✅ declined | — |
| O11 | Course code only | What are the prerequisites for MATH 201? | MATH 101 Calculus (MATH 201 is Differential Equations). (MATH_MajorHandbook.pdf p. 21) | ✅ declined | — |
| O12 | Course code only | What is the prerequisite for CS201? | CS101 Introduction to Programming. (CS_MajorHandbook.pdf p. 13) | ✅ declined | — |
| O13 | Course code only | What are the prerequisites for CS302? | CS201 and MATH202. (CS_MajorHandbook.pdf p. 13) | ✅ declined | — |
| O14 | Course code only | How often is MATH 205 offered? | Once a year (MATH 205 is Probability). (MATH_MajorHandbook.pdf p. 21) | ✅ declined | — |
| O15 | Course code only | Is CS306 currently offered? | No, CS306 Computer Security is on hold. (CS_MajorHandbook.pdf p. 13) | ✅ declined | — |
| O16 | Course name only (no major named) | What are the prerequisites for Real Analysis? | MATH 101 Calculus. (MATH_MajorHandbook.pdf p. 21) | ✅ declined | — |
| O17 | Course name only (no major named) | What is the prerequisite for Data Structures & Algorithms? | CS101 Introduction to Programming. (CS_MajorHandbook.pdf p. 13) | ✅ declined | — |
| O18 | Course name only (no major named) | How often is Linear Algebra offered? | Once a year. (MATH_MajorHandbook.pdf p. 21) | ✅ declined | — |
| O19 | Course name only (no major named) | What must I take before I can enroll in Operating Systems? | CS201 Data Structures & Algorithms. (CS_MajorHandbook.pdf p. 13) | ✅ declined | — |
| O20 | Course name only (no major named) | Which course do I need before Differential Equations? | MATH 101 Calculus. (MATH_MajorHandbook.pdf p. 21) | ✅ declined | — |
| O21 | Follow-up that stays on another major | How many credits does the Computer Science major require? → And what do I need to declare it? | At least two Computer Science courses. (CS_MajorHandbook.pdf p. 7) | ✅ declined | — |
| O22 | Follow-up that stays on another major | What are the prerequisites for MATH 301? → How often is it offered? | Every other year (MATH 301 Optimization). (MATH_MajorHandbook.pdf p. 21) | ✅ declined | — |
| O23 | Switch away from AMS mid-conversation | How many credits does the AMS major require? → What about Computer Science? | 56 credits. (CS_MajorHandbook.pdf p. 7) | ✅ declined | — |
| O24 | Switch away from AMS mid-conversation | What GPA do I need for the Capstone? → Is it the same for the CS capstone? | No: CS requires a major GPA of 3.5 (AMS: 3.6). (CS_MajorHandbook.pdf p. 9) | ✅ declined | — |
| O25 | Switch away from AMS mid-conversation | What do I need to complete to declare Art and Media Studies as my major? → And for Applied Mathematics? | At least 2 MATH courses. (MATH_MajorHandbook.pdf p. 10) | ✅ declined | — |
| C1 | Control: names another subject but is about AMS | What are the prerequisites for ARTS 307 Animation and Graphic Media in East Asia? | ARTS 101 OR LIT 101, and one 200-level ARTS or LIT course. (AMS_MajorHandbook.pdf p. 30) | ✅ answered: The prerequisites for ARTS 307 Animation and Graphic Media in East Asia are: - ARTS 101 Introduction to Visual Studies … | — |
| C2 | Control: names another subject but is about AMS | Is the Art and Media Studies minor a good complement to an economics major? | Yes: the handbook names economics and management among the majors it complements. (AMS_MajorHandbook.pdf p. 9) | ✅ answered: Yes, the Art and Media Studies minor is an ideal complement to a major focusing on economics. The minor provides a foun… | — |
| C3 | Control: names another subject but is about AMS | Can I take ARTS 313 Aesthetics and Violence if I completed SOCI 102? | Prerequisites are ARTS 101, SOCI 102 and two 200-level courses in ARTS or SOCI. (AMS_MajorHandbook.pdf p. 19) | ✅ answered: Yes, you can take ARTS 313 Aesthetics and Violence if you completed SOCI 102. The prerequisite for this course is two 2… | — |
| C4 | Control: names another subject but is about AMS | Which AMS courses are cross-listed with Literature? | For example ARTS 307 (LIT; EAS). (AMS_MajorHandbook.pdf p. 19) | ✅ answered: According to the AMS course catalog, the following courses are cross-listed with Literature (LIT): - LIT 303 Film, Fict… | — |
| C5 | Control: follow-up back to AMS | Maths require how many credits to graduate? → What about AMS then? | 48 credits of major requirements (plus 40 credits of general curriculum). (AMS_MajorHandbook.pdf p. 9) | ✅ answered: To graduate from the Art and Media Studies (AMS) major, a student must complete 48 credits, including 40 credits of Gen… | — |

## AMS evaluation questions (guarded): must not be refused

| # | Question | Result | Answer |
|---|---|---|---|
| A1 | How many credits are required for the Art and Media Studies major? | ✅ answer | The Art and Media Studies major requires 48 credits. |
| A2 | Which courses are required for the Art and Media Studies major? | ✅ answer | The required courses for the Art and Media Studies major are: - Introduction to Visual Studies (ARTS 101) - Two Foundational courses (ARTS … |
| A3 | What do I need to complete to declare Art and Media Studies as my major? | ✅ answer | To formally declare Art and Media Studies as your major, you must complete Introduction to Visual Studies and two Foundational courses. (p.… |
| A4 | What are the requirements for a minor in Art and Media Studies? | ✅ answer | The minor in Art and Media Studies requires students to take a total of six courses. |
| A5 | How can I declare a minor in Art and Media Studies? | ✅ answer | To formally declare the Art and Media Studies minor, the student must complete at least one course in the Art and Media Studies program. |
| A6 | What are the eligibility criteria for the Capstone? | ✅ answer | The eligibility criteria for the Capstone in Art & Media Studies include a minimum major GPA of 3.6, completion of all 100-level requiremen… |
| A7 | What kind of project can I do for the Capstone? | ✅ answer | For the Capstone project, you can develop an ambitious artistic project, complete a short film, or write a thesis. Practice-based projects … |
| A8 | What is the prerequisite for ARTS 104 Introduction to Video and Film Production? | ✅ answer | The prerequisite for ARTS 104 Introduction to Video and Film Production is ARTS 101 Introduction to Visual Studies. |
| A9 | What are the prerequisites for ARTS 309 Advanced Narrative Film Production? | ✅ answer | The prerequisites for ARTS 309 Advanced Narrative Film Production are ARTS 101 Introduction to Visual Studies AND ARTS 104 Introduction to … |
| A10 | Which courses have a materials fee and how much is it? | ✅ answer | The courses with a materials fee are ARTS 107: 2D/3D Foundations and ARTS 308: Projects in Sculpture. The materials fee for ARTS 107 is app… |
| A11 | How often is ARTS 101 Introduction to Visual Studies offered? | ✅ answer | ARTS 101 Introduction to Visual Studies is offered every Fall and Spring. |
| A12 | What does ARTS 105 Introduction to Film History and Theory cover? | ✅ answer | ARTS 105: Introduction to Film History and Theory covers a historical and theoretical introduction to film and cinema, focusing on its capa… |
| A13 | Which courses are currently on hold? | ✅ answer | Based on the information provided in the context, the course that is currently on hold is "Movements in Post-1945 International Cinema" (AR… |
| A14 | What are the major learning outcomes of Art and Media Studies? | ✅ answer | The major learning outcomes of Art and Media Studies are formulated based on the learning outcomes of comparable programs in the region and… |
| A15 | What jobs have Art and Media Studies graduates gotten? | ✅ answer | According to the handbook, Art and Media Studies graduates have successfully gained employment in various roles such as Actor (film, televi… |
| A16 | Which student clubs can Art and Media Studies students join? | ✅ answer | Art and Media Studies students can join the following clubs: - Blue Period painting club - LIT Magazine - Theater Club - Music Club - The L… |
| A17 | What are the prerequisites for ARTS 305 Curating in Context? | ✅ answer | The prerequisites for ARTS 305 Curating in Context are ARTS 101 Introduction to Visual Studies AND two 200-level AMS courses. |
| A18 | What are the prerequisites for ARTS 307 Animation and Graphic Media in East Asia? | ✅ answer | The prerequisites for ARTS 307 Animation and Graphic Media in East Asia are: - ARTS 101 Introduction to Visual Studies OR LIT 101 Foundatio… |
| A19 | What is the major code of Art and Media Studies? | ✅ answer | The major code for Art and Media Studies is B.A. ART & MEDIA STUDIES. |
| A20 | How much is the tuition fee for the Art and Media Studies major? | ✅ not_found | I could not find this in the handbook. |
