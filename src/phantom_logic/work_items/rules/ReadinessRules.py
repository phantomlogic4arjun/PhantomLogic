

from collections.abc import Mapping

from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
)
from phantom_logic.work_items.models.WorkItemState import (
    CodeReviewState,
    ReviewResult,
    WorkItemState,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.PermissionRules import AgentRole


class ReadinessRules:
    """
    Deterministically evaluates whether a work item is ready to enter In Test.

    This component does not mutate work items or perform QA.

    The Work Item Manager is responsible for:
    - Obtaining authoritative build, merge, review, security, and CI evidence.
    - Calling these rules with that evidence.
    - Applying the state transition when validation succeeds.

    Parent-child relationships are stored on the parent WorkItem:
        source_id = parent ID
        target_id = child ID
    """

    READY_PARENT_STATES = frozenset({
        WorkItemState.IN_TEST,
        WorkItemState.RESOLVED,
    })

    READY_TASK_STATES = frozenset({
        WorkItemState.IN_TEST,
        WorkItemState.RESOLVED,
    })

    def validate_readiness(
        self,
        work_item: WorkItem,
        work_items: Mapping[str, WorkItem],
        actor_role: AgentRole,
        *,
        implementation_complete: bool = False,
        changes_in_main: bool = False,
        main_build_available: bool = False,
        review_gates_satisfied: bool = False,
        review_results: Mapping[str, ReviewResult] | None = None,
        security_gate_passed: bool = False,
        ci_gate_passed: bool = False,
    ) -> list[str]:
        """
        Validate whether a work item may transition from In Work to In Test.

        Evidence parameters must be supplied by the Work Item Manager from
        authoritative sources.

        changes_in_main:
            Relevant changes have been merged into the protected main branch.

        main_build_available:
            A build generated from main containing the relevant changes exists.

        review_gates_satisfied:
            All applicable code-review and merge gates have been satisfied.

        review_results:
            Mapping of Feature-level Code Review Task IDs to ReviewResult.
        """

        if not isinstance(work_item, WorkItem):
            return ["A valid WorkItem instance is required."]

        if not isinstance(actor_role, AgentRole):
            return ["A valid AgentRole is required."]

        if actor_role != AgentRole.WORK_ITEM_MANAGER:
            return [
                "Only the Work Item Manager may authorize readiness "
                "transitions into In Test."
            ]

        # Code Review Tasks use their separate Reviewer-owned lifecycle.
        # Check this before standard WorkItemState validation because
        # CodeReviewTask uses CodeReviewState.
        if work_item.work_item_type == WorkItemType.CODE_REVIEW_TASK:
            return [
                "Code Review Tasks use their separate Reviewer-owned lifecycle "
                "and do not enter In Test."
            ]

        if not isinstance(work_items, Mapping):
            return [
                "Work items must be supplied as an ID-to-WorkItem mapping."
            ]

        errors = self._validate_collection(work_items)

        if errors:
            return errors

        if work_item.id not in work_items:
            return [
                "The work item must exist in the supplied work-item collection."
            ]

        if work_items[work_item.id] is not work_item:
            return [
                "The supplied work item must be the same instance "
                "stored in the work-item collection."
            ]

        if not isinstance(work_item.state, WorkItemState):
            return [
                "The work item has an invalid standard lifecycle state."
            ]

        if work_item.state != WorkItemState.IN_WORK:
            return [
                "A work item must be In Work before it can enter In Test."
            ]

        if review_results is None:
            review_results = {}
        elif not isinstance(review_results, Mapping):
            return [
                "Review results must be supplied as a mapping."
            ]

        boolean_evidence = {
            "implementation_complete": implementation_complete,
            "changes_in_main": changes_in_main,
            "main_build_available": main_build_available,
            "review_gates_satisfied": review_gates_satisfied,
            "security_gate_passed": security_gate_passed,
            "ci_gate_passed": ci_gate_passed,
        }

        for evidence_name, evidence_value in boolean_evidence.items():
            if not isinstance(evidence_value, bool):
                errors.append(
                    f"{evidence_name} evidence must be boolean."
                )

        if errors:
            return errors

        if work_item.work_item_type in {
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemType.SUPPORTING_TASK,
        }:
            self._validate_task_readiness(
                implementation_complete,
                changes_in_main,
                main_build_available,
                review_gates_satisfied,
                errors,
            )

        elif work_item.work_item_type == WorkItemType.REQUIREMENT:
            self._validate_requirement_readiness(
                work_item,
                work_items,
                changes_in_main,
                main_build_available,
                review_gates_satisfied,
                errors,
            )

        elif work_item.work_item_type == WorkItemType.USE_CASE:
            self._validate_use_case_readiness(
                work_item,
                work_items,
                changes_in_main,
                main_build_available,
                review_gates_satisfied,
                errors,
            )

        elif work_item.work_item_type == WorkItemType.FEATURE:
            self._validate_feature_readiness(
                work_item,
                work_items,
                changes_in_main,
                main_build_available,
                review_gates_satisfied,
                review_results,
                security_gate_passed,
                ci_gate_passed,
                errors,
            )

        elif work_item.work_item_type in {
            WorkItemType.BUG,
            WorkItemType.CHANGE_REQUEST,
        }:
            self._validate_change_readiness(
                work_item,
                work_items,
                changes_in_main,
                main_build_available,
                review_gates_satisfied,
                errors,
            )

        elif work_item.work_item_type in {
            WorkItemType.EPIC,
            WorkItemType.TEST_CASE,
        }:
            errors.append(
                f"'{work_item.work_item_type.value}' does not have "
                "an independent In Test readiness transition."
            )

        else:
            errors.append(
                f"Readiness rules are not defined for "
                f"'{work_item.work_item_type.value}'."
            )

        return errors

    def is_ready(
        self,
        work_item: WorkItem,
        work_items: Mapping[str, WorkItem],
        actor_role: AgentRole,
        **context,
    ) -> bool:
        """Return True when the work item satisfies all readiness rules."""

        return not self.validate_readiness(
            work_item,
            work_items,
            actor_role,
            **context,
        )

    # ---------------------------------------------------------
    # Development Task and Supporting Task
    # ---------------------------------------------------------

    @staticmethod
    def _validate_task_readiness(
        implementation_complete: bool,
        changes_in_main: bool,
        main_build_available: bool,
        review_gates_satisfied: bool,
        errors: list[str],
    ) -> None:
        if not implementation_complete:
            errors.append(
                "The task implementation must be complete."
            )

        if not changes_in_main:
            errors.append(
                "The task's changes must be merged into main."
            )

        if not main_build_available:
            errors.append(
                "A build containing the task's changes from main must exist."
            )

        if not review_gates_satisfied:
            errors.append(
                "All applicable review and merge gates must be satisfied."
            )

    # ---------------------------------------------------------
    # Requirement
    # ---------------------------------------------------------

    def _validate_requirement_readiness(
        self,
        requirement: WorkItem,
        work_items: Mapping[str, WorkItem],
        changes_in_main: bool,
        main_build_available: bool,
        review_gates_satisfied: bool,
        errors: list[str],
    ) -> None:
        use_case = self._parent_of_type(
            requirement,
            work_items,
            WorkItemType.USE_CASE,
        )

        if use_case is None:
            errors.append(
                "The Requirement must belong to exactly one Use Case."
            )

        test_cases = self._children_of_type(
            requirement,
            work_items,
            WorkItemType.TEST_CASE,
        )

        if not requirement.acceptance_criteria:
            errors.append(
                "The Requirement must have acceptance criteria."
            )

        if not test_cases:
            errors.append(
                "The Requirement must have at least one associated Test Case."
            )

        if use_case is not None:
            development_tasks = self._children_of_type(
                use_case,
                work_items,
                WorkItemType.DEVELOPMENT_TASK,
            )

            if len(development_tasks) != 1:
                errors.append(
                    "The Requirement's Use Case must have exactly "
                    "one Development Task."
                )
            elif development_tasks[0].state not in self.READY_TASK_STATES:
                errors.append(
                    "The Use Case's Development Task must be In Test "
                    "or Resolved."
                )

        if not changes_in_main:
            errors.append(
                "The Requirement's implementation changes must be "
                "merged into main."
            )

        if not main_build_available:
            errors.append(
                "A main-branch build containing the Requirement's "
                "changes must be available."
            )

        if not review_gates_satisfied:
            errors.append(
                "All applicable code-review and merge gates must be satisfied."
            )

    # ---------------------------------------------------------
    # Use Case
    # ---------------------------------------------------------

    def _validate_use_case_readiness(
        self,
        use_case: WorkItem,
        work_items: Mapping[str, WorkItem],
        changes_in_main: bool,
        main_build_available: bool,
        review_gates_satisfied: bool,
        errors: list[str],
    ) -> None:
        requirements = self._children_of_type(
            use_case,
            work_items,
            WorkItemType.REQUIREMENT,
        )

        if not requirements:
            errors.append(
                "A Use Case must contain at least one Requirement."
            )

        for requirement in requirements:
            if requirement.state not in self.READY_PARENT_STATES:
                errors.append(
                    f"Requirement '{requirement.id}' must be In Test "
                    "or Resolved before the Use Case can enter In Test."
                )

        development_tasks = self._children_of_type(
            use_case,
            work_items,
            WorkItemType.DEVELOPMENT_TASK,
        )

        if len(development_tasks) != 1:
            errors.append(
                "A Use Case must have exactly one Development Task."
            )
        elif development_tasks[0].state not in self.READY_TASK_STATES:
            errors.append(
                "The Use Case's Development Task must be In Test "
                "or Resolved."
            )

        if not changes_in_main:
            errors.append(
                "The Use Case's changes must be merged into main."
            )

        if not main_build_available:
            errors.append(
                "A main-branch build containing the Use Case's "
                "changes must be available."
            )

        if not review_gates_satisfied:
            errors.append(
                "All applicable code-review and merge gates must be satisfied."
            )

    # ---------------------------------------------------------
    # Feature
    # ---------------------------------------------------------

    def _validate_feature_readiness(
        self,
        feature: WorkItem,
        work_items: Mapping[str, WorkItem],
        changes_in_main: bool,
        main_build_available: bool,
        review_gates_satisfied: bool,
        review_results: Mapping[str, ReviewResult],
        security_gate_passed: bool,
        ci_gate_passed: bool,
        errors: list[str],
    ) -> None:
        use_cases = self._children_of_type(
            feature,
            work_items,
            WorkItemType.USE_CASE,
        )

        if not use_cases:
            errors.append(
                "A Feature must contain at least one Use Case."
            )

        for use_case in use_cases:
            if use_case.state not in self.READY_PARENT_STATES:
                errors.append(
                    f"Use Case '{use_case.id}' must be In Test "
                    "or Resolved before the Feature can enter In Test."
                )

        supporting_tasks = self._children_of_type(
            feature,
            work_items,
            WorkItemType.SUPPORTING_TASK,
        )

        for task in supporting_tasks:
            if task.state not in self.READY_TASK_STATES:
                errors.append(
                    f"Supporting Task '{task.id}' must be In Test "
                    "or Resolved before the Feature can enter In Test."
                )

        review_tasks = self._children_of_type(
            feature,
            work_items,
            WorkItemType.CODE_REVIEW_TASK,
        )

        if len(review_tasks) != 1:
            errors.append(
                "A Feature must have exactly one Code Review Task."
            )
        else:
            review_task = review_tasks[0]

            if review_task.state != CodeReviewState.RESOLVED:
                errors.append(
                    "The Feature's Code Review Task must be Resolved."
                )

            if review_results.get(review_task.id) != ReviewResult.APPROVED:
                errors.append(
                    "The Feature's Code Review Task must have "
                    "an Approved review result."
                )

        if not changes_in_main:
            errors.append(
                "The Feature's changes must be merged into main."
            )

        if not main_build_available:
            errors.append(
                "A main-branch build containing the Feature's "
                "changes must be available."
            )

        if not review_gates_satisfied:
            errors.append(
                "All applicable code-review and merge gates must be satisfied."
            )

        if not security_gate_passed:
            errors.append(
                "The required security gate must have passed."
            )

        if not ci_gate_passed:
            errors.append(
                "The required CI gate must have passed."
            )

    # ---------------------------------------------------------
    # Bug and Change Request
    # ---------------------------------------------------------

    def _validate_change_readiness(
        self,
        work_item: WorkItem,
        work_items: Mapping[str, WorkItem],
        changes_in_main: bool,
        main_build_available: bool,
        review_gates_satisfied: bool,
        errors: list[str],
    ) -> None:
        if work_item.work_item_type == WorkItemType.BUG:
            relationship_type = RelationshipType.VIOLATED_REQUIREMENT
            target_type = WorkItemType.REQUIREMENT
            relationship_name = "violated Requirement"
        else:
            relationship_type = RelationshipType.AFFECTED_REQUIREMENT
            target_type = WorkItemType.REQUIREMENT
            relationship_name = "affected Requirement"

        related_ids = self._related_items(
            work_item,
            relationship_type,
        )

        if not related_ids:
            errors.append(
                f"The {work_item.work_item_type.value} must reference "
                f"at least one {relationship_name}."
            )

        for related_id in related_ids:
            related_item = work_items.get(related_id)

            if related_item is None:
                errors.append(
                    f"The work item references missing Requirement "
                    f"'{related_id}'."
                )
            elif related_item.work_item_type != target_type:
                errors.append(
                    f"Relationship target '{related_id}' must be "
                    f"a {target_type.value}."
                )

        if not changes_in_main:
            errors.append(
                "The fix or requested changes must be merged into main."
            )

        if not main_build_available:
            errors.append(
                "A main-branch build containing the fix or changes "
                "must be available."
            )

        if not review_gates_satisfied:
            errors.append(
                "All applicable code-review and merge gates must be satisfied."
            )

    # ---------------------------------------------------------
    # Collection and relationship helpers
    # ---------------------------------------------------------

    @staticmethod
    def _validate_collection(
        work_items: Mapping[str, WorkItem],
    ) -> list[str]:
        errors: list[str] = []

        for item_id, item in work_items.items():
            if not isinstance(item, WorkItem):
                errors.append(
                    f"Collection entry '{item_id}' is not a valid WorkItem."
                )
                continue

            if item_id != item.id:
                errors.append(
                    f"Collection key '{item_id}' does not match "
                    f"work item ID '{item.id}'."
                )

        return errors

    @staticmethod
    def _children_of_type(
        parent: WorkItem,
        work_items: Mapping[str, WorkItem],
        child_type: WorkItemType,
    ) -> list[WorkItem]:
        child_ids = {
            relationship.target_id
            for relationship in parent.relationships
            if relationship.source_id == parent.id
            and relationship.relationship_type
            == RelationshipType.PARENT_CHILD
        }

        return [
            item
            for item in work_items.values()
            if item.id in child_ids
            and item.work_item_type == child_type
        ]

    @staticmethod
    def _parent_of_type(
        child: WorkItem,
        work_items: Mapping[str, WorkItem],
        parent_type: WorkItemType,
    ) -> WorkItem | None:
        matching_parents = [
            item
            for item in work_items.values()
            if item.work_item_type == parent_type
            and any(
                relationship.source_id == item.id
                and relationship.target_id == child.id
                and relationship.relationship_type
                == RelationshipType.PARENT_CHILD
                for relationship in item.relationships
            )
        ]

        return (
            matching_parents[0]
            if len(matching_parents) == 1
            else None
        )

    @staticmethod
    def _related_items(
        work_item: WorkItem,
        relationship_type: RelationshipType,
    ) -> tuple[str, ...]:
        return tuple(
            relationship.target_id
            for relationship in work_item.relationships
            if relationship.source_id == work_item.id
            and relationship.relationship_type == relationship_type
        )
