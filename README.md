# EDUcador

Tutor virtual offline-first com motor pedagógico baseado em evidências para ensino médio brasileiro.

## O que é o EDUcador?

Um assistente educacional que roda localmente sem depender de internet. Usa um **motor pedagógico** que decide dinamicamente a ação certa baseada no histórico de evidências do aluno:

- **Probe**: Pergunta/sonda para avaliar conhecimento
- **Explain**: Explicação didática de um conceito
- **Advance**: Avançar para o próximo conceito
- **Recover_Base**: Revisar pré-requisito (baseado em grafo de conhecimento)
- **Exercise**: Exercício prático com correção
- **Analogy**: Analogia para facilitar compreensão
- **Example**: Exemplo prático

O motor usa modelos locais via Ollama (Gemma 3, Phi-4-mini, Qwen3-8B) e um **EventStore** que persiste todo o histórico do aluno.

## Status do Projeto

**PR-3 Validation Framework** — 57/59 checks passing

| Validador | Resultado |
|-----------|-----------|
| Architecture Validation | 5/5 ✅ |
| Contract Validation | 22/22 ✅ |
| Dependency Validation | 5/5 ✅ |
| Intervention Validation | 8/8 ✅ |
| Planner Validation | 12/12 ✅ |
| Readiness Validation | 5/7 ⚠️ (gates not green) |

```bash
python scripts/validation/run_all.py
```

## Como Usar

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Baixe os modelos
```bash
ollama pull gemma3:4b
ollama pull phi4-mini
ollama pull qwen3:8b
ollama pull llama3.2-vision  # opcional (OCR)
```

### 3. Inicie o Ollama
```bash
ollama serve
```

### 4. Rode o EDUcador
```bash
# Interface gráfica (Streamlit)
python run.py

# Modo terminal
python -m streamlit run interface.py
```

## Arquitetura

```
EDUcador/
├── src/
│   ├── pedagogy/
│   │   ├── models/              # Domínio pedagógico
│   │   │   ├── evidence.py       # Evidence, EvidenceType
│   │   │   ├── context.py        # PedagogicalContext, LearningContext
│   │   │   ├── action.py         # ActionType, PedagogicalAction
│   │   │   └── probe.py          # Probe
│   │   ├── memory/
│   │   │   └── event_store.py    # EventStore (persistência JSONL)
│   │   ├── planner/
│   │   │   ├── interface.py      # DecisionPlanner protocol
│   │   │   └── rule_based.py     # RuleBasedPlanner (6 regras)
│   │   ├── extractors/
│   │   │   └── evidence_extractor.py  # Extração de evidências
│   │   ├── probes/
│   │   │   ├── repository.py     # ProbeRepository
│   │   │   └── evaluator.py      # EvaluatorFactory
│   │   ├── composer/
│   │   │   └── instruction_composer.py  # Instruções pedagógicas
│   │   └── knowledge/
│   │       └── graph_repository.py  # Grafo de competências
│   ├── learning/
│   │   ├── domain/
│   │   │   └── decision.py       # PedagogicalDecision, ActionType
│   │   ├── engine/
│   │   │   ├── pedagogical_engine.py  # Engine principal
│   │   │   ├── current_pipeline.py    # Pipeline legado
│   │   │   ├── learning_engine.py     # Interface LearningEngine
│   │   │   └── factory.py             # Factory pattern
│   │   ├── executor/
│   │   │   └── strategy_executor.py   # StrategyExecutor
│   │   ├── tutor/
│   │   │   └── llm_tutor.py           # Tutor via LLM
│   │   ├── presentation/
│   │   │   └── response.py            # TutorResponse
│   │   ├── inspector/
│   │   │   └── engine_inspector.py    # EngineInspector (diagnóstico)
│   │   └── runtime.py             # PedagogicalRuntime (orquestrador)
│   ├── core/                      # Pipeline legado (Tutor + Validador)
│   ├── rag/                       # RAG por tags + BM25
│   └── memory/                    # Histórico serializável
├── config/
│   ├── settings.py                # Configurações centralizadas
│   ├── project_state.py           # ProjectGate (dois gates + hashes)
│   ├── competencies.yaml          # Grafo de competências
│   ├── probes.yaml                # Definição de sondas
│   ├── planner_rules.yaml         # Regras do planner
│   └── .gate_state.json           # Estado persistente dos gates
├── scripts/
│   ├── validation/                # PR-3 Validation Framework
│   │   ├── run_all.py             # Suite runner com CLI
│   │   ├── manifest.py            # Manifesto dos validadores
│   │   ├── registry.py            # Registro com descoberta automática
│   │   ├── invariants.py          # Sistema de invariantes
│   │   ├── scenarios.py           # 20 cenários (planner + intervention)
│   │   ├── contract_validator.py  # 22 checks de contrato
│   │   ├── planner_validator.py   # 12 cenários do planner
│   │   ├── intervention_validator.py  # 8 cenários de intervenção
│   │   ├── architecture_validator.py  # 5 checks de arquitetura
│   │   ├── dependency_validator.py    # 5 checks de dependências
│   │   └── readiness_validator.py     # 7 checks de readiness
│   ├── benchmark_engine.py        # Benchmark do motor
│   ├── benchmark_planner.py       # Benchmark do planner
│   ├── benchmark_pedagogy.py      # Benchmark pedagógico
│   └── download_models.py         # Download dos modelos
├── interface.py                   # Dashboard Streamlit
└── run.py                         # Entrypoint
```

