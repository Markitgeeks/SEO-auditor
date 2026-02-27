from app.config import CATEGORY_WEIGHTS
from app.models import CategoryResult


def compute_overall_score(categories: list[CategoryResult]) -> int:
    total_weight = 0
    weighted_sum = 0
    for cat in categories:
        weight = CATEGORY_WEIGHTS.get(cat.name, 0)
        weighted_sum += cat.score * weight
        total_weight += weight
    if total_weight == 0:
        return 0
    return round(weighted_sum / total_weight)
