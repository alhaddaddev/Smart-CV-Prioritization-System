from sentence_transformers import SentenceTransformer, util
from .extractor import extract_text, extract_nlp_phrases, extract_ui_insights
import re 

def is_noise(value):
    v = value.replace(" ", "")
    if "@" in v and "." in v:
        return True
    if any(ch.isdigit() for ch in v):
        return True
    if re.search(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b", v):
        return True
    return False

_semantic_model = None
def get_semantic_model():
    global _semantic_model
    if _semantic_model is None:
        _semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _semantic_model

def score_cv(path, jd_text):
    """
    Final scoring:
    - Named entities: 30%
    - Content richness: 30%
    - JD semantic match: 40%
    """

    # Constants
    MAX_PHRASES = 160
    UI_INSIGHT_LIMIT = 20
    ENTITY_SCORE_LIMIT = 30
    NAMED_ENTITY_WEIGHT = 30
    CONTENT_RICHNESS_WEIGHT = 30
    SEMANTIC_MATCH_WEIGHT = 40

    # Extract text & NLP
    text = extract_text(path)
    phrases = extract_nlp_phrases(text, max_phrases=MAX_PHRASES)

    all_entities = extract_ui_insights(text, max_items=ENTITY_SCORE_LIMIT)
    entity_score = all_entities

    # Filter UI insights
    ui_insights = [e for e in all_entities if not is_noise(e)][:UI_INSIGHT_LIMIT]

    score = 0
    flags = []

    # --- HARD STOP ---
    if not phrases:
        flags.append("CV is empty or unreadable")
        return 0, flags, ui_insights

    word_count = len(text.split())

    # --- QUALITY FLAGS ---
    if word_count < 200:
        flags.append("CV is too short")

    if len(phrases) < 25:
        flags.append("Low information content")

    # --- NAMED ENTITY SCORE (30%) ---
    entity_count = min(len(entity_score), ENTITY_SCORE_LIMIT)
    score += (entity_count / ENTITY_SCORE_LIMIT) * NAMED_ENTITY_WEIGHT

    # --- CONTENT RICHNESS (30%) ---
    phrase_count = min(len(phrases), MAX_PHRASES)
    score += (phrase_count / MAX_PHRASES) * CONTENT_RICHNESS_WEIGHT

    # --- JD SEMANTIC MATCH (40%) ---
    sim = 0
    if jd_text.strip():
        model = get_semantic_model()
        cv_blob = " ".join(phrases)

        emb_cv = model.encode(cv_blob, convert_to_tensor=True)
        emb_jd = model.encode(jd_text, convert_to_tensor=True)

        sim = util.cos_sim(emb_cv, emb_jd).item()
        score += sim * SEMANTIC_MATCH_WEIGHT

        if sim < 0.4:
            flags.append("Weak match to job description")

    # --- OCR / FORMAT CHECK ---
    non_alpha_ratio = sum(
        1 for c in text if not c.isalnum() and not c.isspace()
    ) / max(len(text), 1)

    if non_alpha_ratio > 0.25:
        flags.append("Possible OCR or formatting issues")

    return round(min(score, 100), 2), flags, ui_insights


def process_cv(path, jd_text):
    score, flags, nlp_insights = score_cv(path, jd_text)
    return score, flags, nlp_insights
