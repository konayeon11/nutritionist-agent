"""
PlannerAgent: 일/주간 식단 계획 생성 (인터페이스만)
"""
from typing import Dict, Any, List

def build_weekly_plan(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: {"age": int, "sex": "M"|"F", "goal": "cut"|"bulk"|"maintain", ...}
    Output: {"week": [{"day": "Mon", "meals": [...]}, ...]}
    """
    raise NotImplementedError
