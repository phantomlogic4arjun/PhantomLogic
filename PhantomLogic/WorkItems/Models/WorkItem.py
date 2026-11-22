
from dataclasses import dataclass, field
from datetime import datetime, timezone

from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    WorkItemRelationship,
)
from PhantomLogic.WorkItems.Models.WorkItemState import (
    CodeReviewState,
    WorkItemState,
)
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType


@dataclass
class WorkItem:
    id: str
    title: str
    work_item_type: WorkItemType
    created_by: str

    description: str = ""
    state: WorkItemState | CodeReviewState = WorkItemState.PROPOSED
    priority: str | None = None
    assigned_agent: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    relationships: tuple[WorkItemRelationship, ...] = field(
        default_factory=tuple
    )
    acceptance_criteria: tuple[str, ...] = field(default_factory=tuple)

    block_reason: str | None = None
    blocked_return_state: WorkItemState | None = None

    resolution_reason: str | None = None
    removal_reason: str | None = None

    audit_references: tuple[str, ...] = field(default_factory=tuple)

    # Explicit Product Manager authorization evidence.
    authorized_by: str | None = None
    authorized_at: datetime | None = None
    authorization_reason: str | None = None
