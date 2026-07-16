from abc import ABC, abstractmethod

from ..presentation.response import TutorResponse


class LearningEngine(ABC):
    @abstractmethod
    def process(self, user_input: str, session_id: str) -> TutorResponse:
        pass

    @abstractmethod
    def get_session_info(self, session_id: str) -> dict:
        pass
