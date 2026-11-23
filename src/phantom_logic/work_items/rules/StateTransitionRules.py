
from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemState import (
    CodeReviewState,
    WorkItemState,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.PermissionRules import AgentRole


class StateTransitionRules:
    """
    Validates work-item state transitions and role authorization.

    This class does not mutate work items. The Work Item Manager applies
    validated transitions, manages saved return states, and records
    significant changes through the central audit mechanism.

    Authorized Bug/Change Request propagation is a narrowly scoped
    Work Item Manager operation. It does not change the ordinary
    authority of QA over In Test -> In Work transitions.
    """

    STANDARD_TRANSITIONS = {
        (WorkItemState.PROPOSED, WorkItemState.IN_WORK),
        (WorkItemState.IN_WORK, WorkItemState.IN_TEST),
        (WorkItemState.IN_TEST, WorkItemState.IN_WORK),
        (WorkItemState.IN_TEST, WorkItemState.RESOLVED),

        (WorkItemState.PROPOSED, WorkItemState.BLOCKED),
        (WorkItemState.IN_WORK, WorkItemState.BLOCKED),
        (WorkItemState.IN_TEST, WorkItemState.BLOCKED),

        (WorkItemState.BLOCKED, WorkItemState.PROPOSED),
        (WorkItemState.BLOCKED, WorkItemState.IN_WORK),
        (WorkItemState.BLOCKED, WorkItemState.IN_TEST),

        (WorkItemState.PROPOSED, WorkItemState.REMOVED),
        (WorkItemState.IN_WORK, WorkItemState.REMOVED),
        (WorkItemState.IN_TEST, WorkItemState.REMOVED),
        (WorkItemState.BLOCKED, WorkItemState.REMOVED),

        (WorkItemState.RESOLVED, WorkItemState.IN_WORK),
    }

    CODE_REVIEW_TRANSITIONS = {
        (CodeReviewState.PROPOSED, CodeReviewState.IN_WORK),
        (CodeReviewState.IN_WORK, CodeReviewState.REVIEW),
        (CodeReviewState.REVIEW, CodeReviewState.IN_WORK),
        (CodeReviewState.REVIEW, CodeReviewState.RESOLVED),
    }

    AUTHORIZED_PROPAGATION_TYPES = {
        WorkItemType.BUG,
        WorkItemType.CHANGE_REQUEST,
    }

    PROPAGATION_TARGET_TYPES = {
        WorkItemType.BUG,
        WorkItemType.CHANGE_REQUEST,
        WorkItemType.REQUIREMENT,
        WorkItemType.USE_CASE,
        WorkItemType.FEATURE,
    }

    BLOCKABLE_ROLES = {
        AgentRole.PRODUCT_MANAGER,
        AgentRole.DEVELOPER,
        AgentRole.REVIEWER,
        AgentRole.QA,
    }

    def validate_transition(
        self,
        work_item: WorkItem,
        target_state: WorkItemState | CodeReviewState,
        actor_role: AgentRole,
        *,
        reason: str | None = None,
        previous_state: WorkItemState | None = None,
        work_authorized: bool = False,
        implementation_ready: bool = False,
        verification_passed: bool = False,
        completion_criteria_met: bool = False,
        review_approved: bool = False,
        authorized_propagation: bool = False,
        propagation_source_type: WorkItemType | None = None,
    ) -> list[str]:
        """
        Validate a requested state transition.

        authorized_propagation is reserved for the Work Item Manager's
        explicitly authorized Bug/Change Request propagation workflow.

        propagation_source_type identifies the originating Bug or Change
        Request. The Work Item Manager must independently validate its
        persisted authorization evidence before requesting this transition.

        work_authorized must be True for propagation. It represents the
        Work Item Manager's successful authorization check; it is not a
        substitute for validating the persisted authorization evidence.

        previous_state is required when unblocking an item. It must represent
        the state saved by the Work Item Manager when the item was blocked.
        """

        if not isinstance(work_item, WorkItem):
            return ["A valid WorkItem instance is required."]

        if not isinstance(actor_role, AgentRole):
            return ["A valid AgentRole is required."]

        if not self._has_valid_state_type(work_item):
            return [
                "The work item's current state does not match "
                "its work item type."
            ]

        if not self._has_valid_target_state_type(work_item, target_state):
            return [
                "The target state does not match the work item's lifecycle."
            ]

        propagation_errors = self._validate_propagation_context(
            work_item=work_item,
            target_state=target_state,
            actor_role=actor_role,
            work_authorized=work_authorized,
            authorized_propagation=authorized_propagation,
            propagation_source_type=propagation_source_type,
        )

        if propagation_errors:
            return propagation_errors

        current_state = work_item.state

        if current_state == target_state:
            return ["The work item is already in the requested state."]

        if work_item.work_item_type == WorkItemType.CODE_REVIEW_TASK:
            return self._validate_code_review_transition(
                current_state=current_state,
                target_state=target_state,
                actor_role=actor_role,
                reason=reason,
                review_approved=review_approved,
            )

        return self._validate_standard_transition(
            work_item=work_item,
            current_state=current_state,
            target_state=target_state,
            actor_role=actor_role,
            reason=reason,
            previous_state=previous_state,
            work_authorized=work_authorized,
            implementation_ready=implementation_ready,
            verification_passed=verification_passed,
            completion_criteria_met=completion_criteria_met,
            authorized_propagation=authorized_propagation,
        )

    def is_valid_transition(
        self,
        work_item: WorkItem,
        target_state: WorkItemState | CodeReviewState,
        actor_role: AgentRole,
        **context,
    ) -> bool:
        """Return True when the requested transition is permitted."""

        return not self.validate_transition(
            work_item,
            target_state,
            actor_role,
            **context,
        )

    @classmethod
    def _validate_propagation_context(
        cls,
        *,
        work_item: WorkItem,
        target_state: WorkItemState | CodeReviewState,
        actor_role: AgentRole,
        work_authorized: bool,
        authorized_propagation: bool,
        propagation_source_type: WorkItemType | None,
    ) -> list[str]:

        if not isinstance(authorized_propagation, bool):
            return ["Authorized propagation flag must be a boolean."]

        if not isinstance(work_authorized, bool):
            return ["Work authorization flag must be a boolean."]

        if not authorized_propagation:
            if propagation_source_type is not None:
                return [
                    "A propagation source type cannot be supplied "
                    "outside authorized propagation."
                ]

            return []

        if actor_role != AgentRole.WORK_ITEM_MANAGER:
            return [
                "Only the Work Item Manager may perform authorized "
                "Bug/Change Request propagation transitions."
            ]

        if not work_authorized:
            return [
                "Authorized propagation requires validated Product Manager "
                "authorization."
            ]

        if not isinstance(propagation_source_type, WorkItemType):
            return [
                "Authorized propagation requires a valid Bug or "
                "Change Request source type."
            ]

        if propagation_source_type not in cls.AUTHORIZED_PROPAGATION_TYPES:
            return [
                "Authorized propagation must originate from a Bug "
                "or Change Request."
            ]

        if work_item.work_item_type == WorkItemType.CODE_REVIEW_TASK:
            return [
                "Authorized Bug/Change Request propagation cannot "
                "change Code Review Task states."
            ]

        if target_state != WorkItemState.IN_WORK:
            return [
                "Authorized propagation can only transition work "
                "into In Work."
            ]

        if work_item.work_item_type not in cls.PROPAGATION_TARGET_TYPES:
            return [
                f"Authorized propagation cannot transition "
                f"'{work_item.work_item_type.value}'."
            ]

        return []

    def _validate_standard_transition(
        self,
        *,
        work_item: WorkItem,
        current_state: WorkItemState,
        target_state: WorkItemState,
        actor_role: AgentRole,
        reason: str | None,
        previous_state: WorkItemState | None,
        work_authorized: bool,
        implementation_ready: bool,
        verification_passed: bool,
        completion_criteria_met: bool,
        authorized_propagation: bool,
    ) -> list[str]:

        errors: list[str] = []

        transition = (current_state, target_state)

        if transition not in self.STANDARD_TRANSITIONS:
            return [
                f"Transition from '{current_state.value}' to "
                f"'{target_state.value}' is not allowed."
            ]

        # Unblocking is exclusively managed by the Work Item Manager.
        # Authorized propagation preserves Blocked state and updates
        # blocked_return_state in the Work Item Manager instead.
        if current_state == WorkItemState.BLOCKED:
            if authorized_propagation:
                return [
                    "Authorized propagation must preserve Blocked state. "
                    "Update the saved return state instead of unblocking."
                ]

            if actor_role != AgentRole.WORK_ITEM_MANAGER:
                return [
                    "Only the Work Item Manager may unblock work."
                ]

            if previous_state != target_state:
                return [
                    "The target state must match the state saved when "
                    "the work item was blocked."
                ]

            if target_state not in {
                WorkItemState.PROPOSED,
                WorkItemState.IN_WORK,
                WorkItemState.IN_TEST,
            }:
                return ["The saved return state is not valid."]

            if not self._has_reason(reason):
                return [
                    "A reason is required when unblocking work."
                ]

            return []

        if target_state == WorkItemState.IN_WORK:

            if current_state == WorkItemState.PROPOSED:
                if authorized_propagation:
                    pass
                else:
                    if actor_role not in {
                        AgentRole.PRODUCT_MANAGER,
                        AgentRole.WORK_ITEM_MANAGER,
                    }:
                        errors.append(
                            "Only the Product Manager or Work Item Manager "
                            "may start proposed work."
                        )

                    if not work_authorized:
                        errors.append(
                            "Work must be explicitly authorized before it "
                            "can enter In Work."
                        )

            elif current_state == WorkItemState.IN_TEST:
                if authorized_propagation:
                    pass
                elif actor_role != AgentRole.QA:
                    errors.append(
                        "Only QA may return work from In Test to In Work."
                    )

            elif current_state == WorkItemState.RESOLVED:
                if authorized_propagation:
                    pass
                else:
                    if actor_role not in {
                        AgentRole.PRODUCT_MANAGER,
                        AgentRole.WORK_ITEM_MANAGER,
                    }:
                        errors.append(
                            "Only the Product Manager or Work Item Manager "
                            "may reopen resolved work."
                        )

                    if not work_authorized:
                        errors.append(
                            "Reopening resolved work requires explicit "
                            "Product Manager authorization."
                        )

        elif target_state == WorkItemState.IN_TEST:
            if actor_role not in {
                AgentRole.DEVELOPER,
                AgentRole.WORK_ITEM_MANAGER,
            }:
                errors.append(
                    "Only the Developer or Work Item Manager may move "
                    "work into In Test."
                )

            if not implementation_ready:
                errors.append(
                    "Implementation and required merge gates must be "
                    "complete before work enters In Test."
                )

        elif target_state == WorkItemState.RESOLVED:
            if actor_role != AgentRole.QA:
                errors.append(
                    "Only QA may resolve standard work items."
                )

            if not verification_passed:
                errors.append(
                    "Successful QA verification is required for resolution."
                )

            if not completion_criteria_met:
                errors.append(
                    "All work-item completion criteria must be satisfied."
                )

        elif target_state == WorkItemState.BLOCKED:
            if actor_role not in self.BLOCKABLE_ROLES:
                errors.append(
                    "This role is not permitted to block work items."
                )

            if not self._has_reason(reason):
                errors.append(
                    "A non-empty reason is required when blocking work."
                )

        elif target_state == WorkItemState.REMOVED:
            if actor_role != AgentRole.PRODUCT_MANAGER:
                errors.append(
                    "Only the Product Manager may remove work items."
                )

            if not self._has_reason(reason):
                errors.append(
                    "A non-empty reason is required when removing work."
                )

        return errors

    def _validate_code_review_transition(
        self,
        *,
        current_state: CodeReviewState,
        target_state: CodeReviewState,
        actor_role: AgentRole,
        reason: str | None,
        review_approved: bool,
    ) -> list[str]:

        transition = (current_state, target_state)

        if transition not in self.CODE_REVIEW_TRANSITIONS:
            return [
                f"Code Review Task transition from '{current_state.value}' "
                f"to '{target_state.value}' is not allowed."
            ]

        if actor_role != AgentRole.REVIEWER:
            return [
                "Only the Reviewer may manage Code Review Task states."
            ]

        if target_state == CodeReviewState.IN_WORK:
            if current_state == CodeReviewState.REVIEW:
                if not self._has_reason(reason):
                    return [
                        "A reason is required when returning a review "
                        "for changes."
                    ]

        elif target_state == CodeReviewState.REVIEW:
            if current_state != CodeReviewState.IN_WORK:
                return [
                    "A Code Review Task must be In Work before "
                    "entering Review."
                ]

        elif target_state == CodeReviewState.RESOLVED:
            if not review_approved:
                return [
                    "A Code Review Task can only be resolved after approval."
                ]

        return []

    @staticmethod
    def _has_valid_state_type(work_item: WorkItem) -> bool:
        if work_item.work_item_type == WorkItemType.CODE_REVIEW_TASK:
            return isinstance(work_item.state, CodeReviewState)

        return isinstance(work_item.state, WorkItemState)

    @staticmethod
    def _has_valid_target_state_type(
        work_item: WorkItem,
        target_state: WorkItemState | CodeReviewState,
    ) -> bool:
        if work_item.work_item_type == WorkItemType.CODE_REVIEW_TASK:
            return isinstance(target_state, CodeReviewState)

        return isinstance(target_state, WorkItemState)

    @staticmethod
    def _has_reason(reason: str | None) -> bool:
        return isinstance(reason, str) and bool(reason.strip())
