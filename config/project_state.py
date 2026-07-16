"""
ProjectGate - Mecanismo de enforcement arquitetural.

Controla o acesso a funcionalidades que dependem de validacao previa:
- technical_ready: motor esta tecnicamente pronto (determinismo, contrato, etc.)
- hypothesis_validated: hipotese pedagogica foi validada com usuarios reais

Caracteristicas:
- Persistencia em disco (.gate_state.json) com hash SHA-256
- CI-aware: override nao funciona em CI
- Dois gates separados (tecnico e pedagogico)
- status() nunca levanta excecao
"""

import hashlib
import json
import os
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class GateBlocked(Exception):
    """Excecao lancada quando um gate bloqueia uma operacao."""
    pass


class ProjectGate:
    """
    Gate de enforcement arquitetural.

    Uso:
        ProjectGate.require_hypothesis_validated("Streamlit Integration")
        ProjectGate.mark_hypothesis_validated("reports/benchmark.json", reviewer_approved=True)
        status = ProjectGate.status()
    """

    _hypothesis_validated: bool = False
    _technical_ready: bool = False
    _hypothesis_validation_date: Optional[str] = None
    _hypothesis_validation_evidence: Optional[str] = None
    _technical_ready_date: Optional[str] = None
    _technical_ready_evidence: Optional[str] = None

    GATE_STATE_FILE: Path = Path("config/.gate_state.json")

    @classmethod
    def _get_state_file(cls) -> Path:
        return cls.GATE_STATE_FILE

    @classmethod
    def _compute_hash(cls, file_path: Optional[str]) -> Optional[str]:
        """Calcula o hash SHA-256 de um arquivo."""
        if not file_path:
            return None
        path = Path(file_path)
        if not path.exists():
            return None
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception:
            return None

    @classmethod
    def _load_state(cls) -> None:
        """
        Carrega o estado persistido do disco com verificacao de integridade.
        NUNCA levanta excecao para quem chama — loga warnings e mantem estado default.
        """
        state_file = cls._get_state_file()
        if not state_file.exists():
            return

        try:
            with open(state_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            warnings.warn(f"⚠️  Nao foi possivel ler o arquivo de estado: {e}")
            return

        if data.get("hypothesis_validated", False):
            evidence_path = data.get("hypothesis_evidence_path")
            stored_hash = data.get("hypothesis_evidence_hash")

            if evidence_path and stored_hash:
                current_hash = cls._compute_hash(evidence_path)
                if current_hash != stored_hash:
                    warnings.warn(
                        f"⚠️  Estado do gate INCONSISTENTE: arquivo de evidencia "
                        f"da hipotese foi alterado.\n"
                        f"    Arquivo: {evidence_path}\n"
                        f"    Hash armazenado: {stored_hash}\n"
                        f"    Hash atual: {current_hash}\n"
                        f"    Re-execute o benchmark e mark_hypothesis_validated()."
                    )
                else:
                    cls._hypothesis_validated = data.get("hypothesis_validated", False)
                    cls._hypothesis_validation_date = data.get("hypothesis_validation_date")
                    cls._hypothesis_validation_evidence = evidence_path
            else:
                warnings.warn(
                    f"⚠️  Estado do gate INCOMPLETO: evidencia da hipotese "
                    f"nao encontrada.\n"
                    f"    Caminho: {evidence_path}\n"
                    f"    Re-execute o benchmark e mark_hypothesis_validated()."
                )

        if data.get("technical_ready", False):
            evidence_path = data.get("technical_ready_evidence")
            stored_hash = data.get("technical_ready_hash")

            if evidence_path and stored_hash:
                current_hash = cls._compute_hash(evidence_path)
                if current_hash != stored_hash:
                    warnings.warn(
                        f"⚠️  Estado do gate INCONSISTENTE: arquivo de evidencia "
                        f"da prontidao tecnica foi alterado.\n"
                        f"    Arquivo: {evidence_path}\n"
                        f"    Hash armazenado: {stored_hash}\n"
                        f"    Hash atual: {current_hash}\n"
                        f"    Re-execute o readiness validator e mark_technical_ready()."
                    )
                else:
                    cls._technical_ready = data.get("technical_ready", False)
                    cls._technical_ready_date = data.get("technical_ready_date")
                    cls._technical_ready_evidence = evidence_path
            else:
                warnings.warn(
                    f"⚠️  Estado do gate INCOMPLETO: evidencia da prontidao "
                    f"tecnica nao encontrada.\n"
                    f"    Caminho: {evidence_path}\n"
                    f"    Re-execute o readiness validator e mark_technical_ready()."
                )

    @classmethod
    def _save_state(cls) -> None:
        """Persiste o estado em disco com hash de integridade."""
        hypothesis_hash = cls._compute_hash(cls._hypothesis_validation_evidence)
        technical_hash = cls._compute_hash(cls._technical_ready_evidence)

        data = {
            "hypothesis_validated": cls._hypothesis_validated,
            "technical_ready": cls._technical_ready,
            "hypothesis_validation_date": cls._hypothesis_validation_date,
            "hypothesis_evidence_path": cls._hypothesis_validation_evidence,
            "hypothesis_evidence_hash": hypothesis_hash,
            "technical_ready_date": cls._technical_ready_date,
            "technical_ready_evidence": cls._technical_ready_evidence,
            "technical_ready_hash": technical_hash,
            "last_updated": datetime.now().isoformat(),
        }

        state_file = cls._get_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)

        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def status(cls) -> Dict[str, Any]:
        """
        Retorna o status atual do gate.

        NOTA: Esta funcao NUNCA levanta excecao.
        O campo 'integrity' indica se o estado e consistente.
        """
        integrity = "ok"
        try:
            cls._load_state()
        except Exception as e:
            integrity = f"error: {str(e)}"

        return {
            "hypothesis_validated": cls._hypothesis_validated,
            "technical_ready": cls._technical_ready,
            "hypothesis_validation_date": cls._hypothesis_validation_date,
            "hypothesis_evidence_path": cls._hypothesis_validation_evidence,
            "technical_ready_date": cls._technical_ready_date,
            "technical_ready_evidence": cls._technical_ready_evidence,
            "integrity": integrity,
            "gate_state_file": str(cls._get_state_file()),
            "gate_state_exists": cls._get_state_file().exists(),
        }

    @classmethod
    def require_technical_readiness(cls, feature_name: str) -> None:
        """Verifica se o motor esta tecnicamente pronto. Levanta GateBlocked se nao."""
        cls._load_state()
        if not cls._technical_ready:
            raise GateBlocked(
                f"Bloqueado: '{feature_name}' requer prontidao tecnica.\n"
                f"   Rode o readiness validator antes de prosseguir.\n"
                f"   Status: ProjectGate.status()"
            )

    @classmethod
    def mark_technical_ready(cls, evidence_path: str) -> None:
        """
        Marca que o motor esta tecnicamente pronto.
        Valida o relatorio do readiness validator antes de marcar.
        """
        result = cls._load_and_validate_readiness_report(evidence_path)

        if not result.get("all_gates_passed", False):
            failures = result.get("failures", [])
            raise GateBlocked(
                f"Evidencia nao confirma prontidao tecnica.\n"
                f"  Gates falhos: {', '.join(failures)}"
            )

        if result.get("intervention_success_rate", 0) < 1.0:
            raise GateBlocked(
                f"Evidencia nao confirma prontidao tecnica: intervencoes < 100%.\n"
                f"  Obtido: {result.get('intervention_success_rate', 0)*100:.1f}%"
            )

        if result.get("planner_determinism_rate", 0) < 1.0:
            raise GateBlocked(
                f"Evidencia nao confirma prontidao tecnica: Planner nao deterministico.\n"
                f"  Obtido: {result.get('planner_determinism_rate', 0)*100:.1f}%"
            )

        cls._technical_ready = True
        cls._technical_ready_date = datetime.now().isoformat()
        cls._technical_ready_evidence = evidence_path
        cls._save_state()

        print(f"Prontidao tecnica confirmada!")
        print(f"   Evidencia: {evidence_path}")
        print(f"   Intervencoes: {result.get('intervention_success_rate', 0)*100:.1f}%")
        print(f"   Determinismo: {result.get('planner_determinism_rate', 0)*100:.1f}%")

    @classmethod
    def reset_technical_readiness(cls) -> None:
        """Reseta o estado de prontidao tecnica (para testes ou apos mudancas)."""
        cls._technical_ready = False
        cls._technical_ready_date = None
        cls._technical_ready_evidence = None
        cls._save_state()

    @classmethod
    def _load_and_validate_readiness_report(cls, path: str) -> Dict[str, Any]:
        """Carrega e valida o relatorio de readiness validator."""
        report_path = Path(path)
        if not report_path.exists():
            raise GateBlocked(f"Arquivo de evidencia nao encontrado: {path}")

        try:
            with open(report_path) as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise GateBlocked(f"Arquivo de evidencia invalido (nao e JSON): {path}")

        required = ["all_gates_passed", "intervention_success_rate", "planner_determinism_rate"]
        for field in required:
            if field not in data:
                raise GateBlocked(
                    f"Relatorio incompleto: campo '{field}' nao encontrado."
                )

        return data

    @classmethod
    def require_hypothesis_validated(cls, feature_name: str, override: bool = False) -> None:
        """
        Verifica se a hipotese pedagogica foi validada.

        Args:
            feature_name: Nome da funcionalidade sendo verificada
            override: Se True, permite bypass (apenas fora de CI)
        """
        cls._load_state()

        if cls._hypothesis_validated:
            return

        if override:
            if os.environ.get("CI") == "true":
                raise GateBlocked(
                    f"Bloqueado em CI: '{feature_name}' requer hipotese validada.\n"
                    f"   Override nao permitido em ambiente de CI."
                )
            warnings.warn(
                f"Aviso: '{feature_name}' sem hipotese validada — permitido fora de CI.",
                UserWarning,
            )
        else:
            raise GateBlocked(
                f"Bloqueado: '{feature_name}' requer validacao de hipotese.\n"
                f"   Rode o benchmark com usuarios reais antes de prosseguir.\n"
                f"   Para forcar (apenas local): override=True"
            )

    @classmethod
    def mark_hypothesis_validated(cls, evidence_path: str, reviewer_approved: bool = False) -> None:
        """
        Marca que a hipotese foi validada.

        Args:
            evidence_path: Caminho para o relatorio de benchmark validado
            reviewer_approved: Flag indicando que um segundo revisor aprovou

        NOTA: reviewer_approved e uma protecao de PROCESSO, nao tecnica.
        O codigo NAO verifica automaticamente se um segundo revisor aprovou.
        A responsabilidade e do revisor humano verificar o relatorio no PR.
        """
        if not reviewer_approved:
            raise GateBlocked(
                "Validacao de hipotese requer aprovacao de um segundo revisor.\n"
                "   Esta e a decisao mais cara do projeto. Documente a revisao no PR.\n"
                "   Para confirmar, passe reviewer_approved=True apos revisao.\n"
                "   NOTA: Protecao de PROCESSO, nao tecnica."
            )

        report = cls._load_and_validate_benchmark_report(evidence_path)

        if report.get("tier1_success_rate", 0) < 0.95:
            raise GateBlocked(
                f"Tier 1 (contrato) < 95%: {report.get('tier1_success_rate', 0)*100:.1f}%"
            )

        if report.get("tier2_success_rate", 0) < 0.90:
            raise GateBlocked(
                f"Tier 2 (intervencao) < 90%: {report.get('tier2_success_rate', 0)*100:.1f}%"
            )

        if report.get("tier3_success_rate", 0) <= report.get("baseline_success_rate", 0):
            raise GateBlocked(
                f"Ciclo nao superou explicacao direta: "
                f"{report.get('tier3_success_rate', 0)*100:.1f}% vs "
                f"{report.get('baseline_success_rate', 0)*100:.1f}%"
            )

        cls._hypothesis_validated = True
        cls._hypothesis_validation_date = datetime.now().isoformat()
        cls._hypothesis_validation_evidence = evidence_path
        cls._save_state()

        print(f"Hipotese validada com sucesso!")
        print(f"   Evidencia: {evidence_path}")
        print(f"   Tier 1: {report['tier1_success_rate']*100:.1f}%")
        print(f"   Tier 2: {report['tier2_success_rate']*100:.1f}%")
        print(f"   Tier 3 (ciclo): {report['tier3_success_rate']*100:.1f}%")
        print(f"   Baseline: {report['baseline_success_rate']*100:.1f}%")

    @classmethod
    def reset_hypothesis_validation(cls) -> None:
        """Reseta o estado de validacao de hipotese (para testes)."""
        cls._hypothesis_validated = False
        cls._hypothesis_validation_date = None
        cls._hypothesis_validation_evidence = None
        cls._save_state()

    @classmethod
    def _load_and_validate_benchmark_report(cls, path: str) -> Dict[str, Any]:
        """Carrega e valida o relatorio de benchmark."""
        report_path = Path(path)
        if not report_path.exists():
            raise GateBlocked(f"Arquivo de evidencia nao encontrado: {path}")

        try:
            with open(report_path) as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise GateBlocked(f"Arquivo de evidencia invalido (nao e JSON): {path}")

        required = [
            "tier1_success_rate",
            "tier2_success_rate",
            "tier3_success_rate",
            "baseline_success_rate",
        ]
        for field in required:
            if field not in data:
                raise GateBlocked(
                    f"Relatorio incompleto: campo '{field}' nao encontrado.\n"
                    f"   Certifique-se de que contem todos os niveis do benchmark."
                )

        return data
