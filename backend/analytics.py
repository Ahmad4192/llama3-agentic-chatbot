import math
import pandas as pd


def _correctness_to_score(val: str) -> float:
    if val == "Correct":
        return 100.0
    if val == "Partial":
        return 50.0
    if val == "Incorrect":
        return 0.0
    return 0.0


def _assign_phases(total_turns: int) -> list[str]:
    """Divide session turns into Start Phase, Middle Phase, and End Phase (FR16)."""
    if total_turns <= 0:
        return []
    if total_turns == 1:
        return ["Start Phase"]
    if total_turns == 2:
        return ["Start Phase", "End Phase"]

    first_cut = math.ceil(total_turns / 3)
    second_cut = math.ceil((2 * total_turns) / 3)

    phases = []
    for idx in range(total_turns):
        if idx < first_cut:
            phases.append("Start Phase")
        elif idx < second_cut:
            phases.append("Middle Phase")
        else:
            phases.append("End Phase")
    return phases


def generate_session_analytics(session_id: str, interactions: list[dict]) -> dict:
    """Compute FR14-FR21 analytics: metrics, 6 tables, and 7 graph payloads."""
    if not interactions:
        return {
            "session_id": session_id,
            "total_turns": 0,
            "metrics": {
                "overall_correctness_pct": 0.0,
                "correct_count": 0,
                "partial_count": 0,
                "incorrect_count": 0,
                "avg_rating": 0.0,
                "avg_response_time_sec": 0.0,
            },
            "tables": {
                "topic_vs_accuracy": [],
                "reply_correctness": [],
                "phase_wise_accuracy": [],
                "response_time_summary": [],
                "rating_distribution": [],
                "length_preference": [],
            },
            "graphs": {},
        }

    rows = []
    for item in sorted(interactions, key=lambda x: x.get("turn_number", 0)):
        fb = item.get("feedback") or {}
        correctness = fb.get("correctness") or "Unrated"
        rating = fb.get("rating")
        length_type = fb.get("length_type") or "Unrated"
        score = _correctness_to_score(correctness) if correctness != "Unrated" else None

        rows.append({
            "turn_number": item.get("turn_number", 0),
            "topic_label": item.get("topic_label", "Machine Learning"),
            "response_time_sec": float(item.get("response_time_sec", 0.0)),
            "correctness": correctness,
            "accuracy_pct": score,
            "rating": float(rating) if rating is not None else None,
            "length_type": length_type,
        })

    df = pd.DataFrame(rows)
    df["phase"] = _assign_phases(len(df))

    rated_df = df[df["accuracy_pct"].notna()].copy()

    correct_count = int((df["correctness"] == "Correct").sum())
    partial_count = int((df["correctness"] == "Partial").sum())
    incorrect_count = int((df["correctness"] == "Incorrect").sum())
    total_rated = len(rated_df)

    overall_correctness_pct = (
        round((correct_count / total_rated) * 100, 2) if total_rated > 0 else 0.0
    )
    avg_rating = (
        round(float(df["rating"].dropna().mean()), 2)
        if df["rating"].dropna().shape[0] > 0
        else 0.0
    )
    avg_rt = round(float(df["response_time_sec"].mean()), 2)

    # --- 6 Tables (FR19) ---
    # 1. Topic vs Accuracy
    if not rated_df.empty:
        t_acc = (
            rated_df.groupby("topic_label", as_index=False)
            .agg(turns=("turn_number", "count"), accuracy_pct=("accuracy_pct", "mean"))
        )
        t_acc["accuracy_pct"] = t_acc["accuracy_pct"].round(2)
        topic_vs_accuracy_table = t_acc.to_dict(orient="records")
    else:
        topic_vs_accuracy_table = []

    # 2. Reply Correctness Table
    reply_correctness_table = df[
        ["turn_number", "topic_label", "correctness", "accuracy_pct", "rating"]
    ].to_dict(orient="records")

    # 3. Phase-Wise Accuracy
    phase_order = ["Start Phase", "Middle Phase", "End Phase"]
    if not rated_df.empty:
        p_acc = (
            rated_df.groupby("phase", as_index=False)
            .agg(turns=("turn_number", "count"), accuracy_pct=("accuracy_pct", "mean"))
        )
        p_acc["accuracy_pct"] = p_acc["accuracy_pct"].round(2)
        p_acc["phase"] = pd.Categorical(p_acc["phase"], categories=phase_order, ordered=True)
        p_acc = p_acc.sort_values("phase")
        phase_wise_accuracy_table = p_acc.to_dict(orient="records")
    else:
        phase_wise_accuracy_table = []

    # 4. Response Time Summary
    response_time_summary_table = [
        {
            "min_sec": round(float(df["response_time_sec"].min()), 2),
            "avg_sec": round(float(df["response_time_sec"].mean()), 2),
            "max_sec": round(float(df["response_time_sec"].max()), 2),
        }
    ]

    # 5. Rating Distribution
    rating_counts = (
        df["rating"]
        .dropna()
        .astype(int)
        .value_counts()
        .reindex([1, 2, 3, 4], fill_value=0)
    )
    rating_distribution_table = [
        {"rating": int(k), "count": int(v)} for k, v in rating_counts.items()
    ]

    # 6. Length Preference
    length_counts = (
        df[df["length_type"] != "Unrated"]["length_type"]
        .value_counts()
        .reindex(["Short", "To the Point", "Lengthy"], fill_value=0)
    )
    length_preference_table = [
        {"length_type": str(k), "count": int(v)} for k, v in length_counts.items()
    ]

    # --- 7 Graphs Payload (FR20) ---
    topic_dist_series = df["topic_label"].value_counts()
    graphs = {
        # 1. Topic distribution (pie chart)
        "topic_distribution_pie": {
            "labels": topic_dist_series.index.tolist(),
            "values": [int(x) for x in topic_dist_series.values.tolist()],
        },
        # 2. Accuracy per topic (bar chart)
        "accuracy_per_topic_bar": {
            "x": [r["topic_label"] for r in topic_vs_accuracy_table],
            "y": [r["accuracy_pct"] for r in topic_vs_accuracy_table],
        },
        # 3. Accuracy vs phase (line graph)
        "accuracy_vs_phase_line": {
            "x": [r["phase"] for r in phase_wise_accuracy_table],
            "y": [r["accuracy_pct"] for r in phase_wise_accuracy_table],
        },
        # 4. Correctness per reply (bar chart)
        "correctness_per_reply_bar": {
            "x": [f"Turn {r['turn_number']}" for r in reply_correctness_table],
            "y": [
                100 if r["correctness"] == "Correct" else 50 if r["correctness"] == "Partial" else 0
                for r in reply_correctness_table
            ],
            "labels": [r["correctness"] for r in reply_correctness_table],
        },
        # 5. Response time trend (line graph)
        "response_time_trend_line": {
            "x": [f"Turn {int(t)}" for t in df["turn_number"].tolist()],
            "y": [round(float(v), 2) for v in df["response_time_sec"].tolist()],
        },
        # 6. Rating distribution (bar chart)
        "rating_distribution_bar": {
            "x": [f"Rating {r['rating']}" for r in rating_distribution_table],
            "y": [r["count"] for r in rating_distribution_table],
        },
        # 7. Length preference (pie chart)
        "length_preference_pie": {
            "labels": [r["length_type"] for r in length_preference_table],
            "values": [r["count"] for r in length_preference_table],
        },
    }

    return {
        "session_id": session_id,
        "total_turns": int(len(df)),
        "metrics": {
            "overall_correctness_pct": overall_correctness_pct,
            "correct_count": correct_count,
            "partial_count": partial_count,
            "incorrect_count": incorrect_count,
            "avg_rating": avg_rating,
            "avg_response_time_sec": avg_rt,
        },
        "tables": {
            "topic_vs_accuracy": topic_vs_accuracy_table,
            "reply_correctness": reply_correctness_table,
            "phase_wise_accuracy": phase_wise_accuracy_table,
            "response_time_summary": response_time_summary_table,
            "rating_distribution": rating_distribution_table,
            "length_preference": length_preference_table,
        },
        "graphs": graphs,
    }