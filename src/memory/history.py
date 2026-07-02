"""
Sistema de memória leve para o EDUcador.
Mantém histórico de interações e formata contexto para o tutor.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Interaction:
    """Uma única interação aluno <-> tutor."""
    user: str
    assistant: str
    timestamp: datetime = field(default_factory=datetime.now)
    topic: Optional[str] = None
    scaffolding_used: Optional[str] = None


class Memory:
    """
    Memória do aluno com histórico de interações.

    Características:
    - Mantém até `max_size` interações
    - Formata contexto para o tutor
    - Pode ser serializada/deserializada para persistência
    """

    def __init__(self, max_size: int = 10):
        """
        Args:
            max_size: Número máximo de interações a manter.
        """
        self.max_size = max_size
        self.history: List[Interaction] = []
        self.current_topic: Optional[str] = None

    def add_interaction(
        self,
        user: str,
        assistant: str,
        topic: Optional[str] = None,
        scaffolding: Optional[str] = None
    ) -> None:
        """Adiciona uma interação ao histórico."""
        interaction = Interaction(
            user=user,
            assistant=assistant,
            topic=topic or self.current_topic,
            scaffolding_used=scaffolding,
        )
        self.history.append(interaction)

        if topic:
            self.current_topic = topic

        if len(self.history) > self.max_size:
            self.history = self.history[-self.max_size:]

    def get_context(self, last_n: int = 3) -> str:
        """
        Retorna as últimas `last_n` interações formatadas como contexto.

        Args:
            last_n: Número de interações a incluir (padrão 3)

        Returns:
            String formatada para o prompt do tutor.
        """
        if not self.history:
            return "(primeira interação — sem histórico)"

        interactions = self.history[-last_n:]
        lines = []
        for i, inter in enumerate(interactions, 1):
            user_msg = inter.user[:300] + "..." if len(inter.user) > 300 else inter.user
            assistant_msg = inter.assistant[:300] + "..." if len(inter.assistant) > 300 else inter.assistant

            lines.append(f"[Interação {i}]")
            lines.append(f"Aluno: {user_msg}")
            lines.append(f"EDUcador: {assistant_msg}")
            if inter.topic:
                lines.append(f"Tópico: {inter.topic}")
            lines.append("")

        return "\n".join(lines).strip()

    def get_last_interaction(self) -> Optional[Interaction]:
        """Retorna a última interação, se houver."""
        return self.history[-1] if self.history else None

    def get_summary(self) -> Dict:
        """Retorna um resumo do histórico para diagnóstico."""
        return {
            "total_interactions": len(self.history),
            "current_topic": self.current_topic,
            "last_user": self.history[-1].user if self.history else None,
            "last_timestamp": self.history[-1].timestamp if self.history else None,
        }

    def clear(self) -> None:
        """Limpa todo o histórico."""
        self.history = []
        self.current_topic = None

    def to_dict(self) -> List[Dict]:
        """Serializa o histórico para JSON."""
        return [
            {
                "user": inter.user,
                "assistant": inter.assistant,
                "timestamp": inter.timestamp.isoformat(),
                "topic": inter.topic,
                "scaffolding_used": inter.scaffolding_used,
            }
            for inter in self.history
        ]

    @classmethod
    def from_dict(cls, data: List[Dict], max_size: int = 10) -> 'Memory':
        """Deserializa o histórico de JSON."""
        memory = cls(max_size=max_size)
        for item in data:
            interaction = Interaction(
                user=item["user"],
                assistant=item["assistant"],
                timestamp=datetime.fromisoformat(item["timestamp"]),
                topic=item.get("topic"),
                scaffolding_used=item.get("scaffolding_used"),
            )
            memory.history.append(interaction)
            if interaction.topic:
                memory.current_topic = interaction.topic
        return memory

    def get_recent_topics(self, n: int = 5) -> List[str]:
        """Retorna os tópicos mais recentes (únicos)."""
        topics = []
        for inter in reversed(self.history):
            if inter.topic and inter.topic not in topics:
                topics.append(inter.topic)
                if len(topics) >= n:
                    break
        return topics
