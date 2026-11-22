
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import datetime, timezone

from PhantomLogic.WorkItems.Manager.WorkItemRelationshipManager import (
    WorkItemRelationshipManager,
)
from PhantomLogic.WorkItems.Manager.WorkItemValidator import WorkItemValidator
from PhantomLogic.WorkItems.Models.WorkItem import WorkItem
from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    WorkItemRelationship,
    RelationshipType,
)
from PhantomLogic.WorkItems.Models.WorkItemState import (
    CodeReviewState,
    WorkItemState,
)
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType
from PhantomLogic.WorkItems.Rules.HierarchyRules import HierarchyRules
from PhantomLogic.WorkItems.Rules.PermissionRules import (
    AgentRole,
    PermissionRules,
    WorkItemOperation,
)
from PhantomLogic.WorkItems.Rules.ReadinessRules import ReadinessRules
from PhantomLogic.WorkItems.Rules.ResolutionRules import ResolutionRules
from PhantomLogic.WorkItems.Rules.StateTransitionRules import (
    StateTransitionRules,
)


class WorkItemManager:
    """
    Central application interface for work-item operations.

    The manager coordinates existing validators and rules. It does not
    duplicate their business logic.

    Operations return a new collection and an error list. The supplied
    collection and its existing WorkItem instances are never mutated.

    Significant operations may additionally return structured audit events.
    The Orchestrator is responsible for sending those events to AuditWriter.
    """

    def __init__(self) -> None:
        self._transition_rules = StateTransitionRules()
        self._readiness_rules = ReadinessRules()
        self._resolution_rules = ResolutionRules()

    # ------------------------------------------------------------------
    # Registration and retrieval
    # ------------------------------------------------------------------

    @staticmethod
    def _creation_operation(
        work_item: WorkItem,
    ) -> WorkItemOperation | None:
        if not isinstance(work_item, WorkItem):
            return None

        if work_item.work_item_type == WorkItemType.BUG:
            return WorkItemOperation.CREATE_BUG

        if work_item.work_item_type == WorkItemType.TEST_CASE:
            return WorkItemOperation.CREATE_TEST_CASE

        return WorkItemOperation.CREATE_WORK_ITEM

    @classmethod
    def register_work_item(
        cls,
        work_items: Mapping[str, WorkItem],
        work_item: WorkItem,
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        return cls.register_work_items(
            work_items,
            (work_item,),
            actor_role,
        )

    @classmethod
    def register_work_items(
        cls,
        work_items: Mapping[str, WorkItem],
        new_work_items: Iterable[WorkItem],
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        errors = cls._validate_collection_shape(work_items)

        if errors:
            return None, errors

        if not isinstance(actor_role, AgentRole):
            return None, ["Agent role is invalid."]

        try:
            additions = tuple(new_work_items)
        except TypeError:
            return None, [
                "New work items must be an iterable collection."
            ]

        if not additions:
            return None, [
                "At least one work item must be registered."
            ]

        candidate = dict(work_items)
        errors = []
        requested_ids = set()

        for item in additions:
            if not isinstance(item, WorkItem):
                errors.append(
                    "Every registered item must be a WorkItem."
                )
                continue

            errors.extend(
                WorkItemValidator.validate_identity(item)
            )

            if item.id in candidate:
                errors.append(
                    f"Work item ID '{item.id}' already exists."
                )

            if item.id in requested_ids:
                errors.append(
                    f"Duplicate work item ID '{item.id}' "
                    "in registration batch."
                )

            requested_ids.add(item.id)

            operation = cls._creation_operation(item)

            if operation is None:
                continue

            errors.extend(
                PermissionRules.validate_permission(
                    actor_role,
                    operation,
                    item,
                )
            )

            errors.extend(
                WorkItemValidator.validate_structure(item)
            )

            candidate[item.id] = item

        if errors:
            return None, errors

        # Validate references after all batch members have been added.
        # Full hierarchy validation is intentionally not performed here,
        # because hierarchy registration is incremental.
        for item in additions:
            errors.extend(
                WorkItemValidator.validate_relationship_references(
                    item,
                    candidate,
                )
            )

            errors.extend(
                WorkItemValidator.validate_relationship_types(
                    item,
                    candidate,
                )
            )

        if errors:
            return None, errors

        return candidate, []

    @staticmethod
    def get_work_item(
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
    ) -> WorkItem | None:
        if not isinstance(work_items, Mapping):
            return None

        if not isinstance(work_item_id, str):
            return None

        return work_items.get(work_item_id)

    # ------------------------------------------------------------------
    # Explicit authorization
    # ------------------------------------------------------------------

    @staticmethod
    def _authorization_operation_errors(
        item: WorkItem,
        actor_role: AgentRole,
        actor_id: str,
        reason: str,
    ) -> list[str]:
        return PermissionRules.validate_permission(
            actor_role,
            WorkItemOperation.AUTHORIZE_WORK,
            item,
            actor_id=actor_id,
            reason=reason,
        )

    def authorize_work(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        actor_role: AgentRole,
        *,
        actor_id: str,
        reason: str,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """
        Record explicit Product Manager authorization.

        Authorization does not change the work item's state.
        """

        errors = self._validate_collection_shape(work_items)

        if errors:
            return None, errors

        if not isinstance(actor_role, AgentRole):
            return None, ["Agent role is invalid."]

        item = work_items.get(work_item_id)

        if item is None:
            return None, [
                f"Work item '{work_item_id}' does not exist."
            ]

        errors = WorkItemValidator.validate_identity(item)
        errors.extend(
            WorkItemValidator.validate_structure(item)
        )

        if errors:
            return None, errors

        errors = self._authorization_operation_errors(
            item,
            actor_role,
            actor_id,
            reason,
        )

        if errors:
            return None, errors

        if item.state == WorkItemState.REMOVED:
            return None, [
                "Removed work items cannot be authorized. "
                "The Product Manager must explicitly reinstate "
                "the item first."
            ]

        timestamp = datetime.now(timezone.utc)

        updated_item = replace(
            item,
            authorized_by=actor_id.strip(),
            authorized_at=timestamp,
            authorization_reason=reason.strip(),
            updated_at=timestamp,
        )

        candidate = dict(work_items)
        candidate[work_item_id] = updated_item

        return candidate, []

    def authorize_work_with_events(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        actor_role: AgentRole,
        *,
        actor_id: str,
        reason: str,
    ) -> tuple[
        dict[str, WorkItem] | None,
        list[str],
        tuple[dict, ...],
    ]:
        """
        Authorization operation with a separate audit-event result.

        The Orchestrator is responsible for passing these events
        to AuditWriter.
        """

        result, errors = self.authorize_work(
            work_items,
            work_item_id,
            actor_role,
            actor_id=actor_id,
            reason=reason,
        )

        if errors:
            return None, errors, ()

        item = result[work_item_id]

        event = {
            "event_type": "WORK_AUTHORIZED",
            "work_item_id": item.id,
            "work_item_type": item.work_item_type.value,
            "actor_role": actor_role.value,
            "actor_id": item.authorized_by,
            "reason": item.authorization_reason,
            "authorized_at": item.authorized_at.isoformat(),
        }

        return result, [], (event,)

    # ------------------------------------------------------------------
    # Authorized Bug / Change Request propagation
    # ------------------------------------------------------------------

    @staticmethod
    def _relationships_from(
        work_item: WorkItem,
        relationship_type: RelationshipType,
    ) -> set[str]:
        return {
            relationship.target_id
            for relationship in work_item.relationships
            if (
                isinstance(relationship, WorkItemRelationship)
                and relationship.relationship_type == relationship_type
            )
        }

    @classmethod
    def _find_parent_ids(
        cls,
        work_items: Mapping[str, WorkItem],
        child_id: str,
        parent_type: WorkItemType,
    ) -> set[str]:
        """
        Find parents using parent-owned PARENT_CHILD relationships.

        Relationship direction:
            source_id = parent
            target_id = child
        """

        parent_ids = set()

        for candidate in work_items.values():
            if candidate.work_item_type != parent_type:
                continue

            child_ids = cls._relationships_from(
                candidate,
                RelationshipType.PARENT_CHILD,
            )

            if child_id in child_ids:
                parent_ids.add(candidate.id)

        return parent_ids

    @classmethod
    def _derive_propagation_targets(
        cls,
        work_items: Mapping[str, WorkItem],
        source: WorkItem,
    ) -> tuple[set[str] | None, list[str]]:
        """
        Derive affected Requirement -> Use Case -> Feature targets.

        Affected Requirements are discovered from the Bug or Change Request.

        Each affected Requirement must have exactly one Use Case parent.
        Each affected Use Case must have exactly one Feature parent.

        Duplicate Use Cases and Features are automatically deduplicated.
        """

        if source.work_item_type == WorkItemType.BUG:
            link_type = RelationshipType.VIOLATED_REQUIREMENT

        elif source.work_item_type == WorkItemType.CHANGE_REQUEST:
            link_type = RelationshipType.AFFECTED_REQUIREMENT

        else:
            return None, [
                "Propagation must originate from a Bug "
                "or Change Request."
            ]

        requirement_ids = cls._relationships_from(
            source,
            link_type,
        )

        if not requirement_ids:
            return None, [
                f"{source.work_item_type.value} '{source.id}' "
                "must reference at least one affected Requirement."
            ]

        targets = {source.id}
        errors = []

        for requirement_id in sorted(requirement_ids):
            requirement = work_items.get(requirement_id)

            if requirement is None:
                errors.append(
                    f"Requirement '{requirement_id}' does not exist."
                )
                continue

            if requirement.work_item_type != WorkItemType.REQUIREMENT:
                errors.append(
                    f"Linked item '{requirement_id}' "
                    "is not a Requirement."
                )
                continue

            use_case_ids = cls._find_parent_ids(
                work_items,
                requirement_id,
                WorkItemType.USE_CASE,
            )

            if len(use_case_ids) != 1:
                errors.append(
                    f"Requirement '{requirement_id}' must have "
                    "exactly one Use Case parent for "
                    "authorized propagation."
                )
                continue

            use_case_id = next(iter(use_case_ids))
            use_case = work_items.get(use_case_id)

            if use_case is None:
                errors.append(
                    f"Use Case '{use_case_id}' does not exist."
                )
                continue

            feature_ids = cls._find_parent_ids(
                work_items,
                use_case_id,
                WorkItemType.FEATURE,
            )

            if len(feature_ids) != 1:
                errors.append(
                    f"Use Case '{use_case_id}' must have "
                    "exactly one Feature parent for "
                    "authorized propagation."
                )
                continue

            feature_id = next(iter(feature_ids))

            targets.update({
                requirement_id,
                use_case_id,
                feature_id,
            })

        if errors:
            return None, errors

        return targets, []

    def _apply_authorized_propagation(
        self,
        work_items: Mapping[str, WorkItem],
        source: WorkItem,
        target_ids: set[str],
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """
        Apply propagation transitions atomically.

        Proposed, In Test, and Resolved items may move to In Work
        through the explicit authorized-propagation operation.

        Blocked items remain Blocked. Their saved return state becomes
        In Work, so unblocking restores them to the authorized state.

        No supplied WorkItem instance is mutated.
        """

        candidate = dict(work_items)
        timestamp = datetime.now(timezone.utc)

        for item_id in sorted(target_ids):
            item = candidate[item_id]

            if item.state == WorkItemState.REMOVED:
                return None, [
                    f"Propagation cannot reopen Removed work item "
                    f"'{item.id}'. The Product Manager must explicitly "
                    "reinstate it first."
                ]

            if item.state == WorkItemState.BLOCKED:
                candidate[item_id] = replace(
                    item,
                    blocked_return_state=WorkItemState.IN_WORK,
                    updated_at=timestamp,
                )
                continue

            if item.state == WorkItemState.IN_WORK:
                continue

            errors = self._transition_rules.validate_transition(
                item,
                WorkItemState.IN_WORK,
                AgentRole.WORK_ITEM_MANAGER,
                reason=source.authorization_reason,
                work_authorized=True,
                authorized_propagation=True,
                propagation_source_type=source.work_item_type,
            )

            if errors:
                return None, [
                    f"Cannot propagate authorized work to '{item.id}': "
                    f"{error}"
                    for error in errors
                ]

            candidate[item_id] = replace(
                item,
                state=WorkItemState.IN_WORK,
                updated_at=timestamp,
            )

        return candidate, []

    def start_authorized_work(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """
        Start an explicitly authorized Bug or Change Request.

        The operation propagates In Work to every affected Requirement,
        its Use Case, and its Feature.

        The operation is atomic: either every target is updated or
        no changes are returned.
        """

        errors = self.validate_collection(work_items)

        if errors:
            return None, errors

        if not isinstance(actor_role, AgentRole):
            return None, ["Agent role is invalid."]

        source = work_items.get(work_item_id)

        if source is None:
            return None, [
                f"Work item '{work_item_id}' does not exist."
            ]

        errors = PermissionRules.validate_permission(
            actor_role,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            source,
        )

        if errors:
            return None, errors

        if source.state == WorkItemState.REMOVED:
            return None, [
                "Removed work items cannot initiate "
                "authorized propagation."
            ]

        target_ids, errors = self._derive_propagation_targets(
            work_items,
            source,
        )

        if errors:
            return None, errors

        if target_ids is None:
            return None, [
                "Unable to derive authorized propagation targets."
            ]

        # Validate every target before applying any changes.
        for target_id in target_ids:
            target = work_items[target_id]

            if target.state == WorkItemState.REMOVED:
                return None, [
                    f"Propagation cannot reopen Removed work item "
                    f"'{target.id}'. The Product Manager must explicitly "
                    "reinstate it first."
                ]

            if (
                target.work_item_type
                not in self._transition_rules.PROPAGATION_TARGET_TYPES
            ):
                return None, [
                    f"Work item '{target.id}' is not an allowed "
                    "propagation target."
                ]

        return self._apply_authorized_propagation(
            work_items,
            source,
            target_ids,
        )

    def start_authorized_work_with_events(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        actor_role: AgentRole,
    ) -> tuple[
        dict[str, WorkItem] | None,
        list[str],
        tuple[dict, ...],
    ]:
        """
        Propagation operation with separate audit-event output.

        The manager does not write to the audit log.
        """

        result, errors = self.start_authorized_work(
            work_items,
            work_item_id,
            actor_role,
        )

        if errors:
            return None, errors, ()

        source = work_items[work_item_id]
        events = []

        for item_id in sorted(result):
            before = work_items[item_id]
            after = result[item_id]

            if before == after:
                continue

            state_changed = before.state != after.state

            return_state_changed = (
                before.blocked_return_state
                != after.blocked_return_state
            )

            if not state_changed and not return_state_changed:
                continue

            events.append({
                "event_type": "AUTHORIZED_WORK_PROPAGATED",
                "source_work_item_id": source.id,
                "source_work_item_type": source.work_item_type.value,
                "work_item_id": item_id,
                "work_item_type": after.work_item_type.value,
                "previous_state": before.state.value,
                "new_state": after.state.value,
                "blocked_return_state": (
                    after.blocked_return_state.value
                    if after.blocked_return_state is not None
                    else None
                ),
                "authorized_by": source.authorized_by,
                "authorized_at": (
                    source.authorized_at.isoformat()
                    if source.authorized_at is not None
                    else None
                ),
                "reason": source.authorization_reason,
                "occurred_at": after.updated_at.isoformat(),
            })

        return result, [], tuple(events)

    # ------------------------------------------------------------------
    # Collection and hierarchy validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_collection_shape(
        work_items: Mapping[str, WorkItem],
    ) -> list[str]:
        if not isinstance(work_items, Mapping):
            return ["Work items must be supplied as a mapping."]

        errors = []

        for key, item in work_items.items():
            if not isinstance(item, WorkItem):
                errors.append(
                    f"Collection entry '{key}' must contain a WorkItem."
                )
                continue

            if key != item.id:
                errors.append(
                    f"Collection key '{key}' does not match "
                    f"work item ID '{item.id}'."
                )

        return errors

    @classmethod
    def validate_collection(
        cls,
        work_items: Mapping[str, WorkItem],
    ) -> list[str]:
        errors = cls._validate_collection_shape(work_items)

        if errors:
            return errors

        items = dict(work_items)

        for item in items.values():
            errors.extend(
                WorkItemValidator.validate_identity(item)
            )

            errors.extend(
                WorkItemValidator.validate_structure(item)
            )

            errors.extend(
                WorkItemValidator.validate_relationship_references(
                    item,
                    items,
                )
            )

            errors.extend(
                WorkItemValidator.validate_relationship_types(
                    item,
                    items,
                )
            )

        return errors

    @classmethod
    def validate_hierarchy(
        cls,
        work_items: Mapping[str, WorkItem],
    ) -> list[str]:
        errors = cls.validate_collection(work_items)

        if errors:
            return errors

        return HierarchyRules.validate_hierarchy(
            dict(work_items)
        )

    # ------------------------------------------------------------------
    # Relationship management
    # ------------------------------------------------------------------

    @staticmethod
    def add_relationship(
        work_items: Mapping[str, WorkItem],
        relationship: WorkItemRelationship,
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        return WorkItemRelationshipManager.add_relationship(
            work_items,
            relationship,
            actor_role,
        )

    @staticmethod
    def add_relationships(
        work_items: Mapping[str, WorkItem],
        relationships: Iterable[WorkItemRelationship],
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        return WorkItemRelationshipManager.add_relationships(
            work_items,
            relationships,
            actor_role,
        )

    @staticmethod
    def remove_relationship(
        work_items: Mapping[str, WorkItem],
        relationship: WorkItemRelationship,
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        return WorkItemRelationshipManager.remove_relationship(
            work_items,
            relationship,
            actor_role,
        )

    @staticmethod
    def remove_relationships(
        work_items: Mapping[str, WorkItem],
        relationships: Iterable[WorkItemRelationship],
        actor_role: AgentRole,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        return WorkItemRelationshipManager.remove_relationships(
            work_items,
            relationships,
            actor_role,
        )

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def transition_state(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        target_state: WorkItemState | CodeReviewState,
        actor_role: AgentRole,
        *,
        reason: str | None = None,
        work_authorized: bool = False,
        implementation_ready: bool = False,
        verification_passed: bool = False,
        completion_criteria_met: bool = False,
        review_approved: bool = False,
        actor_id: str | None = None,
        related_developer_id: str | None = None,
        previous_state: WorkItemState | None = None,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """
        Guarded public state-transition interface.

        Standard work must use submit_for_test() or resolve_work_item()
        for those lifecycle transitions.

        Starting or reopening ordinary work requires persisted
        Product Manager authorization.

        Code Review Tasks retain their separate Reviewer-owned lifecycle.
        """

        errors = self._validate_collection_shape(work_items)

        if errors:
            return None, errors

        if not isinstance(actor_role, AgentRole):
            return None, ["Agent role is invalid."]

        item = work_items.get(work_item_id)

        if item is None:
            return None, [
                f"Work item '{work_item_id}' does not exist."
            ]

        # Standard work must enter In Test through submit_for_test().
        if (
            target_state == WorkItemState.IN_TEST
            and item.work_item_type != WorkItemType.CODE_REVIEW_TASK
        ):
            return None, [
                "Use submit_for_test() to move work items into In Test."
            ]

        # Standard work must enter Resolved through resolve_work_item().
        if (
            target_state == WorkItemState.RESOLVED
            and item.work_item_type != WorkItemType.CODE_REVIEW_TASK
        ):
            return None, [
                "Use resolve_work_item() to resolve standard work items."
            ]

        # Starting or reopening ordinary work requires persisted
        # Product Manager authorization.
        if (
            target_state == WorkItemState.IN_WORK
            and item.state in {
                WorkItemState.PROPOSED,
                WorkItemState.RESOLVED,
            }
            and item.work_item_type not in {
                WorkItemType.BUG,
                WorkItemType.CHANGE_REQUEST,
            }
        ):
            authorization_valid = (
                isinstance(item.authorized_by, str)
                and bool(item.authorized_by.strip())
                and isinstance(item.authorized_at, datetime)
                and item.authorized_at.tzinfo is not None
                and item.authorized_at.utcoffset() == timezone.utc.utcoffset(
                    item.authorized_at
                )
                and isinstance(item.authorization_reason, str)
                and bool(item.authorization_reason.strip())
            )

            if not authorization_valid:
                return None, [
                    "Work must have valid Product Manager authorization "
                    "before it can be started."
                ]

            # Do not trust the caller's work_authorized argument.
            work_authorized = True

        return self._transition_state(
            work_items,
            work_item_id,
            target_state,
            actor_role,
            reason=reason,
            work_authorized=work_authorized,
            implementation_ready=implementation_ready,
            verification_passed=verification_passed,
            completion_criteria_met=completion_criteria_met,
            review_approved=review_approved,
            actor_id=actor_id,
            related_developer_id=related_developer_id,
            previous_state=previous_state,
        )

    def _transition_state(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        target_state: WorkItemState | CodeReviewState,
        actor_role: AgentRole,
        *,
        reason: str | None = None,
        work_authorized: bool = False,
        implementation_ready: bool = False,
        verification_passed: bool = False,
        completion_criteria_met: bool = False,
        review_approved: bool = False,
        actor_id: str | None = None,
        related_developer_id: str | None = None,
        previous_state: WorkItemState | None = None,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        """
        Internal transition implementation.

        Callers should use the appropriate higher-level Manager operation.
        """

        errors = self._validate_collection_shape(work_items)

        if errors:
            return None, errors

        if not isinstance(actor_role, AgentRole):
            return None, ["Agent role is invalid."]

        item = work_items.get(work_item_id)

        if item is None:
            return None, [
                f"Work item '{work_item_id}' does not exist."
            ]

        # Bugs and Change Requests must use the dedicated propagation
        # operation when moving from Proposed or Resolved to In Work.
        #
        # This prevents an ordinary state transition from reopening the
        # source item without reopening its affected hierarchy.
        if (
            item.work_item_type in {
                WorkItemType.BUG,
                WorkItemType.CHANGE_REQUEST,
            }
            and target_state == WorkItemState.IN_WORK
            and item.state in {
                WorkItemState.PROPOSED,
                WorkItemState.RESOLVED,
            }
        ):
            return None, [
                "Bugs and Change Requests must be started through "
                "start_authorized_work() so their affected hierarchy "
                "is reopened consistently."
            ]

        operation = self._permission_for_transition(
            item,
            target_state,
            actor_role,
        )

        if operation is not None:
            errors = PermissionRules.validate_permission(
                actor_role,
                operation,
                item,
                actor_id=actor_id,
                related_developer_id=related_developer_id,
                reason=reason,
                work_authorized=work_authorized,
                review_approved=review_approved,
                verification_passed=verification_passed,
                completion_criteria_met=completion_criteria_met,
            )

            if errors:
                return None, errors

        if item.state == WorkItemState.BLOCKED:
            previous_state = item.blocked_return_state

        errors = self._transition_rules.validate_transition(
            item,
            target_state,
            actor_role,
            reason=reason,
            previous_state=previous_state,
            work_authorized=work_authorized,
            implementation_ready=implementation_ready,
            verification_passed=verification_passed,
            completion_criteria_met=completion_criteria_met,
            review_approved=review_approved,
        )

        if errors:
            return None, errors

        changes = {
            "state": target_state,
            "updated_at": datetime.now(timezone.utc),
        }

        if target_state == WorkItemState.BLOCKED:
            changes["blocked_return_state"] = item.state
            changes["block_reason"] = reason.strip()

        elif item.state == WorkItemState.BLOCKED:
            changes["blocked_return_state"] = None
            changes["block_reason"] = None

        if target_state == WorkItemState.REMOVED:
            changes["removal_reason"] = reason.strip()

        if target_state == WorkItemState.RESOLVED:
            changes["resolution_reason"] = reason

        candidate = dict(work_items)
        candidate[work_item_id] = replace(
            item,
            **changes,
        )

        return candidate, []

    @staticmethod
    def _permission_for_transition(
        work_item: WorkItem,
        target_state: WorkItemState | CodeReviewState,
        actor_role: AgentRole,
    ) -> WorkItemOperation | None:
        if work_item.work_item_type == WorkItemType.CODE_REVIEW_TASK:
            if target_state == CodeReviewState.RESOLVED:
                return WorkItemOperation.RESOLVE_CODE_REVIEW

            return WorkItemOperation.PERFORM_CODE_REVIEW

        if target_state == WorkItemState.BLOCKED:
            return WorkItemOperation.BLOCK

        if target_state == WorkItemState.REMOVED:
            return WorkItemOperation.REMOVE

        if work_item.state == WorkItemState.BLOCKED:
            return WorkItemOperation.UNBLOCK

        if target_state == WorkItemState.IN_TEST:
            if actor_role == AgentRole.WORK_ITEM_MANAGER:
                return WorkItemOperation.ENFORCE_WORKFLOW

            return WorkItemOperation.SUBMIT_FOR_TEST

        if target_state == WorkItemState.IN_WORK:
            if work_item.state in {
                WorkItemState.PROPOSED,
                WorkItemState.RESOLVED,
            }:
                return WorkItemOperation.START_AUTHORIZED_WORK

        return None

    # ------------------------------------------------------------------
    # Readiness and test submission
    # ------------------------------------------------------------------

    def check_readiness(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        actor_role: AgentRole,
        *,
        implementation_complete: bool = False,
        changes_in_main: bool = False,
        main_build_available: bool = False,
        review_gates_satisfied: bool = False,
        review_results=None,
        security_gate_passed: bool = False,
        ci_gate_passed: bool = False,
    ) -> list[str]:
        errors = self._validate_collection_shape(work_items)

        if errors:
            return errors

        item = work_items.get(work_item_id)

        if item is None:
            return [
                f"Work item '{work_item_id}' does not exist."
            ]

        return self._readiness_rules.validate_readiness(
            item,
            work_items,
            actor_role,
            implementation_complete=implementation_complete,
            changes_in_main=changes_in_main,
            main_build_available=main_build_available,
            review_gates_satisfied=review_gates_satisfied,
            review_results=review_results,
            security_gate_passed=security_gate_passed,
            ci_gate_passed=ci_gate_passed,
        )

    def submit_for_test(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        actor_role: AgentRole,
        *,
        implementation_complete: bool = False,
        changes_in_main: bool = False,
        main_build_available: bool = False,
        review_gates_satisfied: bool = False,
        review_results=None,
        security_gate_passed: bool = False,
        ci_gate_passed: bool = False,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        errors = self.check_readiness(
            work_items,
            work_item_id,
            actor_role,
            implementation_complete=implementation_complete,
            changes_in_main=changes_in_main,
            main_build_available=main_build_available,
            review_gates_satisfied=review_gates_satisfied,
            review_results=review_results,
            security_gate_passed=security_gate_passed,
            ci_gate_passed=ci_gate_passed,
        )

        if errors:
            return None, errors

        item = work_items[work_item_id]

        if item.work_item_type in {
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemType.SUPPORTING_TASK,
            WorkItemType.BUG,
            WorkItemType.CHANGE_REQUEST,
        } and actor_role != AgentRole.DEVELOPER:
            return None, [
                "Only the Developer may submit implementation "
                "work for testing."
            ]

        return self._transition_state(
            work_items,
            work_item_id,
            WorkItemState.IN_TEST,
            actor_role,
            implementation_ready=True,
        )

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def check_resolution(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        actor_role: AgentRole,
        *,
        verification_passed: bool = False,
        acceptance_criteria_met: bool = False,
        passed_test_case_ids=frozenset(),
        review_results=None,
        security_gate_passed: bool = False,
        ci_gate_passed: bool = False,
    ) -> list[str]:
        errors = self._validate_collection_shape(work_items)

        if errors:
            return errors

        item = work_items.get(work_item_id)

        if item is None:
            return [
                f"Work item '{work_item_id}' does not exist."
            ]

        return self._resolution_rules.validate_resolution(
            item,
            work_items,
            actor_role,
            verification_passed=verification_passed,
            acceptance_criteria_met=acceptance_criteria_met,
            passed_test_case_ids=passed_test_case_ids,
            review_results=review_results,
            security_gate_passed=security_gate_passed,
            ci_gate_passed=ci_gate_passed,
        )

    def resolve_work_item(
        self,
        work_items: Mapping[str, WorkItem],
        work_item_id: str,
        actor_role: AgentRole,
        *,
        verification_passed: bool = False,
        acceptance_criteria_met: bool = False,
        passed_test_case_ids=frozenset(),
        review_results=None,
        security_gate_passed: bool = False,
        ci_gate_passed: bool = False,
        reason: str | None = None,
    ) -> tuple[dict[str, WorkItem] | None, list[str]]:
        errors = self.check_resolution(
            work_items,
            work_item_id,
            actor_role,
            verification_passed=verification_passed,
            acceptance_criteria_met=acceptance_criteria_met,
            passed_test_case_ids=passed_test_case_ids,
            review_results=review_results,
            security_gate_passed=security_gate_passed,
            ci_gate_passed=ci_gate_passed,
        )

        if errors:
            return None, errors

        return self._transition_state(
            work_items,
            work_item_id,
            WorkItemState.RESOLVED,
            actor_role,
            reason=reason,
            verification_passed=verification_passed,
            completion_criteria_met=acceptance_criteria_met,
        )
