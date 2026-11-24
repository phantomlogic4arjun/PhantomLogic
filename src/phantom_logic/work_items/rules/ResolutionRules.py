
from collections.abc import Mapping, Set

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


class ResolutionRules:
    """
    Deterministically evaluates whether a work item is eligible for resolution.

    This component does not change work-item states or certify evidence.
    The Work Item Manager applies transitions after validating the supplied
    QA, review, security, CI, and hierarchy evidence.

    Parent-child relationships are stored on the parent WorkItem:
        source_id = parent ID
        target_id = child ID
    """

    ACTIVE_STATES = frozenset({
        WorkItemState.PROPOSED,
        WorkItemState.IN_WORK,
        WorkItemState.IN_TEST,
        WorkItemState.BLOCKED,
    })

    def validate_resolution(
        self,
        work_item: WorkItem,
        work_items: Mapping[str, WorkItem],
        actor_role: AgentRole,
        *,
        verification_passed: bool = False,
        acceptance_criteria_met: bool = False,
        passed_test_case_ids: Set[str] | frozenset[str] = frozenset(),
        review_results: Mapping[str, ReviewResult] | None = None,
        security_gate_passed: bool = False,
        ci_gate_passed: bool = False,
    ) -> list[str]:
        """
        Validate whether a work item may enter Resolved.

        Returns an empty list when all applicable conditions are satisfied.

        passed_test_case_ids:
            IDs of Test Cases whose latest authoritative QA result is Passed.

        review_results:
            Mapping of Code Review Task IDs to their recorded ReviewResult.

        The Work Item Manager must supply evidence from authoritative sources.
        """

        if not isinstance(work_item, WorkItem):
            return ["A valid WorkItem instance is required."]

        if not isinstance(actor_role, AgentRole):
            return ["A valid AgentRole is required."]

        if actor_role != AgentRole.QA:
            return ["Only QA may authorize standard work-item resolution."]

        if work_item.work_item_type == WorkItemType.CODE_REVIEW_TASK:
            return [
                "Code Review Tasks use their separate Reviewer-owned "
                "resolution lifecycle."
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

        if work_item.state != WorkItemState.IN_TEST:
            return [
                "A standard work item must be In Test before it can be resolved."
            ]

        if not verification_passed:
            errors.append("Successful QA verification is required.")

        if not acceptance_criteria_met:
            errors.append(
                "All applicable acceptance criteria must be satisfied."
            )

        if not isinstance(passed_test_case_ids, Set):
            errors.append(
                "Passed Test Case IDs must be supplied as a set."
            )

        if review_results is None:
            review_results = {}
        elif not isinstance(review_results, Mapping):
            errors.append(
                "Review results must be supplied as a mapping."
            )
            review_results = {}

        if errors:
            return errors

        if work_item.work_item_type == WorkItemType.TEST_CASE:
            self._validate_test_case(
                work_item,
                work_items,
                passed_test_case_ids,
                errors,
            )

        elif work_item.work_item_type == WorkItemType.REQUIREMENT:
            self._validate_requirement(
                work_item,
                work_items,
                passed_test_case_ids,
                errors,
            )

        elif work_item.work_item_type == WorkItemType.USE_CASE:
            self._validate_use_case(
                work_item,
                work_items,
                errors,
            )

        elif work_item.work_item_type == WorkItemType.FEATURE:
            self._validate_feature(
                work_item,
                work_items,
                review_results,
                security_gate_passed,
                ci_gate_passed,
                errors,
            )

        elif work_item.work_item_type == WorkItemType.BUG:
            self._validate_bug(
                work_item,
                work_items,
                errors,
            )

        elif work_item.work_item_type == WorkItemType.CHANGE_REQUEST:
            self._validate_change_request(
                work_item,
                work_items,
                errors,
            )

        elif work_item.work_item_type in {
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemType.SUPPORTING_TASK,
        }:
            pass

        elif work_item.work_item_type == WorkItemType.EPIC:
            self._validate_epic(
                work_item,
                work_items,
                errors,
            )

        else:
            errors.append(
                f"Resolution rules are not defined for "
                f"'{work_item.work_item_type.value}'."
            )

        return errors

    def is_resolvable(
        self,
        work_item: WorkItem,
        work_items: Mapping[str, WorkItem],
        actor_role: AgentRole,
        **context,
    ) -> bool:
        """Return True when the work item satisfies all resolution rules."""

        return not self.validate_resolution(
            work_item,
            work_items,
            actor_role,
            **context,
        )

    # ---------------------------------------------------------
    # Requirement
    # ---------------------------------------------------------

    def _validate_requirement(
        self,
        requirement: WorkItem,
        work_items: Mapping[str, WorkItem],
        passed_test_case_ids: Set[str] | frozenset[str],
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
        else:
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
            elif development_tasks[0].state != WorkItemState.RESOLVED:
                errors.append(
                    "The Use Case's Development Task must be Resolved "
                    "before its Requirements can be resolved."
                )

        test_cases = self._children_of_type(
            requirement,
            work_items,
            WorkItemType.TEST_CASE,
        )

        if not test_cases:
            errors.append(
                "A Requirement must have at least one associated Test Case."
            )

        for test_case in test_cases:
            if test_case.state != WorkItemState.RESOLVED:
                errors.append(
                    f"Test Case '{test_case.id}' must be Resolved."
                )

            if test_case.id not in passed_test_case_ids:
                errors.append(
                    f"Test Case '{test_case.id}' must have a Passed QA result."
                )

        for related_item in work_items.values():
            if not self._is_active(related_item):
                continue

            if related_item.work_item_type == WorkItemType.BUG:
                if self._has_relationship(
                    related_item,
                    requirement.id,
                    RelationshipType.VIOLATED_REQUIREMENT,
                ):
                    errors.append(
                        f"Active Bug '{related_item.id}' violates this "
                        "Requirement and must be resolved first."
                    )

            elif related_item.work_item_type == WorkItemType.CHANGE_REQUEST:
                if self._has_relationship(
                    related_item,
                    requirement.id,
                    RelationshipType.AFFECTED_REQUIREMENT,
                ):
                    errors.append(
                        f"Active Change Request '{related_item.id}' affects "
                        "this Requirement and must be resolved first."
                    )

    # ---------------------------------------------------------
    # Use Case
    # ---------------------------------------------------------

    def _validate_use_case(
        self,
        use_case: WorkItem,
        work_items: Mapping[str, WorkItem],
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
            if requirement.state != WorkItemState.RESOLVED:
                errors.append(
                    f"Requirement '{requirement.id}' must be Resolved."
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
        elif development_tasks[0].state != WorkItemState.RESOLVED:
            errors.append(
                "The Use Case's Development Task must be Resolved."
            )

    # ---------------------------------------------------------
    # Feature
    # ---------------------------------------------------------

    def _validate_feature(
        self,
        feature: WorkItem,
        work_items: Mapping[str, WorkItem],
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
            if use_case.state != WorkItemState.RESOLVED:
                errors.append(
                    f"Use Case '{use_case.id}' must be Resolved."
                )

        supporting_tasks = self._children_of_type(
            feature,
            work_items,
            WorkItemType.SUPPORTING_TASK,
        )

        for task in supporting_tasks:
            if task.state != WorkItemState.RESOLVED:
                errors.append(
                    f"Supporting Task '{task.id}' must be Resolved."
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
                    "The Feature's Code Review Task must have an "
                    "Approved review result."
                )

        if not security_gate_passed:
            errors.append(
                "The required security gate must have passed."
            )

        if not ci_gate_passed:
            errors.append(
                "The required CI gate must have passed."
            )

        for related_item in work_items.values():
            if (
                related_item.work_item_type == WorkItemType.BUG
                and self._is_active(related_item)
                and self._affects_feature(
                    related_item,
                    feature,
                    work_items,
                    RelationshipType.VIOLATED_REQUIREMENT,
                )
            ):
                errors.append(
                    f"Active Bug '{related_item.id}' affects this Feature "
                    "and must be resolved first."
                )

    # ---------------------------------------------------------
    # Bug
    # ---------------------------------------------------------

    def _validate_bug(
        self,
        bug: WorkItem,
        work_items: Mapping[str, WorkItem],
        errors: list[str],
    ) -> None:
        violated_requirement_ids = self._related_items(
            bug,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        if not violated_requirement_ids:
            errors.append(
                "A Bug must reference at least one violated Requirement."
            )

        for requirement_id in violated_requirement_ids:
            requirement = work_items.get(requirement_id)

            if requirement is None:
                errors.append(
                    f"Bug references missing Requirement '{requirement_id}'."
                )
            elif requirement.work_item_type != WorkItemType.REQUIREMENT:
                errors.append(
                    f"Bug relationship target '{requirement_id}' "
                    "is not a Requirement."
                )

        failed_test_case_ids = self._related_items(
            bug,
            RelationshipType.FAILED_TEST_CASE,
        )

        # A failed Test Case is required only when the Bug originated
        # from a failed Test Case. The relationship is optional otherwise.
        for test_case_id in failed_test_case_ids:
            test_case = work_items.get(test_case_id)

            if test_case is None:
                errors.append(
                    f"Bug references missing Test Case '{test_case_id}'."
                )
            elif test_case.work_item_type != WorkItemType.TEST_CASE:
                errors.append(
                    f"Bug relationship target '{test_case_id}' "
                    "is not a Test Case."
                )

    # ---------------------------------------------------------
    # Change Request
    # ---------------------------------------------------------

    def _validate_change_request(
        self,
        change_request: WorkItem,
        work_items: Mapping[str, WorkItem],
        errors: list[str],
    ) -> None:
        affected_requirement_ids = self._related_items(
            change_request,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        if not affected_requirement_ids:
            errors.append(
                "A Change Request must reference at least one "
                "affected Requirement."
            )

        for requirement_id in affected_requirement_ids:
            requirement = work_items.get(requirement_id)

            if requirement is None:
                errors.append(
                    f"Change Request references missing Requirement "
                    f"'{requirement_id}'."
                )
            elif requirement.work_item_type != WorkItemType.REQUIREMENT:
                errors.append(
                    f"Change Request relationship target '{requirement_id}' "
                    "is not a Requirement."
                )

    # ---------------------------------------------------------
    # Epic
    # ---------------------------------------------------------

    def _validate_epic(
        self,
        epic: WorkItem,
        work_items: Mapping[str, WorkItem],
        errors: list[str],
    ) -> None:
        features = self._children_of_type(
            epic,
            work_items,
            WorkItemType.FEATURE,
        )

        if not features:
            errors.append(
                "An Epic must contain at least one Feature."
            )

        for feature in features:
            if feature.state != WorkItemState.RESOLVED:
                errors.append(
                    f"Feature '{feature.id}' must be Resolved."
                )

    # ---------------------------------------------------------
    # Test Case
    # ---------------------------------------------------------

    def _validate_test_case(
        self,
        test_case: WorkItem,
        work_items: Mapping[str, WorkItem],
        passed_test_case_ids: Set[str] | frozenset[str],
        errors: list[str],
    ) -> None:
        if test_case.id not in passed_test_case_ids:
            errors.append(
                "A Test Case can only be resolved when its QA result is Passed."
            )

        requirement = self._parent_of_type(
            test_case,
            work_items,
            WorkItemType.REQUIREMENT,
        )

        if requirement is None:
            errors.append(
                "A Test Case must belong to exactly one Requirement."
            )

    # ---------------------------------------------------------
    # Relationship and collection helpers
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

    @staticmethod
    def _has_relationship(
        source: WorkItem,
        target_id: str,
        relationship_type: RelationshipType,
    ) -> bool:
        return any(
            relationship.source_id == source.id
            and relationship.target_id == target_id
            and relationship.relationship_type == relationship_type
            for relationship in source.relationships
        )

    @classmethod
    def _affects_feature(
        cls,
        bug: WorkItem,
        feature: WorkItem,
        work_items: Mapping[str, WorkItem],
        relationship_type: RelationshipType,
    ) -> bool:
        requirement_ids = cls._related_items(
            bug,
            relationship_type,
        )

        for requirement_id in requirement_ids:
            requirement = work_items.get(requirement_id)

            if (
                requirement is None
                or requirement.work_item_type != WorkItemType.REQUIREMENT
            ):
                continue

            use_case = cls._parent_of_type(
                requirement,
                work_items,
                WorkItemType.USE_CASE,
            )

            if use_case is None:
                continue

            parent_feature = cls._parent_of_type(
                use_case,
                work_items,
                WorkItemType.FEATURE,
            )

            if (
                parent_feature is not None
                and parent_feature.id == feature.id
            ):
                return True

        return False

    @classmethod
    def _is_active(cls, work_item: WorkItem) -> bool:
        return (
            isinstance(work_item.state, WorkItemState)
            and work_item.state in cls.ACTIVE_STATES
        )
