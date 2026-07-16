from typing import Optional

from ..executor.strategy_executor import ExecutionResult
from ..presentation.response import TutorResponse


class LLMTutor:
    def __init__(self, ollama_client: Optional[object] = None):
        self._ollama_client = ollama_client

    def generate(
        self, execution_result: ExecutionResult, session_id: str = ""
    ) -> TutorResponse:
        if execution_result.type == "probe":
            return TutorResponse(
                session_id=session_id,
                message=execution_result.prompt or "Vamos testar seus conhecimentos.",
                action_type="probe",
                probe_id=execution_result.probe_id,
                metadata=(
                    {"target_competency": execution_result.target_competency}
                    if execution_result.target_competency
                    else None
                ),
            )

        if execution_result.type == "advance":
            return TutorResponse(
                session_id=session_id,
                message=execution_result.message or "Otim! Vamos para o proximo conceito.",
                action_type="advance",
                metadata=(
                    {"target_competency": execution_result.target_competency}
                    if execution_result.target_competency
                    else None
                ),
            )

        if execution_result.type == "instruction" and execution_result.instruction:
            content = execution_result.instruction.content
            if self._ollama_client:
                content = self._ollama_client.generate(content)
            return TutorResponse(
                session_id=session_id,
                message=content,
                action_type=execution_result.instruction.role,
                metadata=(
                    {"target_competency": execution_result.target_competency}
                    if execution_result.target_competency
                    else None
                ),
            )

        return TutorResponse(
            session_id=session_id,
            message="Vamos continuar praticando.",
            action_type="general",
        )
