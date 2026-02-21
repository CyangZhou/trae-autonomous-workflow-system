"""
Closed Loop Models
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

class LoopState(Enum):
    INITIALIZED = "initialized"
    DECOMPOSING = "decomposing"
    EXECUTING = "executing"
    INTEGRATING = "integrating"
    VALIDATING = "validating"
    RESEARCHING = "researching"
    FIXING = "fixing"
    COMPLETED = "completed"
    FAILED = "failed"
    LOOPING = "looping"


class LoopPhase(Enum):
    DECOMPOSE = "decompose"
    EXECUTE = "execute"
    INTEGRATE = "integrate"
    VALIDATE = "validate"
    RESEARCH = "research"
    FIX = "fix"
    DELIVER = "deliver"


@dataclass
class LoopContext:
    session_id: str
    main_task: str
    state: LoopState
    current_phase: LoopPhase
    iteration: int
    max_iterations: int
    task_document: Optional[Dict] = None
    execution_results: Dict[str, Any] = field(default_factory=dict)
    integration_result: Optional[Dict] = None
    validation_result: Optional[Dict] = None
    research_findings: List[Dict] = field(default_factory=list)
    issues_found: List[Dict] = field(default_factory=list)
    fixes_applied: List[Dict] = field(default_factory=list)
    history: List[Dict] = field(default_factory=list)


@dataclass
class LoopResult:
    session_id: str
    success: bool
    iterations: int
    final_state: LoopState
    delivery_artifacts: Dict[str, Any]
    issues_resolved: int
    issues_remaining: int
    summary: str
    timestamp: str
