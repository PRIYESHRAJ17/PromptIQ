"""Centrally Managed Multi-Model Pool Service."""

from promptiq.gateway.privacy_governance import PROVIDER_PRIVACY_PROFILES
from promptiq.schemas.model_pool import (
    DataSensitivityLevel,
    EligibilityState,
    LogicalModelRole,
    ModelCapabilities,
    ModelPoolRecord,
    ModelRateLimits,
    ProviderPrivacyCard,
)

# Centrally managed catalog of model pool entries with dated verification records (late 2026)
CENTRAL_MODEL_POOL: list[ModelPoolRecord] = [
    # 1. Google Gemini 3.8 Flash
    ModelPoolRecord(
        id="gemini-3.8-flash",
        provider="google",
        model_id="gemini-3.8-flash",
        name="Gemini 3.8 Flash",
        model_family="gemini",
        version="3.8-flash-2026",
        eligibility_state=EligibilityState.CONDITIONALLY_ELIGIBLE,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=True, vision=True, long_context=True
        ),
        context_window=1048576,
        output_limit=8192,
        rate_limits=ModelRateLimits(rpm=15, rpd=1500, tpm=1000000, tpd=10000000),
        privacy_card=PROVIDER_PRIVACY_PROFILES["google"],
        max_allowed_data_sensitivity=DataSensitivityLevel.GENERAL,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={
            "instruction_adherence": 0.94,
            "structured_json": 0.96,
            "complex_reasoning": 0.91,
            "long_context_handling": 0.97,
            "security_and_injection": 0.93,
        },
        composite_score=0.94,
        eligible_use_cases=["general_orchestration", "adaptive_discovery", "long_context_synthesis", "prompt_compilation"],
        ineligible_use_cases=["confidential_ip_data", "restricted_compliance_data"],
        verification_date="2026-11-20",
        verification_evidence="Verified under Google AI Studio Developer API zero-price tier. Confirmed no billable project attached.",
        source_url="https://ai.google.dev/gemini-api/docs/pricing",
    ),
    # 2. Google Gemini 3.5 Flash-Lite
    ModelPoolRecord(
        id="gemini-3.5-flash-lite",
        provider="google",
        model_id="gemini-3.5-flash-lite",
        name="Gemini 3.5 Flash-Lite",
        model_family="gemini",
        version="3.5-flash-lite-2026",
        eligibility_state=EligibilityState.CONDITIONALLY_ELIGIBLE,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=True, vision=False, long_context=True
        ),
        context_window=1048576,
        output_limit=8192,
        rate_limits=ModelRateLimits(rpm=30, rpd=1500, tpm=1000000, tpd=10000000),
        privacy_card=PROVIDER_PRIVACY_PROFILES["google"],
        max_allowed_data_sensitivity=DataSensitivityLevel.GENERAL,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={
            "instruction_adherence": 0.90,
            "structured_json": 0.93,
            "complex_reasoning": 0.85,
            "long_context_handling": 0.94,
            "security_and_injection": 0.90,
        },
        composite_score=0.90,
        eligible_use_cases=["fast_classification", "routine_extraction", "quick_profile_turns"],
        ineligible_use_cases=["deep_architectural_reasoning", "confidential_ip_data"],
        verification_date="2026-11-20",
        verification_evidence="Conditionally eligible under Google AI Studio free tier. Excluded from general production due to minor restrictions and human review.",
        source_url="https://ai.google.dev/gemini-api/docs/pricing",
    ),
    # 3. Google Gemini 2.5 Flash
    ModelPoolRecord(
        id="gemini-2.5-flash",
        provider="google",
        model_id="gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        model_family="gemini",
        version="2.5-flash-2025",
        eligibility_state=EligibilityState.CONDITIONALLY_ELIGIBLE,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=True, vision=True, long_context=True
        ),
        context_window=1048576,
        output_limit=8192,
        rate_limits=ModelRateLimits(rpm=15, rpd=1500, tpm=1000000, tpd=10000000),
        privacy_card=PROVIDER_PRIVACY_PROFILES["google"],
        max_allowed_data_sensitivity=DataSensitivityLevel.GENERAL,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={
            "instruction_adherence": 0.91,
            "structured_json": 0.92,
            "complex_reasoning": 0.88,
            "long_context_handling": 0.95,
            "security_and_injection": 0.89,
        },
        composite_score=0.91,
        eligible_use_cases=["secondary_generator", "discovery_continuation"],
        ineligible_use_cases=["confidential_ip_data"],
        verification_date="2026-11-20",
        verification_evidence="Verified stable production route on Developer API.",
        source_url="https://ai.google.dev/gemini-api/docs/pricing",
    ),
    # 4. Groq OpenAI GPT-OSS 120B (Active Candidate)
    ModelPoolRecord(
        id="openai/gpt-oss-120b",
        provider="groq",
        model_id="openai/gpt-oss-120b",
        name="OpenAI GPT-OSS 120B (Groq)",
        model_family="gpt-oss",
        version="120b",
        eligibility_state=EligibilityState.VERIFIED_ELIGIBLE,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=True, vision=False, long_context=False
        ),
        context_window=131072,
        output_limit=4096,
        rate_limits=ModelRateLimits(rpm=30, rpd=1000, tpm=8000, tpd=100000),
        privacy_card=PROVIDER_PRIVACY_PROFILES["groq"],
        max_allowed_data_sensitivity=DataSensitivityLevel.CONFIDENTIAL,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={
            "instruction_adherence": 0.95,
            "structured_json": 0.95,
            "complex_reasoning": 0.94,
            "long_context_handling": 0.88,
            "security_and_injection": 0.94,
        },
        composite_score=0.94,
        eligible_use_cases=["reasoning", "independent_critic", "prompt_engineering", "confidential_workflows"],
        ineligible_use_cases=["extreme_long_context_gt_128k", "restricted_compliance_data"],
        verification_date="2026-11-21",
        verification_evidence="Active open-weight candidate on GroqCloud. Free-tier quota: 30 RPM, 1,000 RPD, 100k TPD. Paid Developer Plan excluded.",
        source_url="https://console.groq.com/docs/rate-limits",
    ),
    # 5. Groq OpenAI GPT-OSS 20B (Active Fast Candidate)
    ModelPoolRecord(
        id="openai/gpt-oss-20b",
        provider="groq",
        model_id="openai/gpt-oss-20b",
        name="OpenAI GPT-OSS 20B (Groq)",
        model_family="gpt-oss",
        version="20b",
        eligibility_state=EligibilityState.VERIFIED_ELIGIBLE,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=True, vision=False, long_context=False
        ),
        context_window=131072,
        output_limit=8192,
        rate_limits=ModelRateLimits(rpm=30, rpd=14400, tpm=6000, tpd=500000),
        privacy_card=PROVIDER_PRIVACY_PROFILES["groq"],
        max_allowed_data_sensitivity=DataSensitivityLevel.CONFIDENTIAL,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={
            "instruction_adherence": 0.89,
            "structured_json": 0.90,
            "complex_reasoning": 0.83,
            "long_context_handling": 0.82,
            "security_and_injection": 0.88,
        },
        composite_score=0.88,
        eligible_use_cases=["high_volume_bursts", "fast_filtering", "token_budget_conservation"],
        ineligible_use_cases=["deep_architectural_critique"],
        verification_date="2026-11-21",
        verification_evidence="Active open-weight candidate on GroqCloud. Free-tier quota: 30 RPM, 14,400 RPD, 500k TPD. Paid Developer Plan excluded.",
        source_url="https://console.groq.com/docs/rate-limits",
    ),
    # 6. Groq Qwen 3.8 27B (Preview Candidate - Evaluation Only)
    ModelPoolRecord(
        id="qwen/qwen3.8-27b",
        provider="groq",
        model_id="qwen/qwen3.8-27b",
        name="Qwen 3.8 27B (Groq Preview)",
        model_family="qwen",
        version="3.8-27b-preview",
        eligibility_state=EligibilityState.REVIEW_REQUIRED,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=True, vision=False, long_context=False
        ),
        context_window=131072,
        output_limit=4096,
        rate_limits=ModelRateLimits(rpm=30, rpd=1000, tpm=6000, tpd=100000),
        privacy_card=PROVIDER_PRIVACY_PROFILES["groq"],
        max_allowed_data_sensitivity=DataSensitivityLevel.CONFIDENTIAL,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={
            "instruction_adherence": 0.94,
            "structured_json": 0.95,
            "complex_reasoning": 0.93,
            "long_context_handling": 0.85,
            "security_and_injection": 0.92,
        },
        composite_score=0.93,
        eligible_use_cases=["experimental_evaluation_only"],
        ineligible_use_cases=["production_routing", "production_verification", "extreme_long_context_gt_128k"],
        verification_date="2026-11-21",
        verification_evidence="Preview/experimental model on GroqCloud. Per Phase 3.4 directive, preview models are strictly barred from production routes.",
        source_url="https://console.groq.com/docs/rate-limits",
    ),
    # 7. Internal Deterministic Mock
    ModelPoolRecord(
        id="promptiq-mock-v1",
        provider="mock",
        model_id="promptiq-mock-v1",
        name="PromptIQ Internal Deterministic Engine",
        model_family="internal",
        version="v1",
        eligibility_state=EligibilityState.VERIFIED_ELIGIBLE,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=True, vision=True, long_context=True
        ),
        context_window=2000000,
        output_limit=16384,
        rate_limits=ModelRateLimits(rpm=10000, rpd=1000000, tpm=10000000, tpd=100000000),
        privacy_card=PROVIDER_PRIVACY_PROFILES["mock"],
        max_allowed_data_sensitivity=DataSensitivityLevel.RESTRICTED,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={
            "instruction_adherence": 1.0,
            "structured_json": 1.0,
            "complex_reasoning": 0.95,
            "long_context_handling": 1.0,
            "security_and_injection": 1.0,
        },
        composite_score=0.99,
        eligible_use_cases=["deterministic_testing", "restricted_data_airgap", "offline_verification"],
        ineligible_use_cases=[],
        verification_date="2026-11-20",
        verification_evidence="Air-gapped in-memory execution. Zero external egress.",
        source_url="internal://promptiq/mock",
    ),
    # 8. OpenRouter Meta Llama 3.3 70B Instruct Free (Conditionally Eligible)
    ModelPoolRecord(
        id="meta-llama/llama-3.3-70b-instruct:free",
        provider="openrouter",
        model_id="meta-llama/llama-3.3-70b-instruct:free",
        name="Llama 3.3 70B Instruct (OpenRouter Free)",
        model_family="llama",
        version="3.3-70b-free",
        eligibility_state=EligibilityState.CONDITIONALLY_ELIGIBLE,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=True, vision=False, long_context=False
        ),
        context_window=131072,
        output_limit=4096,
        rate_limits=ModelRateLimits(rpm=20, rpd=50, tpm=5000, tpd=50000),
        privacy_card=PROVIDER_PRIVACY_PROFILES["openrouter"],
        max_allowed_data_sensitivity=DataSensitivityLevel.GENERAL,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={"instruction_adherence": 0.90, "structured_json": 0.90},
        composite_score=0.90,
        eligible_use_cases=["secondary_failover", "public_research"],
        ineligible_use_cases=["confidential_ip_data"],
        verification_date="2026-11-21",
        verification_evidence="OpenRouter free variants capped at 50 RPD for accounts with <$10 lifetime purchases.",
        source_url="https://openrouter.ai/models/meta-llama/llama-3.3-70b-instruct:free",
    ),
    # 9. Cloudflare Workers AI Llama 3.1 8B Instruct (Conditionally Eligible)
    ModelPoolRecord(
        id="@cf/meta/llama-3.1-8b-instruct",
        provider="cloudflare",
        model_id="@cf/meta/llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct (Cloudflare Workers AI)",
        model_family="llama",
        version="3.1-8b-cf",
        eligibility_state=EligibilityState.CONDITIONALLY_ELIGIBLE,
        capabilities=ModelCapabilities(
            reasoning=True, coding=True, structured_output=True, tools=False, vision=False, long_context=False
        ),
        context_window=131072,
        output_limit=4096,
        rate_limits=ModelRateLimits(rpm=100, rpd=2000, tpm=50000, tpd=200000),
        privacy_card=ProviderPrivacyCard(
            training_policy="no_training",
            data_retention_days=0,
            allows_confidential_data=True,
            allows_minors=True,
            privacy_notes="Cloudflare Workers AI does not train on customer inference requests.",
        ),
        max_allowed_data_sensitivity=DataSensitivityLevel.CONFIDENTIAL,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=True,
        benchmark_scores={"instruction_adherence": 0.88, "structured_json": 0.89},
        composite_score=0.88,
        eligible_use_cases=["edge_classification", "fast_filtering", "token_budget_conservation"],
        ineligible_use_cases=["deep_architectural_critique", "complex_multi_turn_reasoning"],
        verification_date="2026-11-21",
        verification_evidence="Free tier offers 10,000 Neurons/day with native hard stop on free plans.",
        source_url="https://developers.cloudflare.com/workers-ai/platform/pricing/",
    ),
    # 10. Cerebras Llama 3.3 70B (Ineligible: Credit card required, promotional credits only)
    ModelPoolRecord(
        id="cerebras/llama-3.3-70b",
        provider="cerebras",
        model_id="llama-3.3-70b",
        name="Llama 3.3 70B (Cerebras)",
        model_family="llama",
        version="3.3-70b",
        eligibility_state=EligibilityState.INELIGIBLE_BILLING,
        capabilities=ModelCapabilities(),
        context_window=131072,
        output_limit=8192,
        rate_limits=ModelRateLimits(rpm=0, rpd=0, tpm=0, tpd=0),
        privacy_card=ProviderPrivacyCard(
            training_policy="unverified",
            data_retention_days=30,
            allows_confidential_data=False,
            allows_minors=False,
        ),
        max_allowed_data_sensitivity=DataSensitivityLevel.PUBLIC,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=False,
        benchmark_scores={},
        composite_score=0.0,
        eligible_use_cases=[],
        ineligible_use_cases=["all"],
        verification_date="2026-11-21",
        verification_evidence="No permanent free tier. Promotional $5 credit expires after 30 days and requires a credit card.",
        source_url="https://inference-docs.cerebras.ai/pricing",
    ),
    # 11. SambaNova Llama 3.3 70B (Ineligible: Extreme 20 RPD bottleneck on cardless free tier)
    ModelPoolRecord(
        id="sambanova/Meta-Llama-3.3-70B-Instruct",
        provider="sambanova",
        model_id="Meta-Llama-3.3-70B-Instruct",
        name="Meta-Llama-3.3-70B-Instruct (SambaNova)",
        model_family="llama",
        version="3.3-70b",
        eligibility_state=EligibilityState.INELIGIBLE_TERMS,
        capabilities=ModelCapabilities(),
        context_window=131072,
        output_limit=4096,
        rate_limits=ModelRateLimits(rpm=0, rpd=0, tpm=0, tpd=0),
        privacy_card=ProviderPrivacyCard(
            training_policy="unverified",
            data_retention_days=30,
            allows_confidential_data=False,
            allows_minors=False,
        ),
        max_allowed_data_sensitivity=DataSensitivityLevel.PUBLIC,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=False,
        benchmark_scores={},
        composite_score=0.0,
        eligible_use_cases=[],
        ineligible_use_cases=["all"],
        verification_date="2026-11-21",
        verification_evidence="Free tier without credit card is capped at 20 RPD. Adding credit card unlocks paid Developer tier.",
        source_url="https://cloud.sambanova.ai/pricing",
    ),
    # 12. NVIDIA NIM Llama 3.3 70B (Ineligible: Non-commercial evaluation license only)
    ModelPoolRecord(
        id="nvidia/meta/llama-3.3-70b-instruct",
        provider="nvidia",
        model_id="meta/llama-3.3-70b-instruct",
        name="Llama 3.3 70B Instruct (NVIDIA NIM)",
        model_family="llama",
        version="3.3-70b-nim",
        eligibility_state=EligibilityState.INELIGIBLE_TERMS,
        capabilities=ModelCapabilities(),
        context_window=131072,
        output_limit=4096,
        rate_limits=ModelRateLimits(rpm=0, rpd=0, tpm=0, tpd=0),
        privacy_card=ProviderPrivacyCard(
            training_policy="unverified",
            data_retention_days=30,
            allows_confidential_data=False,
            allows_minors=False,
        ),
        max_allowed_data_sensitivity=DataSensitivityLevel.PUBLIC,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=False,
        benchmark_scores={},
        composite_score=0.0,
        eligible_use_cases=[],
        ineligible_use_cases=["all"],
        verification_date="2026-11-21",
        verification_evidence="build.nvidia.com free endpoints are restricted to personal development and evaluation. Commercial production requires NVIDIA AI Enterprise ($4,500/GPU/yr).",
        source_url="https://build.nvidia.com/",
    ),
    # 9. Retired Models (Blacklisted)
    ModelPoolRecord(
        id="gemini-2.0-flash",
        provider="google",
        model_id="gemini-2.0-flash",
        name="Gemini 2.0 Flash (RETIRED)",
        model_family="gemini",
        version="2.0-retired",
        eligibility_state=EligibilityState.RETIRED,
        capabilities=ModelCapabilities(),
        context_window=1048576,
        output_limit=8192,
        rate_limits=ModelRateLimits(rpm=0, rpd=0, tpm=0, tpd=0),
        privacy_card=PROVIDER_PRIVACY_PROFILES["google"],
        max_allowed_data_sensitivity=DataSensitivityLevel.PUBLIC,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=False,
        benchmark_scores={},
        composite_score=0.0,
        eligible_use_cases=[],
        ineligible_use_cases=["all"],
        verification_date="2026-06-01",
        verification_evidence="Shutdown on June 1, 2026. Prohibited from execution.",
        source_url="https://ai.google.dev/gemini-api/docs/pricing",
    ),
    ModelPoolRecord(
        id="llama-3.3-70b-versatile",
        provider="groq",
        model_id="llama-3.3-70b-versatile",
        name="Llama 3.3 70B Versatile (RETIRED)",
        model_family="llama",
        version="3.3-70b-retired",
        eligibility_state=EligibilityState.RETIRED,
        capabilities=ModelCapabilities(),
        context_window=131072,
        output_limit=4096,
        rate_limits=ModelRateLimits(rpm=0, rpd=0, tpm=0, tpd=0),
        privacy_card=PROVIDER_PRIVACY_PROFILES["groq"],
        max_allowed_data_sensitivity=DataSensitivityLevel.PUBLIC,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=False,
        benchmark_scores={},
        composite_score=0.0,
        eligible_use_cases=[],
        ineligible_use_cases=["all"],
        verification_date="2026-10-31",
        verification_evidence="Officially retired on GroqCloud endpoints in 2026. Prohibited from execution.",
        source_url="https://console.groq.com/docs/rate-limits",
    ),
    ModelPoolRecord(
        id="llama-3.1-8b-instant",
        provider="groq",
        model_id="llama-3.1-8b-instant",
        name="Llama 3.1 8B Instant (RETIRED)",
        model_family="llama",
        version="3.1-8b-retired",
        eligibility_state=EligibilityState.RETIRED,
        capabilities=ModelCapabilities(),
        context_window=131072,
        output_limit=8192,
        rate_limits=ModelRateLimits(rpm=0, rpd=0, tpm=0, tpd=0),
        privacy_card=PROVIDER_PRIVACY_PROFILES["groq"],
        max_allowed_data_sensitivity=DataSensitivityLevel.PUBLIC,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=False,
        benchmark_scores={},
        composite_score=0.0,
        eligible_use_cases=[],
        ineligible_use_cases=["all"],
        verification_date="2026-10-31",
        verification_evidence="Officially retired on GroqCloud endpoints in 2026. Prohibited from execution.",
        source_url="https://console.groq.com/docs/rate-limits",
    ),
    ModelPoolRecord(
        id="qwen-2.5-coder-32b",
        provider="groq",
        model_id="qwen-2.5-coder-32b",
        name="Qwen 2.5 Coder 32B (RETIRED)",
        model_family="qwen",
        version="2.5-32b-retired",
        eligibility_state=EligibilityState.RETIRED,
        capabilities=ModelCapabilities(),
        context_window=131072,
        output_limit=4096,
        rate_limits=ModelRateLimits(rpm=0, rpd=0, tpm=0, tpd=0),
        privacy_card=PROVIDER_PRIVACY_PROFILES["groq"],
        max_allowed_data_sensitivity=DataSensitivityLevel.PUBLIC,
        cost_input_per_token=0.0,
        cost_output_per_token=0.0,
        is_zero_price=False,
        benchmark_scores={},
        composite_score=0.0,
        eligible_use_cases=[],
        ineligible_use_cases=["all"],
        verification_date="2026-10-31",
        verification_evidence="Officially retired on GroqCloud endpoints in 2026. Prohibited from execution.",
        source_url="https://console.groq.com/docs/rate-limits",
    ),
    # 10. Paid Models (Strictly Ineligible for Internal Inference)
    ModelPoolRecord(
        id="claude-3-7-sonnet",
        provider="anthropic",
        model_id="claude-3-7-sonnet-20250219",
        name="Claude 3.7 Sonnet (PAID TARGET ONLY)",
        model_family="claude",
        version="3.7-sonnet",
        eligibility_state=EligibilityState.INELIGIBLE_PAID,
        capabilities=ModelCapabilities(reasoning=True, coding=True, structured_output=True),
        context_window=200000,
        output_limit=8192,
        rate_limits=ModelRateLimits(rpm=0, rpd=0, tpm=0, tpd=0),
        privacy_card=ProviderPrivacyCard(training_policy="paid_commercial", data_retention_days=30, allows_confidential_data=True),
        max_allowed_data_sensitivity=DataSensitivityLevel.CONFIDENTIAL,
        cost_input_per_token=0.000003,
        cost_output_per_token=0.000015,
        is_zero_price=False,
        benchmark_scores={},
        composite_score=0.0,
        eligible_use_cases=["external_target_compilation_only"],
        ineligible_use_cases=["internal_inference"],
        verification_date="2026-11-20",
        verification_evidence="Paid commercial API. Strictly forbidden from internal PromptIQ execution.",
        source_url="https://platform.claude.com/docs/en/models/overview",
    ),
]