### Ciclo de Decisão Pedagógica

```
Entrada do Aluno
       │
       ▼
┌────────────────┐
│  Evidence       │
│  Extractor      │  Extrai evidência da resposta
└───────┬────────┘
        │ (acerto/erro/ajuda)
        ▼
┌────────────────┐
│  EventStore    │  Persiste evidência
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  RuleBased     │  Decide próxima ação
│  Planner       │  (6 regras determinísticas)
└───────┬────────┘
        │ (probe/explain/advance/recover_base/exercise/analogy/example)
        ▼
┌────────────────┐
│  Strategy      │  Executa a ação decidida
│  Executor      │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│  LLM Tutor     │  Gera resposta formatada
└───────┬────────┘
        │
        ▼
   Resposta Final
```

### Regras do Planner

| Condição | Ação |
|----------|------|
| Sem competência ativa | PROBE |
| 3 erros consecutivos | RECOVER_BASE |
| 3 acertos consecutivos | ADVANCE |
| Help requested | EXPLAIN |
| 5+ respostas com probe_id | EXERCISE |
| Caso contrário | PROBE |

### ProjectGate

O `config/project_state.py` implementa dois gates de governança:

1. **technical_ready** — Motor deve estar tecnicamente válido
2. **hypothesis_validated** — Hipótese pedagógica deve ser validada com usuários reais

Ambos com hash SHA-256 do estado para detecção de adulteração e blocking em CI.

## Validação

```bash
# Suite completa
python scripts/validation/run_all.py

# Validadores específicos
python scripts/validation/run_all.py --select contract
python scripts/validation/run_all.py --select planner
python scripts/validation/run_all.py --select intervention

# Relatório JSON
python scripts/validation/run_all.py --json

# Exigir gates verdes
python scripts/validation/run_all.py --require-gates
```

## Benchmarks

```bash
# Benchmark do motor pedagógico
python scripts/benchmark_engine.py

# Benchmark das regras do planner
python scripts/benchmark_planner.py

# Benchmark pedagógico completo
python scripts/benchmark_pedagogy.py
```

## Modelos Necessários

```bash
ollama pull gemma3:4b       # Tutor principal
ollama pull phi4-mini       # Validador
ollama pull qwen3:8b        # Fallback
ollama pull llama3.2-vision # OCR (opcional)
```

## Requisitos

- **Mínimo:** Python 3.8+, 8 GB RAM, 10 GB disco
- **Recomendado:** 16 GB RAM, SSD
- Ollama instalado (https://ollama.com/)

## Licença

MIT
