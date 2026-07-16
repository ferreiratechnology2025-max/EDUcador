# EDUcador — Brain Record

## Projeto
Tutor virtual offline-first com motor pedagógico baseado em evidências para ensino médio brasileiro.

## Estado Atual (Jul 2026)

### PR-3 Validation Framework — CONCLUÍDO ✅
57/59 checks passing. 2 advisory readiness warnings (gates not green, esperado).

| Validador | Resultado |
|-----------|-----------|
| Architecture | 5/5 ✅ |
| Contract | 22/22 ✅ |
| Dependency | 5/5 ✅ |
| Intervention | 8/8 ✅ |
| Planner | 12/12 ✅ |
| Readiness | 5/7 ⚠️ |

### Commits Principais
- `a612e28` — README atualizado
- `6c852ec` — Fix todos os findings do arquiteto (bug duplicate-append, 8 violações contrato, 2 violações arquitetura, stale .pyc)
- `fd5569a` — Suite runner (run_all.py)
- `90f2ef2` — 6 validadores
- `2bcfcd6` — Scaffolding validação + ExecutionResult.evidence
- `8700853` — ProjectGate

## Arquitetura

### Camadas
```
src/pedagogy/    → Modelos, memória, planner, extratores, probes, composer, conhecimento
src/learning/    → Domínio, engine, executor, tutor, runtime, inspector
scripts/         → Validação, benchmarks
config/          → Settings, ProjectGate, competências YAML
```

### Ciclo de Decisão
Entrada → EvidenceExtractor → EventStore → RuleBasedPlanner → StrategyExecutor → LLMTutor → Resposta

### 6 Regras do Planner
1. Sem competência → PROBE
2. 3 erros consecutivos → RECOVER_BASE
3. 3 acertos consecutivos → ADVANCE
4. Help requested → EXPLAIN
5. 5+ respostas com probe_id → EXERCISE
6. Padrão → PROBE

### ProjectGate (config/project_state.py)
- Dois gates: technical_ready, hypothesis_validated
- SHA-256 integrity hashes
- CI-aware override blocking
- status() nunca levanta exceção

## Dívida Técnica Documentada
- `DT-001`: factory.py importa diretamente de pedagogy (precisa de acesso aos construtores para montar Runtime)
- `DT-002`: engine_inspector.py importa diretamente de pedagogy (precisa de acesso direto para diagnóstico)

## Execução da Suite de Validação
```bash
python scripts/validation/run_all.py
python scripts/validation/run_all.py --select contract
python scripts/validation/run_all.py --json
python scripts/validation/run_all.py --require-gates
```

## Próximos Passos (PR-4 / PR-5)
- PR-4: Streamlit (interface do motor pedagógico)
- PR-5: Comparative Benchmark (motor pedagógico vs pipeline legado)
