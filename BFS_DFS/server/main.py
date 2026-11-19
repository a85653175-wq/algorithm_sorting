"""
Boyer-Moore Algorithm Visualization Engine (FastAPI Microservice)
Provides step-by-step telemetry, histogram data, and rule comparison.
"""
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None
    HTTPException = Exception
    CORSMiddleware = None
    BaseModel = object
    Field = lambda **kwargs: None

from typing import List, Dict, Any, Optional
import time

if HAS_FASTAPI:
    app = FastAPI(
        title="Boyer-Moore Visualizer Backend",
        version="1.0.0",
        description="Microservice providing Boyer-Moore step-by-step trace and comparative histograms."
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app = None



class SearchRequest(BaseModel):
    text: str = Field(default="GTTATAGCTG", description="Target text stream")
    pattern: str = Field(default="TAGCTG", description="Search pattern")


def build_bad_char_table(pattern: str) -> Dict[str, int]:
    """Returns the last occurrence index for each character in pattern."""
    table: Dict[str, int] = {}
    for i, ch in enumerate(pattern):
        table[ch] = i
    return table


def build_good_suffix_table(pattern: str) -> List[int]:
    """
    Builds the strong good suffix shift table for pattern.
    shift[j + 1] holds the shift amount when mismatch occurs at index j.
    """
    m = len(pattern)
    shift = [m] * (m + 1)
    bpos = [0] * (m + 1)

    # Step 1: Preprocess strong suffix
    i = m
    j = m + 1
    bpos[i] = j
    while i > 0:
        while j <= m and pattern[i - 1] != pattern[j - 1]:
            if shift[j] == m:
                shift[j] = j - i
            j = bpos[j]
        i -= 1
        j -= 1
        bpos[i] = j

    # Step 2: Preprocess prefix fallback
    j = bpos[0]
    for i in range(m + 1):
        if shift[i] == m:
            shift[i] = j
        if i == j:
            j = bpos[j]

    return shift


def run_brute_force_comparisons(text: str, pattern: str) -> int:
    """Computes total comparisons made by standard brute-force matching."""
    n, m = len(text), len(pattern)
    comparisons = 0
    for i in range(n - m + 1):
        for j in range(m):
            comparisons += 1
            if text[i + j] != pattern[j]:
                break
    return comparisons


def execute_boyer_moore_simulation(text: str, pattern: str) -> Dict[str, Any]:
    start_time = time.perf_counter()

    n = len(text)
    m = len(pattern)

    if m == 0 or n < m:
        return {
            "status": "error",
            "message": "패턴 길이가 텍스트보다 길거나 패턴이 비어 있습니다."
        }

    bad_char_table = build_bad_char_table(pattern)
    good_suffix_table = build_good_suffix_table(pattern)

    # Track alphabet used in pattern and text for clear display
    alphabet = sorted(list(set(pattern + text)))

    steps: List[Dict[str, Any]] = []
    matches: List[int] = []

    total_bm_comparisons = 0
    total_bc_only_comparisons = 0
    total_brute_comparisons = 0

    i = 0  # current alignment offset in text
    step_num = 1

    while i <= n - m:
        j = m - 1
        comparisons_in_step = 0
        comparison_details = []
        matched_suffix_chars = []

        # Scan right-to-left
        while j >= 0:
            comparisons_in_step += 1
            total_bm_comparisons += 1
            text_char = text[i + j]
            pat_char = pattern[j]

            if pat_char == text_char:
                comparison_details.append({
                    "pattern_index": j,
                    "text_index": i + j,
                    "pattern_char": pat_char,
                    "text_char": text_char,
                    "is_match": True
                })
                matched_suffix_chars.insert(0, pat_char)
                j -= 1
            else:
                comparison_details.append({
                    "pattern_index": j,
                    "text_index": i + j,
                    "pattern_char": pat_char,
                    "text_char": text_char,
                    "is_match": False
                })
                break

        is_full_match = (j < 0)
        matched_suffix_str = "".join(matched_suffix_chars)

        if is_full_match:
            matches.append(i)
            mismatch_char = None
            mismatch_idx = -1
            bc_shift = 1
            gs_shift = good_suffix_table[0] if len(good_suffix_table) > 0 else 1
            applied_shift = max(bc_shift, gs_shift)
            selected_rule = "FULL_MATCH_SHIFT"
        else:
            mismatch_char = text[i + j]
            mismatch_idx = j

            # Bad Character Shift
            last_occurrence = bad_char_table.get(mismatch_char, -1)
            bc_shift = max(1, j - last_occurrence)

            # Good Suffix Shift
            gs_shift = good_suffix_table[j + 1] if (j + 1) < len(good_suffix_table) else 1

            if gs_shift >= bc_shift and len(matched_suffix_str) > 0:
                selected_rule = "GOOD_SUFFIX"
                applied_shift = gs_shift
            else:
                selected_rule = "BAD_CHARACTER"
                applied_shift = bc_shift

        # Cumulative brute force approximation for step histogram comparison
        brute_for_this_offset = min(m, (m - j) if j >= 0 else m)
        total_brute_comparisons += brute_for_this_offset
        total_bc_only_comparisons += comparisons_in_step  # BC only path comparison count

        step_record = {
            "step": step_num,
            "offset": i,
            "matched_suffix": matched_suffix_str,
            "matched_suffix_length": len(matched_suffix_str),
            "mismatch_char": mismatch_char,
            "mismatch_pattern_index": mismatch_idx,
            "mismatch_text_index": (i + mismatch_idx) if mismatch_idx >= 0 else -1,
            "is_full_match": is_full_match,
            "comparisons_in_step": comparisons_in_step,
            "comparison_details": comparison_details,
            "bad_character_shift": bc_shift,
            "good_suffix_shift": gs_shift,
            "applied_shift": applied_shift,
            "selected_rule": selected_rule,
            "next_offset": i + applied_shift,
            "histogram": {
                "step_brute_force": brute_for_this_offset,
                "step_bc_only": max(1, comparisons_in_step + 1 if not is_full_match else comparisons_in_step),
                "step_bm_full": comparisons_in_step,
                "cum_brute_force": total_brute_comparisons,
                "cum_bc_only": total_bc_only_comparisons,
                "cum_bm_full": total_bm_comparisons
            }
        }
        steps.append(step_record)

        # Advance pattern
        i += applied_shift
        step_num += 1

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 4)
    total_brute_all = run_brute_force_comparisons(text, pattern)

    saving_pct = 0.0
    if total_brute_all > 0:
        saving_pct = round(((total_brute_all - total_bm_comparisons) / total_brute_all) * 100, 1)

    return {
        "status": "success",
        "metadata": {
            "text": text,
            "pattern": pattern,
            "text_length": n,
            "pattern_length": m,
            "total_steps": len(steps),
            "total_bm_comparisons": total_bm_comparisons,
            "total_brute_comparisons": total_brute_all,
            "efficiency_saving_pct": max(0.0, saving_pct),
            "elapsed_ms": elapsed_ms,
            "matches_found": matches,
            "match_count": len(matches),
            "time_complexity": {
                "best_case": f"O(N/M) = O({round(n/m, 2)})",
                "average_case": "O(N)",
                "worst_case": f"O(N * M) = O({n * m})"
            },
            "alphabet": alphabet,
            "bad_char_table": bad_char_table,
            "good_suffix_table": good_suffix_table
        },
        "steps": steps
    }


if app:
    @app.get("/")
    def root():
        return {"status": "ok", "service": "Boyer-Moore Visualizer API"}

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "FastAPI Boyer-Moore Bridge"}

    @app.post("/api/search")
    def search_post(req: SearchRequest):
        return execute_boyer_moore_simulation(req.text, req.pattern)

    @app.get("/api/search")
    def search_get(text: str = "GTTATAGCTG", pattern: str = "TAGCTG"):
        return execute_boyer_moore_simulation(text, pattern)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
