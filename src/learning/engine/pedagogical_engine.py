from ..presentation.response import TutorResponse
from ..runtime import PedagogicalRuntime
from .learning_engine import LearningEngine


class PedagogicalEngine(LearningEngine):
    def __init__(self, runtime: PedagogicalRuntime):
        self._runtime = runtime

    def process(self, user_input: str, session_id: str) -> TutorResponse:
        return self._runtime.process(user_input, session_id)

    def get_session_info(self, session_id: str) -> dict:
        return {
            "engine": "pedagogical",
            "session_id": session_id,
        }
