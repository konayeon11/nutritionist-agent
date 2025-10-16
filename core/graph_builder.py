"""
GraphBuilder: 에이전트 흐름 정의 (인터페이스만)
"""
from typing import Dict, Any

def build_graph(config: Dict[str, Any]) -> Any:
    """
    Input: {"nodes":[...], "edges":[...]} (TBD)
    Output: graph object / callable
    """
    raise NotImplementedError
