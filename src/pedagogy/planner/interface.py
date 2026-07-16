from abc import ABC, abstractmethod
from typing import Optional

from ..models.context import PedagogicalContext
from ..models.action import PedagogicalAction


class DecisionPlanner(ABC):
    @abstractmethod
    def decide(self, context: PedagogicalContext) -> PedagogicalAction:
        pass

    @abstractmethod
    def get_hypothesis(self, context: PedagogicalContext) -> Optional[str]:
        pass
