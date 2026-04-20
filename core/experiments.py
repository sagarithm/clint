from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

import aiosqlite


async def create_experiment(
    db: aiosqlite.Connection,
    *,
    name: str,
    hypothesis: str,
    segment: str,
    metric_key: str,
    variant_a: str,
    variant_b: str,
) -> int:
    cur = await db.execute(
        """
        INSERT INTO experiments (
            name,
            hypothesis,
            segment,
            metric_key,
            status,
            variant_a,
            variant_b
        )
        VALUES (?, ?, ?, ?, 'planned', ?, ?)
        """,
        (name, hypothesis, segment, metric_key, variant_a, variant_b),
    )
    return int(cur.lastrowid)


async def start_experiment(db: aiosqlite.Connection, *, experiment_id: int) -> None:
    await db.execute(
        """
        UPDATE experiments
        SET status = 'running', start_at_utc = datetime('now'), updated_at_utc = datetime('now')
        WHERE id = ?
        """,
        (experiment_id,),
    )


async def record_observation(
    db: aiosqlite.Connection,
    *,
    experiment_id: int,
    variant: str,
    sample_size: int,
    metric_value: float,
    quality_impact: float,
) -> None:
    await db.execute(
        """
        INSERT INTO experiment_observations (
            experiment_id,
            variant,
            sample_size,
            metric_value,
            quality_impact
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (experiment_id, variant, sample_size, metric_value, quality_impact),
    )


async def complete_experiment(
    db: aiosqlite.Connection,
    *,
    experiment_id: int,
    winner_variant: str,
    decision_note: str,
) -> None:
    await db.execute(
        """
        UPDATE experiments
        SET status = 'completed',
            winner_variant = ?,
            decision_note = ?,
            end_at_utc = datetime('now'),
            updated_at_utc = datetime('now')
        WHERE id = ?
        """,
        (winner_variant, decision_note, experiment_id),
    )


async def list_experiments(db: aiosqlite.Connection, *, status: Optional[str] = None) -> List[Dict[str, Any]]:
    query = "SELECT * FROM experiments"
    params: list[Any] = []
    if status:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY created_at_utc DESC"

    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def decide_experiment(
    db: aiosqlite.Connection,
    *,
    experiment_id: int,
    min_sample_per_variant: int = 30,
    min_uplift_pct: float = 5.0,
    max_negative_quality_impact: float = -5.0,
) -> Dict[str, Any]:
    async with db.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)) as cursor:
        exp_row = await cursor.fetchone()
    if exp_row is None:
        raise ValueError(f"Experiment not found: {experiment_id}")

    experiment = dict(exp_row)
    variant_a = str(experiment.get("variant_a") or "A")
    variant_b = str(experiment.get("variant_b") or "B")

    async with db.execute(
        """
        SELECT variant, sample_size, metric_value, quality_impact
        FROM experiment_observations
        WHERE experiment_id = ?
        """,
        (experiment_id,),
    ) as cursor:
        rows = await cursor.fetchall()

    if not rows:
        return {
            "experiment_id": experiment_id,
            "decision": "insufficient_data",
            "reason": "no_observations",
        }

    bucket = defaultdict(lambda: {"sample": 0, "weighted_metric": 0.0, "quality_sum": 0.0, "count": 0})
    for row in rows:
        v = str(row[0])
        sample = int(row[1] or 0)
        metric = float(row[2] or 0.0)
        qimpact = float(row[3] or 0.0)
        bucket[v]["sample"] += sample
        bucket[v]["weighted_metric"] += metric * max(sample, 1)
        bucket[v]["quality_sum"] += qimpact
        bucket[v]["count"] += 1

    def summarize(v: str) -> Dict[str, float]:
        data = bucket[v]
        sample = int(data["sample"])
        avg_metric = (data["weighted_metric"] / sample) if sample > 0 else 0.0
        avg_quality = (data["quality_sum"] / data["count"]) if data["count"] > 0 else 0.0
        return {
            "sample": sample,
            "avg_metric": avg_metric,
            "avg_quality": avg_quality,
        }

    stats_a = summarize(variant_a)
    stats_b = summarize(variant_b)

    if stats_a["sample"] < min_sample_per_variant or stats_b["sample"] < min_sample_per_variant:
        return {
            "experiment_id": experiment_id,
            "decision": "insufficient_data",
            "reason": "min_sample_not_met",
            "variant_a": stats_a,
            "variant_b": stats_b,
        }

    if stats_a["avg_quality"] < max_negative_quality_impact and stats_b["avg_quality"] < max_negative_quality_impact:
        decision_note = "Both variants regress quality beyond threshold"
        await complete_experiment(
            db,
            experiment_id=experiment_id,
            winner_variant="none",
            decision_note=decision_note,
        )
        return {
            "experiment_id": experiment_id,
            "decision": "rollback",
            "winner": "none",
            "reason": "quality_regression",
            "variant_a": stats_a,
            "variant_b": stats_b,
        }

    baseline = stats_a["avg_metric"] if stats_a["avg_metric"] > 0 else 1e-6
    uplift_b_vs_a = ((stats_b["avg_metric"] - stats_a["avg_metric"]) / baseline) * 100.0

    if uplift_b_vs_a >= min_uplift_pct and stats_b["avg_quality"] >= max_negative_quality_impact:
        winner = variant_b
    elif uplift_b_vs_a <= -min_uplift_pct and stats_a["avg_quality"] >= max_negative_quality_impact:
        winner = variant_a
    else:
        winner = "none"

    if winner == "none":
        decision_note = "No statistically meaningful winner under configured thresholds"
        await complete_experiment(
            db,
            experiment_id=experiment_id,
            winner_variant="none",
            decision_note=decision_note,
        )
        return {
            "experiment_id": experiment_id,
            "decision": "no_winner",
            "winner": "none",
            "uplift_b_vs_a": round(uplift_b_vs_a, 2),
            "variant_a": stats_a,
            "variant_b": stats_b,
        }

    decision_note = f"Winner selected by uplift rule: {winner}"
    await complete_experiment(
        db,
        experiment_id=experiment_id,
        winner_variant=winner,
        decision_note=decision_note,
    )
    return {
        "experiment_id": experiment_id,
        "decision": "promote",
        "winner": winner,
        "uplift_b_vs_a": round(uplift_b_vs_a, 2),
        "variant_a": stats_a,
        "variant_b": stats_b,
    }
