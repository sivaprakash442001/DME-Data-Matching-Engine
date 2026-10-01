"""
Scoring and explainability engine.
Combines algorithm metrics, assigns match categories, calculates confidence,
and generates structured explanations for user trust and debugging.
"""
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any


@dataclass
class MatchThresholds:
    strong: float = 85.0
    likely: float = 70.0
    possible: float = 40.0
    weak: float = 20.0


@dataclass
class MatchExplanation:
    original_a: str
    original_b: str
    normalized_a: str
    normalized_b: str
    matching_tokens: List[str] = field(default_factory=list)
    tokens_only_in_a: List[str] = field(default_factory=list)
    tokens_only_in_b: List[str] = field(default_factory=list)
    component_scores: Dict[str, float] = field(default_factory=dict)
    applied_weights: Dict[str, float] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchResult:
    score: float
    status: str          # "Strong Match", "Likely Match", "Possible Match", "Weak Match", "No Match"
    confidence: str      # "High", "Medium", "Low"
    matching_type: str
    explanation: MatchExplanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "status": self.status,
            "confidence": self.confidence,
            "matching_type": self.matching_type,
            "explanation": self.explanation.to_dict(),
        }


class MatchScorer:
    """
    Evaluates individual component scores, computes weighted composite score,
    and categorizes match with full explainability.
    """

    def __init__(self, thresholds: Optional[MatchThresholds] = None):
        self.thresholds = thresholds or MatchThresholds()

    def determine_status(self, score: float) -> str:
        """Categorize score into human-friendly match status."""
        if score >= self.thresholds.strong:
            return "Strong Match"
        elif score >= self.thresholds.likely:
            return "Likely Match"
        elif score >= self.thresholds.possible:
            return "Possible Match"
        elif score >= self.thresholds.weak:
            return "Weak Match"
        else:
            return "No Match"

    def determine_confidence(self, score: float, component_scores: Dict[str, float]) -> str:
        """
        Estimate confidence in the score based on score magnitude and variance between signals.
        """
        if not component_scores:
            return "High" if score >= 90 or score <= 10 else "Medium"

        values = list(component_scores.values())
        if not values:
            return "Medium"

        max_v = max(values)
        min_v = min(values)
        spread = max_v - min_v

        if score >= 88:
            return "High" if spread <= 25 else "Medium"
        elif score <= 20:
            return "High" if max_v <= 35 else "Medium"
        elif score >= 60:
            return "Medium"
        else:
            return "Low" if spread >= 40 else "Medium"

    def calculate_composite_score(
        self,
        component_scores: Dict[str, float],
        weights: Dict[str, float],
    ) -> float:
        """
        Compute weighted score: sum(score_i * weight_i) / sum(weight_i)
        """
        total_weight = 0.0
        weighted_sum = 0.0

        for key, weight in weights.items():
            if key in component_scores and weight > 0:
                weighted_sum += component_scores[key] * (weight / 100.0)
                total_weight += (weight / 100.0)

        if total_weight <= 0:
            return 0.0

        final = (weighted_sum / total_weight)
        return max(0.0, min(100.0, final))

    def build_result(
        self,
        original_a: str,
        original_b: str,
        normalized_a: str,
        normalized_b: str,
        component_scores: Dict[str, float],
        weights: Dict[str, float],
        matching_type: str,
        custom_summary: Optional[str] = None,
    ) -> MatchResult:
        """
        Produce a complete MatchResult with calculated score, category, and explanation.
        """
        score = self.calculate_composite_score(component_scores, weights)
        status = self.determine_status(score)
        confidence = self.determine_confidence(score, component_scores)

        # Token analysis
        tokens_a = set(normalized_a.split())
        tokens_b = set(normalized_b.split())
        matching_tokens = sorted(list(tokens_a.intersection(tokens_b)))
        only_a = sorted(list(tokens_a - tokens_b))
        only_b = sorted(list(tokens_b - tokens_a))

        if custom_summary:
            summary = custom_summary
        else:
            if score >= 90:
                summary = f"High similarity across components with {len(matching_tokens)} shared tokens."
            elif score >= 70:
                summary = f"Likely match with minor differences in wording or formatting."
            elif score >= 45:
                summary = f"Partial overlap detected; verify specific attributes."
            else:
                summary = f"Low similarity; strings differ significantly."

        explanation = MatchExplanation(
            original_a=original_a,
            original_b=original_b,
            normalized_a=normalized_a,
            normalized_b=normalized_b,
            matching_tokens=matching_tokens,
            tokens_only_in_a=only_a,
            tokens_only_in_b=only_b,
            component_scores={k: round(v, 1) for k, v in component_scores.items()},
            applied_weights={k: round(v, 1) for k, v in weights.items()},
            summary=summary,
        )

        return MatchResult(
            score=round(score, 1),
            status=status,
            confidence=confidence,
            matching_type=matching_type,
            explanation=explanation,
        )


default_scorer = MatchScorer()
