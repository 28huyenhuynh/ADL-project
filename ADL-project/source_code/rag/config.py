"""
All RAG settings in one place.

Every value can be overridden with an environment variable of the same name,
which is how Docker (docker-compose.yml) configures the app without editing code.
Example: LLM_MODEL=qwen2.5:3b python app.py
"""

import os


def _env(name, default, cast=str):
    value = os.getenv(name)
    return default if value is None or value == "" else cast(value)


# Where the documents live. Every *.txt and *.pdf file in this folder is indexed.
DATA_DIR = _env("DATA_DIR", "data/handbook")
# Where Chroma saves its vectors. Kept outside DATA_DIR so documents stay clean.
VECTOR_STORE = _env("VECTOR_STORE", "vector_store/handbook")
COLLECTION = _env("COLLECTION", "rag_documents")

# Chunking
CHUNK_SIZE = _env("CHUNK_SIZE", 800, int)
CHUNK_OVERLAP = _env("CHUNK_OVERLAP", 150, int)

# Models served by Ollama
EMBED_MODEL = _env("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL = _env("LLM_MODEL", "qwen2.5:1.5b")
TEMPERATURE = _env("TEMPERATURE", 0.1, float)
OLLAMA_URL = _env("OLLAMA_URL", "http://127.0.0.1:11434")

# Retrieval
TOP_K = _env("TOP_K", 5, int)
# Cosine similarity (0..1). Below this the chunk is considered irrelevant.
SCORE_THRESHOLD = _env("SCORE_THRESHOLD", 0.35, float)
# If even the best chunk is below this, the question is not about the handbook at all
# ("what is the weather today?") and the bot says it is outside its scope.
SCOPE_THRESHOLD = _env("SCOPE_THRESHOLD", 0.60, float)
# Between SCOPE_THRESHOLD and this value the LLM is asked whether the question is about the handbook.
SCOPE_CONFIRM = _env("SCOPE_CONFIRM", 0.68, float)

# How many previous question/answer pairs are given to the model as conversation memory.
HISTORY_TURNS = _env("HISTORY_TURNS", 2, int)

# Name shown in the web interface.
APP_TITLE = _env("APP_TITLE", "Art & Media Studies Handbook")
# Credit for the tarot card images in static/tarot/ (required by CC BY 4.0).
TAROT_ARTIST = _env("TAROT_ARTIST", "Pamela Colman Smith (Rider-Waite-Smith deck, 1909, public domain)")
TAROT_TITLE = _env("TAROT_TITLE", "78 Tarot Cards")
TAROT_AUTHOR = _env("TAROT_AUTHOR", "")   # fill in the creator's name from the Figma Community page
TAROT_SOURCE = _env("TAROT_SOURCE", "https://www.figma.com/community/file/1276447799586098149/78-tarot-cards")
TAROT_LICENSE = _env("TAROT_LICENSE", "CC BY 4.0")
TAROT_LICENSE_URL = _env("TAROT_LICENSE_URL", "https://creativecommons.org/licenses/by/4.0/")

# How the prompt describes the documents to the model.
DOC_DESCRIPTION = _env(
    "DOC_DESCRIPTION",
    "the Fulbright University Vietnam B.A. Art and Media Studies (AMS) Major Handbook",
)
