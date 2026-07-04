"""Diagnostico del worker."""

from pliegocheck_api.config import get_settings
from pliegocheck_api.decision.findings import DEFAULT_ADAPTER_REGISTRY
from pliegocheck_api.decision.policy import PolicyLoadError, load_active_policy
from pliegocheck_worker import SERVICE_NAME, SERVICE_VERSION
from pliegocheck_worker.decision.orchestrator import decision_queue_connected
from pliegocheck_worker.financial.orchestrator import financial_queue_connected
from pliegocheck_worker.normalization.orchestrator import normalization_queue_connected
from pliegocheck_worker.runner import queue_connected
from pliegocheck_worker.specialized.orchestrator import specialized_queue_connected


def _decision_policy_version() -> str | None:
    try:
        policy, _payload, _digest = load_active_policy()
    except PolicyLoadError:
        return None
    return policy.semantic_version


def health_status() -> dict[str, str | bool | list[str] | None]:
    """Estado del worker con comprobacion real de la cola PostgreSQL."""
    settings = get_settings()
    connected = queue_connected()
    normalization_connected = normalization_queue_connected()
    financial_connected = financial_queue_connected()
    specialized_connected = specialized_queue_connected()
    decision_connected = decision_queue_connected()
    decision_policy = _decision_policy_version()
    return {
        "decision_engine_enabled": decision_connected and decision_policy is not None,
        "decision_policy_version": decision_policy,
        "available_decision_adapters": [
            domain.value for domain in DEFAULT_ADAPTER_REGISTRY.available_domains()
        ],
        "status": "ok" if connected else "error",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "queue_connected": connected,
        "document_processing_enabled": connected,
        "company_evidence_extraction_enabled": connected,
        "financial_evaluation_enabled": financial_connected,
        "specialized_evaluators_enabled": specialized_connected,
        "available_specialized_evaluators": ["LEGAL", "EXPERIENCE", "TECHNICAL"],
        "requirement_normalization_enabled": (
            normalization_connected
            and (settings.ai_enabled or settings.allow_fake_normalization_provider)
        ),
        "normalization_provider": (
            "fake"
            if settings.allow_fake_normalization_provider and not settings.ai_enabled
            else "openai"
        ),
        "normalization_model": settings.openai_normalization_model,
    }
