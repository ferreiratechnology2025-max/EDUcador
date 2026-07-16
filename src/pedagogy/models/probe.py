from dataclasses import dataclass


@dataclass
class Probe:
    id: str
    competency: str
    difficulty_level: int
    prompt_template: str
    expected_response_schema: str
    evidence_weight: int
    evaluator_type: str
    evaluator_config: dict
