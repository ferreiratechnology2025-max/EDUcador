from pathlib import Path
from typing import Dict

from ..presentation.response import TutorResponse
from .learning_engine import LearningEngine


class CurrentPipelineEngine(LearningEngine):
    def __init__(self):
        self._sessions: Dict[str, object] = {}
        self._rag = None
        self._init_rag()

    def _init_rag(self):
        try:
            from src.rag.simple_rag import SimpleRAG
            from config.settings import CORPUS_PATH
            if CORPUS_PATH.exists():
                self._rag = SimpleRAG(str(CORPUS_PATH))
        except Exception:
            self._rag = None

    def _get_memory(self, session_id: str):
        if session_id not in self._sessions:
            from src.memory.history import Memory
            self._sessions[session_id] = Memory(max_size=10)
        return self._sessions[session_id]

    def process(self, user_input: str, session_id: str) -> TutorResponse:
        try:
            from src.core.pipeline import run_pipeline
            from config.settings import PipelineConfig

            memory = self._get_memory(session_id)
            result = run_pipeline(
                student_input=user_input,
                memory=memory,
                rag=self._rag,
                verbose=False,
            )
            return TutorResponse(
                session_id=session_id,
                message=result.final_response,
                action_type="explanation",
                metadata={
                    "time_s": round(result.total_time_s, 1),
                    "iterations": result.iterations,
                    "rag_used": result.rag_used,
                    "fallback_used": getattr(result, "fallback_used", False),
                },
            )
        except Exception as e:
            return TutorResponse(
                session_id=session_id,
                message=f"Erro ao processar: {e}",
                action_type="error",
            )

    def get_session_info(self, session_id: str) -> dict:
        return {
            "engine": "current_pipeline",
            "session_id": session_id,
            "has_memory": session_id in self._sessions,
        }
