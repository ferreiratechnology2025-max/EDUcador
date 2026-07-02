"""
Tutor: Gera respostas usando o modelo configurado (Gemma 3 4B).
"""

from config.settings import ModelConfig
from src.utils.ollama_client import OllamaClient

TUTOR_SYSTEM_PROMPT = """Você é o EDUcador, um professor particular de matemática para alunos do ensino médio brasileiro.

Seu estilo:
- Didático e acolhedor, sem ser infantil
- Usa analogias do cotidiano brasileiro (futebol, feira, transporte, contas de casa)
- Explica passo a passo, sem pular etapas algébricas
- Quando o aluno erra, mostra onde errou com gentileza
- NUNCA dá a resposta final logo de cara — usa SCAFFOLDING:
    Nível 1 (iniciante): só uma dica sutil, sem resolver
    Nível 2 (intermediário): mostra um passo-chave e deixa o aluno completar o resto
    Nível 3 (avançado): resolução completa com explicação conceitual e conexões
- Responda SEMPRE em português brasileiro natural (não em português de Portugal, não em inglês)
- Use LaTeX entre $ pra fórmulas (ex: $x^2 + 2x$)

Importante: NÃO invente fórmulas, propriedades ou teoremas. Se não souber resolver com segurança, admita e sugira consultar o material didático.

[CONTEXTO DO ALUNO]
{student_context}

[MATERIAL DE REFERÊNCIA — use apenas o que for relevante à pergunta]
{rag_context}

[MATÉRIA SELECIONADA]
{subject}

[NÍVEL DE DIFICULDADE PEDIDO]
{scaffolding_level}
"""

def call_tutor(
    student_input: str,
    student_context: str,
    rag_context: str,
    scaffolding_level: str,
    subject: str = "",
    client: OllamaClient = None,
    config: ModelConfig = None,
) -> str:
    """Gera a resposta inicial do tutor."""
    if client is None:
        client = OllamaClient()
    if config is None:
        config = ModelConfig()

    system = TUTOR_SYSTEM_PROMPT.format(
        student_context=student_context or "(primeira interação — sem histórico)",
        rag_context=rag_context or "(sem material específico recuperado)",
        subject=subject or "(não especificada)",
        scaffolding_level=scaffolding_level,
    )

    return client.generate(
        prompt=student_input,
        system=system,
        model=config.tutor_model,
        temperature=config.tutor_temperature,
        max_tokens=config.tutor_max_tokens,
    )

def call_tutor_with_feedback(
    student_input: str,
    feedback: list[str],
    student_context: str,
    rag_context: str,
    scaffolding_level: str,
    subject: str = "",
    client: OllamaClient = None,
    config: ModelConfig = None,
) -> str:
    """Pede pro tutor reescrever aplicando o feedback do validador."""
    if client is None:
        client = OllamaClient()
    if config is None:
        config = ModelConfig()

    feedback_text = "\n".join(f"- {f}" for f in feedback) if feedback else "(nenhuma sugestão específica)"

    rewrite_prompt = f"""O validador encontrou problemas na sua resposta anterior. Reescreva aplicando as sugestões abaixo.

FEEDBACK DO VALIDADOR:
{feedback_text}

PERGUNTA ORIGINAL DO ALUNO:
{student_input}

Reescreva a resposta do zero, aplicando todas as sugestões. Mantenha o tom acolhedor e o nível de dificuldade."""

    system = TUTOR_SYSTEM_PROMPT.format(
        student_context=student_context or "(primeira interação — sem histórico)",
        rag_context=rag_context or "(sem material específico recuperado)",
        subject=subject or "(não especificada)",
        scaffolding_level=scaffolding_level,
    )

    return client.generate(
        prompt=rewrite_prompt,
        system=system,
        model=config.tutor_model,
        temperature=config.tutor_temperature,
        max_tokens=config.tutor_max_tokens,
    )
