"""Prompt Test Lab and Benchmark evaluation database models."""

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from promptiq.core.database import Base
from promptiq.models.base import TimestampMixin, UUIDMixin


class EvaluationSuite(Base, UUIDMixin, TimestampMixin):
    """Test suite bundle specifying test cases, reference assertions, and constraints."""

    __tablename__ = "evaluation_suites"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    test_cases: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    assertions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class EvaluationRun(Base, UUIDMixin, TimestampMixin):
    """Record of an execution run against an evaluation suite."""

    __tablename__ = "evaluation_runs"

    suite_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_suites.id"), nullable=False, index=True
    )
    package_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("prompt_packages.id"), nullable=True, index=True
    )

    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_route: Mapped[str] = mapped_column(String(64), nullable=False)

    pass_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    results: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_estimate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # Always 0.0 under zero-price policy


class FailureRecord(Base, UUIDMixin, TimestampMixin):
    """Failure intelligence record with root-cause hypotheses and regression seeds."""

    __tablename__ = "failure_records"

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )
    run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evaluation_runs.id"), nullable=True
    )

    failure_class: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # intent_loss, format, hallucination, timeout
    observed_failure: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    correction: Mapped[str] = mapped_column(Text, nullable=False)
    regression_seed: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
