from __future__ import annotations

import re
from rapidfuzz import process, fuzz


def normalize_name(text: str) -> str:
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", (text or "")).lower()


def match_player_name(ocr_name: str, player_name_candidates: list[str], threshold: int = 60):
    """
    OCR 이름을 실제 player_id 후보들과 fuzzy matching
    """
    if not ocr_name:
        return None

    normalized_ocr = normalize_name(ocr_name)
    normalized_candidates = {candidate: normalize_name(candidate) for candidate in player_name_candidates}

    reverse_map = {normalized: original for original, normalized in normalized_candidates.items()}

    best = process.extractOne(
        normalized_ocr,
        list(reverse_map.keys()),
        scorer=fuzz.ratio,
    )

    if not best:
        return None

    best_normalized, score, _ = best
    if score < threshold:
        return None

    return reverse_map[best_normalized]