class ModelPoolService:
    """Manages the zero-price multi-model pool, querying, and role compatibility."""

    @staticmethod
    def list_models(
        eligibility_state: EligibilityState | None = None,
        zero_price_only: bool = True,
    ) -> list[ModelPoolRecord]:
        """Lists models filtered by eligibility state and zero-price requirement."""
        results: list[ModelPoolRecord] = []
        for m in CENTRAL_MODEL_POOL:
            if zero_price_only and not m.is_zero_price:
                continue
            if eligibility_state is not None and m.eligibility_state != eligibility_state:
                continue
            results.append(m)
        return results

    @staticmethod
    def get_model(model_id: str) -> ModelPoolRecord | None:
        """Retrieves a model by unique ID or provider model_id."""
        for m in CENTRAL_MODEL_POOL:
            if m.id == model_id or m.model_id == model_id:
                return m
        return None

    @classmethod
    def get_verified_eligible_models(cls, include_conditional: bool = False) -> list[ModelPoolRecord]:
        """Returns all verified eligible zero-price models, optionally including conditional models."""
        results = cls.list_models(eligibility_state=EligibilityState.VERIFIED_ELIGIBLE, zero_price_only=True)
        if include_conditional:
            results.extend(cls.list_models(eligibility_state=EligibilityState.CONDITIONALLY_ELIGIBLE, zero_price_only=True))
        return results

    @classmethod
    def get_candidates_for_role(
        cls,
        role: LogicalModelRole,
        sensitivity: DataSensitivityLevel = DataSensitivityLevel.GENERAL,
        required_context_length: int = 4000,
        include_conditional: bool = False,
    ) -> list[ModelPoolRecord]:
        """Identifies eligible candidate models matching a logical role and data sensitivity."""
        from promptiq.gateway.privacy_governance import PrivacyGovernanceService

        eligible_models = cls.get_verified_eligible_models(include_conditional=include_conditional)
        # Filter for privacy
        privacy_safe = PrivacyGovernanceService.filter_models_for_sensitivity(eligible_models, sensitivity)

        candidates: list[ModelPoolRecord] = []
        for m in privacy_safe:
            # Check context window
            if m.context_window < required_context_length:
                continue

            # Role capability matching
            if role == LogicalModelRole.FAST:
                # Lightweight fast model
                if m.provider in ("google", "groq", "mock") and (m.rate_limits.rpm >= 30 or m.model_family == "internal"):
                    candidates.append(m)
            elif role == LogicalModelRole.REASONING:
                if m.capabilities.reasoning and m.composite_score >= 0.90:
                    candidates.append(m)
            elif role == LogicalModelRole.RESEARCH:
                if m.capabilities.long_context or m.context_window >= 100000:
                    candidates.append(m)
            elif role == LogicalModelRole.PROMPT_ENGINEER:
                if m.capabilities.structured_output and m.composite_score >= 0.90:
                    candidates.append(m)
            elif role == LogicalModelRole.CRITIC:
                # Critic must have reasoning capability (allows GPT-OSS 120B and GPT-OSS 20B)
                if m.capabilities.reasoning and (m.composite_score >= 0.85 or m.model_id == "openai/gpt-oss-20b"):
                    candidates.append(m)
            elif role == LogicalModelRole.VERIFIER:
                if m.capabilities.structured_output or m.model_family == "internal":
                    candidates.append(m)
            elif role == LogicalModelRole.ORCHESTRATOR:
                if m.capabilities.tools and m.composite_score >= 0.90:
                    candidates.append(m)
            else:
                candidates.append(m)

        # Sort candidates by composite score descending
        candidates.sort(key=lambda x: x.composite_score, reverse=True)
        return candidates
