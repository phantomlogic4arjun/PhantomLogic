
import unittest

from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from phantom_logic.work_items.models.WorkItemState import (
    CodeReviewState,
    ReviewResult,
    WorkItemState,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.PermissionRules import AgentRole
from phantom_logic.work_items.rules.ReadinessRules import ReadinessRules


class TestReadinessRules(unittest.TestCase):

    def setUp(self):
        self.rules = ReadinessRules()
        self.items = {}

        self.ready_context = {
            "implementation_complete": True,
            "changes_in_main": True,
            "main_build_available": True,
            "review_gates_satisfied": True,
        }

    # ---------------------------------------------------------
    # Test helpers
    # ---------------------------------------------------------

    def create_item(
        self,
        item_id,
        item_type,
        state=WorkItemState.IN_WORK,
        acceptance_criteria=(),
    ):
        item = WorkItem(
            id=item_id,
            title=f"Test {item_type.value}",
            work_item_type=item_type,
            created_by="ProductManager",
            state=state,
            acceptance_criteria=tuple(acceptance_criteria),
        )

        self.items[item_id] = item
        return item

    def add_child(self, parent, child):
        parent.relationships += (
            WorkItemRelationship(
                source_id=parent.id,
                target_id=child.id,
                relationship_type=RelationshipType.PARENT_CHILD,
            ),
        )

    def add_related_item(self, source, target, relationship_type):
        source.relationships += (
            WorkItemRelationship(
                source_id=source.id,
                target_id=target.id,
                relationship_type=relationship_type,
            ),
        )

    def validate(self, item, **context):
        effective_context = {
            **self.ready_context,
            **context,
        }

        return self.rules.validate_readiness(
            item,
            self.items,
            AgentRole.WORK_ITEM_MANAGER,
            **effective_context,
        )

    def assert_allowed(self, item, **context):
        self.assertEqual(
            [],
            self.validate(item, **context),
        )

    def assert_denied(self, item, **context):
        self.assertTrue(
            self.validate(item, **context)
        )

    def create_requirement_hierarchy(
        self,
        requirement_state=WorkItemState.IN_WORK,
        development_task_state=WorkItemState.IN_TEST,
    ):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            requirement_state,
            acceptance_criteria=("Acceptance criterion 1",),
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            development_task_state,
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
            WorkItemState.PROPOSED,
        )

        self.add_child(use_case, requirement)
        self.add_child(use_case, development_task)
        self.add_child(requirement, test_case)

        return use_case, requirement, development_task, test_case

    def create_feature_hierarchy(self):
        feature = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
        )

        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            WorkItemState.IN_TEST,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            WorkItemState.IN_TEST,
            acceptance_criteria=("Acceptance criterion 1",),
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
            WorkItemState.PROPOSED,
        )

        supporting_task = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
            WorkItemState.IN_TEST,
        )

        review_task = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            CodeReviewState.RESOLVED,
        )

        self.add_child(feature, use_case)
        self.add_child(feature, supporting_task)
        self.add_child(feature, review_task)
        self.add_child(use_case, requirement)
        self.add_child(use_case, development_task)
        self.add_child(requirement, test_case)

        return {
            "feature": feature,
            "use_case": use_case,
            "requirement": requirement,
            "development_task": development_task,
            "test_case": test_case,
            "supporting_task": supporting_task,
            "review_task": review_task,
        }

    # ---------------------------------------------------------
    # General validation
    # ---------------------------------------------------------

    def test_invalid_work_item_is_rejected(self):
        errors = self.rules.validate_readiness(
            None,
            {},
            AgentRole.WORK_ITEM_MANAGER,
        )

        self.assertTrue(errors)

    def test_invalid_actor_role_is_rejected(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        errors = self.rules.validate_readiness(
            item,
            self.items,
            "WORK_ITEM_MANAGER",
            **self.ready_context,
        )

        self.assertTrue(errors)

    def test_only_work_item_manager_can_authorize_readiness(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        errors = self.rules.validate_readiness(
            item,
            self.items,
            AgentRole.DEVELOPER,
            **self.ready_context,
        )

        self.assertTrue(errors)

    def test_non_mapping_collection_is_rejected(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        errors = self.rules.validate_readiness(
            item,
            [],
            AgentRole.WORK_ITEM_MANAGER,
            **self.ready_context,
        )

        self.assertTrue(errors)

    def test_collection_entry_must_be_work_item(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.items["INVALID"] = "not a work item"

        self.assert_denied(item)

    def test_collection_key_must_match_item_id(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.items["WRONG-ID"] = item

        self.assert_denied(item)

    def test_item_must_exist_in_collection(self):
        item = WorkItem(
            id="DEV-1",
            title="Development Task",
            work_item_type=WorkItemType.DEVELOPMENT_TASK,
            created_by="ProductManager",
            state=WorkItemState.IN_WORK,
        )

        errors = self.rules.validate_readiness(
            item,
            {},
            AgentRole.WORK_ITEM_MANAGER,
            **self.ready_context,
        )

        self.assertTrue(errors)

    def test_item_must_be_same_instance_as_collection_entry(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        duplicate = WorkItem(
            id=item.id,
            title=item.title,
            work_item_type=item.work_item_type,
            created_by=item.created_by,
            state=item.state,
        )

        errors = self.rules.validate_readiness(
            duplicate,
            self.items,
            AgentRole.WORK_ITEM_MANAGER,
            **self.ready_context,
        )

        self.assertTrue(errors)

    def test_item_must_be_in_work(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.PROPOSED,
        )

        self.assert_denied(item)

    def test_resolved_item_cannot_enter_in_test_again(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.RESOLVED,
        )

        self.assert_denied(item)

    def test_blocked_item_cannot_enter_in_test(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.BLOCKED,
        )

        self.assert_denied(item)

    def test_implementation_evidence_must_be_boolean(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_denied(
            item,
            implementation_complete="yes",
        )

    def test_changes_in_main_evidence_must_be_boolean(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_denied(
            item,
            changes_in_main="yes",
        )

    def test_main_build_evidence_must_be_boolean(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_denied(
            item,
            main_build_available="yes",
        )

    def test_review_gate_evidence_must_be_boolean(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_denied(
            item,
            review_gates_satisfied="yes",
        )

    def test_security_gate_evidence_must_be_boolean(self):
        item = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
        )

        self.assert_denied(
            item,
            security_gate_passed="yes",
        )

    def test_ci_gate_evidence_must_be_boolean(self):
        item = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
        )

        self.assert_denied(
            item,
            ci_gate_passed="yes",
        )

    def test_review_results_must_be_mapping(self):
        item = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
        )

        self.assert_denied(
            item,
            review_results=[],
        )

    def test_code_review_task_uses_separate_lifecycle(self):
        item = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            CodeReviewState.IN_WORK,
        )

        self.assert_denied(item)

    def test_epic_does_not_enter_in_test(self):
        item = self.create_item(
            "EPIC-1",
            WorkItemType.EPIC,
        )

        self.assert_denied(item)

    def test_test_case_does_not_enter_in_test_independently(self):
        item = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        self.assert_denied(item)

    def test_is_ready_returns_true_for_eligible_item(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assertIs(
            self.rules.is_ready(
                item,
                self.items,
                AgentRole.WORK_ITEM_MANAGER,
                **self.ready_context,
            ),
            True,
        )

    def test_is_ready_returns_false_for_ineligible_item(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assertIs(
            self.rules.is_ready(
                item,
                self.items,
                AgentRole.WORK_ITEM_MANAGER,
                implementation_complete=False,
                changes_in_main=True,
                main_build_available=True,
                review_gates_satisfied=True,
            ),
            False,
        )

    # ---------------------------------------------------------
    # Development Task and Supporting Task
    # ---------------------------------------------------------

    def test_development_task_can_enter_in_test(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_allowed(item)

    def test_supporting_task_can_enter_in_test(self):
        item = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
        )

        self.assert_allowed(item)

    def test_task_requires_implementation_complete(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_denied(
            item,
            implementation_complete=False,
        )

    def test_task_requires_changes_in_main(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_denied(
            item,
            changes_in_main=False,
        )

    def test_task_requires_main_build(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_denied(
            item,
            main_build_available=False,
        )

    def test_task_requires_review_and_merge_gates(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.assert_denied(
            item,
            review_gates_satisfied=False,
        )

    # ---------------------------------------------------------
    # Requirement
    # ---------------------------------------------------------

    def test_requirement_can_enter_in_test_when_ready(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        self.assert_allowed(requirement)

    def test_requirement_requires_use_case_parent(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            acceptance_criteria=("Acceptance criterion 1",),
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        self.add_child(requirement, test_case)

        self.assert_denied(requirement)

    def test_requirement_requires_acceptance_criteria(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        self.add_child(use_case, requirement)
        self.add_child(use_case, development_task)
        self.add_child(requirement, test_case)

        self.assert_denied(requirement)

    def test_requirement_requires_at_least_one_test_case(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            acceptance_criteria=("Acceptance criterion 1",),
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.add_child(use_case, requirement)
        self.add_child(use_case, development_task)

        self.assert_denied(requirement)

    def test_requirement_requires_exactly_one_development_task(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            acceptance_criteria=("Acceptance criterion 1",),
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        self.add_child(use_case, requirement)
        self.add_child(requirement, test_case)

        self.assert_denied(requirement)

    def test_requirement_requires_development_task_in_test_or_resolved(self):
        _, requirement, development_task, _ = (
            self.create_requirement_hierarchy(
                development_task_state=WorkItemState.IN_WORK,
            )
        )

        self.assert_denied(requirement)

    def test_requirement_accepts_resolved_development_task(self):
        _, requirement, _, _ = self.create_requirement_hierarchy(
            development_task_state=WorkItemState.RESOLVED,
        )

        self.assert_allowed(requirement)

    def test_requirement_requires_changes_in_main(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        self.assert_denied(
            requirement,
            changes_in_main=False,
        )

    def test_requirement_requires_main_build(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        self.assert_denied(
            requirement,
            main_build_available=False,
        )

    def test_requirement_requires_review_gates(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        self.assert_denied(
            requirement,
            review_gates_satisfied=False,
        )

    # ---------------------------------------------------------
    # Use Case
    # ---------------------------------------------------------

    def test_use_case_can_enter_in_test_when_ready(self):
        use_case, _, _, _ = self.create_requirement_hierarchy(
            requirement_state = WorkItemState.IN_TEST,
        )

        self.assert_allowed(use_case)

    def test_use_case_requires_requirements(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.add_child(use_case, development_task)

        self.assert_denied(use_case)

    def test_use_case_requires_all_requirements_in_test_or_resolved(self):
        use_case, requirement, _, _ = self.create_requirement_hierarchy(
            requirement_state=WorkItemState.IN_WORK,
        )

        self.assert_denied(use_case)

    def test_use_case_accepts_resolved_requirements(self):
        use_case, requirement, _, _ = self.create_requirement_hierarchy(
            requirement_state=WorkItemState.RESOLVED,
        )

        self.assert_allowed(use_case)

    def test_use_case_requires_exactly_one_development_task(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            WorkItemState.IN_TEST,
            acceptance_criteria=("Acceptance criterion 1",),
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        self.add_child(use_case, requirement)
        self.add_child(requirement, test_case)

        self.assert_denied(use_case)

    def test_use_case_requires_development_task_in_test_or_resolved(self):
        use_case, _, _, _ = self.create_requirement_hierarchy(
            development_task_state=WorkItemState.IN_WORK,
        )

        self.assert_denied(use_case)

    def test_use_case_accepts_resolved_development_task(self):
        use_case, _, _, _ = self.create_requirement_hierarchy(
            requirement_state=WorkItemState.IN_TEST,
        )

        self.assert_allowed(use_case)

    def test_use_case_requires_changes_in_main(self):
        use_case, _, _, _ = self.create_requirement_hierarchy()

        self.assert_denied(
            use_case,
            changes_in_main=False,
        )

    def test_use_case_requires_main_build(self):
        use_case, _, _, _ = self.create_requirement_hierarchy()

        self.assert_denied(
            use_case,
            main_build_available=False,
        )

    def test_use_case_requires_review_gates(self):
        use_case, _, _, _ = self.create_requirement_hierarchy()

        self.assert_denied(
            use_case,
            review_gates_satisfied=False,
        )

    # ---------------------------------------------------------
    # Feature
    # ---------------------------------------------------------

    def test_feature_can_enter_in_test_when_all_gates_pass(self):
        hierarchy = self.create_feature_hierarchy()

        self.assert_allowed(
            hierarchy["feature"],
            review_results={
                "REVIEW-1": ReviewResult.APPROVED,
            },
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_at_least_one_use_case(self):
        feature = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
        )

        self.assert_denied(
            feature,
            review_results={},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_all_use_cases_in_test_or_resolved(self):
        hierarchy = self.create_feature_hierarchy()
        hierarchy["use_case"].state = WorkItemState.IN_WORK

        self.assert_denied(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_accepts_resolved_use_cases(self):
        hierarchy = self.create_feature_hierarchy()
        hierarchy["use_case"].state = WorkItemState.RESOLVED

        self.assert_allowed(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_supporting_tasks_in_test_or_resolved(self):
        hierarchy = self.create_feature_hierarchy()
        hierarchy["supporting_task"].state = WorkItemState.IN_WORK

        self.assert_denied(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_accepts_resolved_supporting_tasks(self):
        hierarchy = self.create_feature_hierarchy()
        hierarchy["supporting_task"].state = WorkItemState.RESOLVED

        self.assert_allowed(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_exactly_one_code_review_task(self):
        hierarchy = self.create_feature_hierarchy()
        hierarchy["review_task"].work_item_type = (
            WorkItemType.SUPPORTING_TASK
        )

        self.assert_denied(
            hierarchy["feature"],
            review_results={},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_resolved_code_review_task(self):
        hierarchy = self.create_feature_hierarchy()
        hierarchy["review_task"].state = CodeReviewState.REVIEW

        self.assert_denied(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_approved_review_result(self):
        hierarchy = self.create_feature_hierarchy()

        self.assert_denied(
            hierarchy["feature"],
            review_results={
                "REVIEW-1": ReviewResult.CHANGES_REQUESTED,
            },
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_security_gate(self):
        hierarchy = self.create_feature_hierarchy()

        self.assert_denied(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=False,
            ci_gate_passed=True,
        )

    def test_feature_requires_ci_gate(self):
        hierarchy = self.create_feature_hierarchy()

        self.assert_denied(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=False,
        )

    def test_feature_requires_changes_in_main(self):
        hierarchy = self.create_feature_hierarchy()

        self.assert_denied(
            hierarchy["feature"],
            changes_in_main=False,
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_main_build(self):
        hierarchy = self.create_feature_hierarchy()

        self.assert_denied(
            hierarchy["feature"],
            main_build_available=False,
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_review_gates(self):
        hierarchy = self.create_feature_hierarchy()

        self.assert_denied(
            hierarchy["feature"],
            review_gates_satisfied=False,
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    # ---------------------------------------------------------
    # Bug and Change Request
    # ---------------------------------------------------------

    def test_bug_can_enter_in_test_when_ready(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        self.add_related_item(
            bug,
            requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_allowed(bug)

    def test_bug_requires_violated_requirement(self):
        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        self.assert_denied(bug)

    def test_bug_rejects_missing_requirement(self):
        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        bug.relationships += (
            WorkItemRelationship(
                source_id="BUG-1",
                target_id="MISSING",
                relationship_type=RelationshipType.VIOLATED_REQUIREMENT,
            ),
        )

        self.assert_denied(bug)

    def test_bug_requires_requirement_relationship_target(self):
        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        self.add_related_item(
            bug,
            development_task,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_denied(bug)

    def test_change_request_can_enter_in_test_when_ready(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
        )

        self.add_related_item(
            change_request,
            requirement,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        self.assert_allowed(change_request)

    def test_change_request_requires_affected_requirement(self):
        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
        )

        self.assert_denied(change_request)

    def test_change_request_rejects_missing_requirement(self):
        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
        )

        change_request.relationships += (
            WorkItemRelationship(
                source_id="CR-1",
                target_id="MISSING",
                relationship_type=RelationshipType.AFFECTED_REQUIREMENT,
            ),
        )

        self.assert_denied(change_request)

    def test_change_request_requires_requirement_relationship_target(self):
        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
        )

        self.add_related_item(
            change_request,
            development_task,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        self.assert_denied(change_request)

    def test_bug_requires_changes_in_main(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        self.add_related_item(
            bug,
            requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_denied(
            bug,
            changes_in_main=False,
        )

    def test_change_request_requires_main_build(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
        )

        self.add_related_item(
            change_request,
            requirement,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        self.assert_denied(
            change_request,
            main_build_available=False,
        )

    def test_bug_requires_review_gates(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
        )

        self.add_related_item(
            bug,
            requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_denied(
            bug,
            review_gates_satisfied=False,
        )


if __name__ == "__main__":
    unittest.main()
