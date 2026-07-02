"""
Pipeline principal: orquestra tutor -> validador -> revisao -> fallback.
Integra RAG e Memoria para contexto completo.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any

from config.settings import ModelConfig, PipelineConfig
from src.core.tutor import call_tutor, call_tutor_with_feedback
from src.core.validator import call_validator
from src.rag.simple_rag import SimpleRAG
from src.memory.history import Memory


@dataclass
class PipelineResult:
    student_input: str
    tutor_response: str
    validator_verdict: Dict[str, Any]
    final_response: str
    iterations: int
    total_time_s: float
    trail: List[Dict] = field(default_factory=list)
    rag_used: bool = False
    fallback_used: bool = False


def run_pipeline(
    student_input: str,
    memory: Optional[Memory] = None,
    rag: Optional[SimpleRAG] = None,
    scaffolding_level: Optional[str] = None,
    on_fallback: Optional[Callable[[str, List[str]], str]] = None,
    max_revisions: Optional[int] = None,
    subject: Optional[str] = None,
    verbose: bool = True,
) -> PipelineResult:
    """
    Orquestra: tutor -> validador -> revise loop -> decisao final.

    Args:
        student_input: Pergunta do aluno
        memory: Memoria do aluno (para historico)
        rag: Instancia do RAG para recuperar exemplos
        scaffolding_level: Nivel de dificuldade (1, 2, 3)
        on_fallback: Callable para fallback (ex: Qwen3-8B)
        max_revisions: Numero maximo de revisoes (sobrescreve config)
        subject: Materia selecionada (ex: Matematica, Fisica) - injeta contexto no tutor
        verbose: Log de cada iteracao

    Returns:
        PipelineResult com resposta final e metadados
    """
    model_config = ModelConfig()
    pipeline_config = PipelineConfig()

    if scaffolding_level is None:
        scaffolding_level = pipeline_config.default_scaffolding

    if max_revisions is None:
        max_revisions = pipeline_config.max_revisions

    start = time.time()
    trail = []

    # -- 1. Contexto do Aluno (Memoria) -----------------------
    student_context = ""
    if memory:
        student_context = memory.get_context(last_n=pipeline_config.history_size)
        if verbose and memory.history:
            print(f"  Historico: {len(memory.history)} interacoes")

    # -- 2. Recuperacao RAG -----------------------------------
    rag_context = "(sem material especifico recuperado)"
    rag_used = False
    if rag:
        matched = rag.retrieve(student_input, top_k=1)
        if matched:
            doc = matched[0]
            rag_context = (
                f"Topico: {doc.get('assunto', '')}\n"
                f"Exemplo: {doc.get('enunciado', '')}\n"
                f"Resolucao: {doc.get('resolucao', '')}"
            )
            rag_used = True
            if verbose:
                print(f"  RAG: {doc.get('assunto', '')}")

    # -- 3. Iteracao 1 ----------------------------------------
    draft = call_tutor(
        student_input=student_input,
        student_context=student_context,
        rag_context=rag_context,
        scaffolding_level=scaffolding_level,
        subject=subject or "",
    )

    verdict = call_validator(
        student_input=student_input,
        tutor_response=draft,
        scaffolding_level=scaffolding_level,
    )

    trail.append({"iter": 1, "draft": draft, "verdict": verdict})
    if verbose:
        print(f"  [iter 1] veredito={verdict.get('verdict')} "
              f"conf={verdict.get('confidence', 0.0):.2f} "
              f"math_ok={verdict.get('math_correct')}")

    iterations = 1

    # -- 4. Revise Loop ---------------------------------------
    while (
        verdict.get("verdict") == "revise"
        and iterations < max_revisions
        and not verdict.get("_error", False)
    ):
        iterations += 1
        draft = call_tutor_with_feedback(
            student_input=student_input,
            feedback=verdict.get("suggestions", []),
            student_context=student_context,
            rag_context=rag_context,
            scaffolding_level=scaffolding_level,
            subject=subject or "",
        )
        verdict = call_validator(
            student_input=student_input,
            tutor_response=draft,
            scaffolding_level=scaffolding_level,
        )
        trail.append({"iter": iterations, "draft": draft, "verdict": verdict})
        if verbose:
            print(f"  [iter {iterations}] veredito={verdict.get('verdict')} "
                  f"conf={verdict.get('confidence', 0.0):.2f} "
                  f"math_ok={verdict.get('math_correct')}")

    # -- 5. Decisao Final -------------------------------------
    final_verdict = verdict.get("verdict")
    fallback_used = False

    if verdict.get("_error", False):
        final_verdict = "reject"

    if final_verdict == "approve":
        final_response = draft
    elif on_fallback and final_verdict == "reject":
        final_response = on_fallback(student_input, verdict.get("issues", []))
        fallback_used = True
        if verbose:
            print(f"  Fallback ativado")
    else:
        final_response = (
            f"{draft}\n\n"
            f"---\n_Nota: confianca do validador = "
            f"{verdict.get('confidence', 0.0):.2f}. "
            f"Confirme com seu material didatico._"
        )

    # -- 6. Atualiza Memoria -----------------------------------
    if memory:
        topic = None
        if rag_used and matched:
            topic = matched[0].get("assunto", "")
        memory.add_interaction(
            user=student_input,
            assistant=final_response,
            topic=topic,
            scaffolding=scaffolding_level,
        )

    return PipelineResult(
        student_input=student_input,
        tutor_response=draft,
        validator_verdict=verdict,
        final_response=final_response,
        iterations=iterations,
        total_time_s=time.time() - start,
        trail=trail,
        rag_used=rag_used,
        fallback_used=fallback_used,
    )
