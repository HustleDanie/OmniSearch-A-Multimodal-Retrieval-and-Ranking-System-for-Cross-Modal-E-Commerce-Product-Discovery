"""
Ranking module for re-scoring and re-ranking search results.

Scoring factors:
- Vector similarity (0-1)
- Exact color match (boost)
- Exact category match (boost)
- Text similarity between query text and product title (0-1)

Final weighted score:
    final_score = 0.5*vector + 0.2*color + 0.2*category + 0.1*text

This module is dependency-free and uses a simple bag-of-words cosine
similarity for the text similarity component.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Union
import re
import math
import numpy as np


def _tokenize(text: str) -> List[str]:
    """Tokenize text to lowercase alphanumeric tokens."""
    if not text:
        return []
    return re.findall(r"[a-z0-9]+", text.lower())


def _bow(text: str) -> Dict[str, int]:
    """Create a bag-of-words frequency dict from text."""
    tokens = _tokenize(text)
    freq: Dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    return freq


def _cosine_sim(freq_a: Dict[str, int], freq_b: Dict[str, int]) -> float:
    """Cosine similarity between two frequency dicts (0..1)."""
    if not freq_a or not freq_b:
        return 0.0
    # Dot product
    dot = 0
    for k, va in freq_a.items():
        vb = freq_b.get(k)
        if vb:
            dot += va * vb
    # Norms
    na = math.sqrt(sum(v * v for v in freq_a.values()))
    nb = math.sqrt(sum(v * v for v in freq_b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return float(dot / (na * nb))


def text_similarity(query_text: Optional[str], title: Optional[str]) -> float:
    """Compute text similarity (0..1) between query text and product title."""
    if not query_text or not title:
        return 0.0
    return _cosine_sim(_bow(query_text), _bow(title))


def exact_match_boost(a: Optional[str], b: Optional[str]) -> float:
    """Return 1.0 if a and b match exactly (case-insensitive), else 0.0."""
    if not a or not b:
        return 0.0
    return 1.0 if str(a).strip().lower() == str(b).strip().lower() else 0.0


def compute_final_score(
    vector_sim: Optional[float] = None,
    color_match: float = 0.0,
    category_match: float = 0.0,
    text_sim: float = 0.0,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Compute weighted score.

    Defaults: 0.5*vector + 0.2*color + 0.2*category + 0.1*text
    """
    w = {
        "vector": 0.5,
        "color": 0.2,
        "category": 0.2,
        "text": 0.1,
    }
    if weights:
        w.update(weights)

    v = float(vector_sim) if vector_sim is not None else 0.0

    score = (
        w["vector"] * v
        + w["color"] * float(color_match)
        + w["category"] * float(category_match)
        + w["text"] * float(text_sim)
    )
    # Clamp to [0,1] for safety
    return max(0.0, min(1.0, score))


def _result_to_dict(result: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """
    Convert "SearchResult"-like object or dict into a dict with expected keys.
    Expected keys in the dict: product_id, title, description, color, category,
    image_path, similarity (vector sim), distance.
    """
    if isinstance(result, dict):
        return result
    # Fallback for objects like services.search_service.SearchResult
    return {
        "product_id": getattr(result, "product_id", None),
        "title": getattr(result, "title", None),
        "description": getattr(result, "description", None),
        "color": getattr(result, "color", None),
        "category": getattr(result, "category", None),
        "image_path": getattr(result, "image_path", None),
        "similarity": getattr(result, "similarity", None),
        "distance": getattr(result, "distance", None),
    }


def rerank_results(
    results: List[Union[Dict[str, Any], Any]],
    query_text: Optional[str] = None,
    query_color: Optional[str] = None,
    query_category: Optional[str] = None,
    weights: Optional[Dict[str, float]] = None,
    add_score_field: bool = True,
    add_debug_scores: bool = False,
) -> List[Dict[str, Any]]:
    """
    Re-rank results using the weighted scoring formula.

    Args:
        results: List of SearchResult objects or dicts with required fields.
        query_text: Optional text query (for text-title similarity)
        query_color: Optional color to boost exact match
        query_category: Optional category to boost exact match
        weights: Optional override for default weights
        add_score_field: If True, add 'final_score' to each result dict
        add_debug_scores: If True, add individual score components (vector_score, color_score, etc.)

    Returns:
        List of result dicts sorted by 'final_score' desc (or by computed score if not added).
    """
    scored: List[Tuple[float, Dict[str, Any]]] = []

    for res in results:
        rd = _result_to_dict(res)

        vector_sim = rd.get("similarity")
        color_match = exact_match_boost(query_color, rd.get("color"))
        category_match = exact_match_boost(query_category, rd.get("category"))
        text_sim = text_similarity(query_text, rd.get("title"))

        score = compute_final_score(
            vector_sim=vector_sim,
            color_match=color_match,
            category_match=category_match,
            text_sim=text_sim,
            weights=weights,
        )

        if add_score_field:
            rd["final_score"] = score
        
        if add_debug_scores:
            rd["debug_scores"] = {
                "vector_score": float(vector_sim) if vector_sim is not None else 0.0,
                "color_score": float(color_match),
                "category_score": float(category_match),
                "text_score": float(text_sim),
                "final_score": float(score)
            }

        scored.append((score, rd))

    # Sort by score desc, stable
    scored.sort(key=lambda x: x[0], reverse=True)
    return [rd for _, rd in scored]


def cosine_similarity_embeddings(
    query_vec: Optional[np.ndarray],
    title_vec: Optional[np.ndarray],
    *,
    map_to_unit_interval: bool = True,
) -> float:
    """
    Cosine similarity between two embedding vectors.

    Args:
        query_vec: Embedding for the query text.
        title_vec: Embedding for the product title.
        map_to_unit_interval: If True, map [-1,1] -> [0,1] using (cos+1)/2.

    Returns:
        Similarity score in [0,1] if map_to_unit_interval else cosine in [-1,1].
    """
    if query_vec is None or title_vec is None:
        return 0.0

    q = np.asarray(query_vec, dtype=np.float32)
    t = np.asarray(title_vec, dtype=np.float32)

    # Handle zero vectors gracefully
    q_norm = np.linalg.norm(q)
    t_norm = np.linalg.norm(t)
    if q_norm == 0.0 or t_norm == 0.0:
        return 0.0

    # Normalize then compute cosine (dot of unit vectors)
    q_unit = q / q_norm
    t_unit = t / t_norm
    cos = float(np.dot(q_unit, t_unit))

    if map_to_unit_interval:
        # Map from [-1, 1] to [0, 1]
        return 0.5 * (cos + 1.0)
    return cos
