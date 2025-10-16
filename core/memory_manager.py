"""
MemoryManager: 사용자 컨텍스트/히스토리 관리 (인터페이스만)
"""
from typing import Dict, Any

def load_session(session_id: str) -> Dict[str, Any]:
    """Output: session state dict"""
    raise NotImplementedError

def save_session(session_id: str, state: Dict[str, Any]) -> bool:
    """Output: True/False"""
    raise NotImplementedError
