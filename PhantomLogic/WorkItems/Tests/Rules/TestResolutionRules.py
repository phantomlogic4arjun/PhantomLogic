
import unittest

from PhantomLogic.WorkItems.Models.WorkItem import WorkItem
from PhantomLogic.WorkItems.Models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from PhantomLogic.WorkItems.Models.WorkItemState import (
    CodeReviewState,
    ReviewResult,
    WorkItemState,
)
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType
from PhantomLogic.WorkItems.Rules.PermissionRules import AgentRole
from PhantomLogic.WorkItems.Rules.ResolutionRules import ResolutionRules


class TestResolutionRules(unittest.TestCase):

    def setUp(self):
        self.rules = ResolutionRules()
        self.items = {}

        self.qa_context = {
            "verification_passed": True,
            "acceptance_criteria_met": True,
        }

    # ---------------------------------------------------------
    # Test helpers
    # ---------------------------------------------------------

    def create_item(
        self,
        item_id,
        item_type,
        state=WorkItemState.RESOLVED,
    ):
        item = WorkItem(
            id=item_id,
            title=f"Test {item_type.value}",
            work_item_type=item_type,
            created_by="ProductManager",
            state=state,
        )

        self.items[item_id] = item
        return item

    def add_child(self, parent, child):
        relationship = WorkItemRelationship(
            source_id=parent.id,
            target_id=child.id,
            relationship_type=RelationshipType.PARENT_CHILD,
        )

        parent.relationships += (relationship,)

    def add_related_item(self, source, target, relationship_type):
        relationship = WorkItemRelationship(
            source_id=source.id,
            target_id=target.id,
            relationship_type=relationship_type,
        )

        source.relationships += (relationship,)

    def validate(self, item, **context):
        effective_context = {
            **self.qa_context,
            **context,
        }

        return self.rules.validate_resolution(
            item,
            self.items,
            AgentRole.QA,
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

    def create_requirement_hierarchy(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            WorkItemState.IN_TEST,
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        self.add_child(use_case, requirement)
        self.add_child(use_case, development_task)
        self.add_child(requirement, test_case)

        return use_case, requirement, development_task, test_case

    def create_feature_hierarchy(self):
        feature = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
            WorkItemState.IN_TEST,
        )

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
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        supporting_task = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
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
        errors = self.rules.validate_resolution(
            None,
            {},
            AgentRole.QA,
        )

        self.assertTrue(errors)

    def test_invalid_actor_role_is_rejected(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        errors = self.rules.validate_resolution(
            item,
            self.items,
            "QA",
            **self.qa_context,
        )

        self.assertTrue(errors)

    def test_non_qa_role_cannot_authorize_resolution(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        errors = self.rules.validate_resolution(
            item,
            self.items,
            AgentRole.DEVELOPER,
            **self.qa_context,
        )

        self.assertTrue(errors)

    def test_non_mapping_collection_is_rejected(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        errors = self.rules.validate_resolution(
            item,
            [],
            AgentRole.QA,
            **self.qa_context,
        )

        self.assertTrue(errors)

    def test_collection_entry_must_be_work_item(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.items["INVALID"] = "not a work item"

        self.assertTrue(self.validate(item))

    def test_collection_key_must_match_item_id(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.items["WRONG-ID"] = item

        self.assertTrue(self.validate(item))

    def test_item_must_exist_in_collection(self):
        item = WorkItem(
            id="DEV-1",
            title="Development Task",
            work_item_type=WorkItemType.DEVELOPMENT_TASK,
            created_by="ProductManager",
            state=WorkItemState.IN_TEST,
        )

        errors = self.rules.validate_resolution(
            item,
            {},
            AgentRole.QA,
            **self.qa_context,
        )

        self.assertTrue(errors)

    def test_item_must_be_same_instance_as_collection_entry(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        duplicate = WorkItem(
            id=item.id,
            title=item.title,
            work_item_type=item.work_item_type,
            created_by=item.created_by,
            state=item.state,
        )

        errors = self.rules.validate_resolution(
            duplicate,
            self.items,
            AgentRole.QA,
            **self.qa_context,
        )

        self.assertTrue(errors)

    def test_item_must_be_in_test(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_WORK,
        )

        self.assert_denied(item)

    def test_qa_verification_is_required(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(
            item,
            verification_passed=False,
        )

    def test_acceptance_criteria_must_be_met(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(
            item,
            acceptance_criteria_met=False,
        )

    def test_passed_test_case_ids_must_be_a_set(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(
            item,
            passed_test_case_ids=["TEST-1"],
        )

    def test_review_results_must_be_a_mapping(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(
            item,
            review_results=[],
        )

    def test_code_review_task_uses_separate_lifecycle(self):
        item = self.create_item(
            "REVIEW-1",
            WorkItemType.CODE_REVIEW_TASK,
            CodeReviewState.RESOLVED,
        )

        self.assert_denied(item)

    def test_development_task_can_resolve_after_qa(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.assert_allowed(item)

    def test_supporting_task_can_resolve_after_qa(self):
        item = self.create_item(
            "SUP-1",
            WorkItemType.SUPPORTING_TASK,
            WorkItemState.IN_TEST,
        )

        self.assert_allowed(item)

    def test_is_resolvable_returns_true_for_eligible_item(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_TEST,
        )

        self.assertIs(
            self.rules.is_resolvable(
                item,
                self.items,
                AgentRole.QA,
                **self.qa_context,
            ),
            True,
        )

    def test_is_resolvable_returns_false_for_ineligible_item(self):
        item = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemState.IN_WORK,
        )

        self.assertIs(
            self.rules.is_resolvable(
                item,
                self.items,
                AgentRole.QA,
                **self.qa_context,
            ),
            False,
        )

    # ---------------------------------------------------------
    # Test Case
    # ---------------------------------------------------------

    def test_test_case_requires_passed_result(self):
        _, _, _, test_case = self.create_requirement_hierarchy()
        test_case.state = WorkItemState.IN_TEST

        self.assert_denied(test_case)

    def test_test_case_can_resolve_when_passed(self):
        _, _, _, test_case = self.create_requirement_hierarchy()
        test_case.state = WorkItemState.IN_TEST

        self.assert_allowed(
            test_case,
            passed_test_case_ids={"TEST-1"},
        )

    def test_test_case_requires_requirement_parent(self):
        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(
            test_case,
            passed_test_case_ids={"TEST-1"},
        )

    def test_test_case_rejects_multiple_requirement_parents(self):
        requirement_one = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        requirement_two = self.create_item(
            "REQ-2",
            WorkItemType.REQUIREMENT,
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
            WorkItemState.IN_TEST,
        )

        self.add_child(requirement_one, test_case)
        self.add_child(requirement_two, test_case)

        self.assert_denied(
            test_case,
            passed_test_case_ids={"TEST-1"},
        )

    # ---------------------------------------------------------
    # Requirement
    # ---------------------------------------------------------

    def test_requirement_can_resolve_when_all_conditions_are_met(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        self.assert_allowed(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    def test_requirement_requires_test_case(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            WorkItemState.IN_TEST,
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.add_child(use_case, requirement)
        self.add_child(use_case, development_task)

        self.assert_denied(requirement)

    def test_requirement_requires_resolved_test_case(self):
        _, requirement, _, test_case = self.create_requirement_hierarchy()
        test_case.state = WorkItemState.IN_TEST

        self.assert_denied(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    def test_requirement_requires_passed_test_case(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        self.assert_denied(
            requirement,
            passed_test_case_ids=set(),
        )

    def test_requirement_requires_use_case_parent(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            WorkItemState.IN_TEST,
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        self.add_child(requirement, test_case)

        self.assert_denied(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    def test_requirement_requires_exactly_one_development_task(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
            WorkItemState.IN_TEST,
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        self.add_child(use_case, requirement)
        self.add_child(requirement, test_case)

        self.assert_denied(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    def test_requirement_requires_resolved_development_task(self):
        _, requirement, development_task, _ = (
            self.create_requirement_hierarchy()
        )

        development_task.state = WorkItemState.IN_TEST

        self.assert_denied(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    def test_active_bug_prevents_requirement_resolution(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_WORK,
        )

        self.add_related_item(
            bug,
            requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_denied(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    def test_resolved_bug_does_not_prevent_requirement_resolution(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.RESOLVED,
        )

        self.add_related_item(
            bug,
            requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_allowed(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    def test_active_change_request_prevents_requirement_resolution(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            WorkItemState.IN_WORK,
        )

        self.add_related_item(
            change_request,
            requirement,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        self.assert_denied(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    def test_resolved_change_request_does_not_block_requirement(self):
        _, requirement, _, _ = self.create_requirement_hierarchy()

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            WorkItemState.RESOLVED,
        )

        self.add_related_item(
            change_request,
            requirement,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        self.assert_allowed(
            requirement,
            passed_test_case_ids={"TEST-1"},
        )

    # ---------------------------------------------------------
    # Use Case
    # ---------------------------------------------------------

    def test_use_case_can_resolve_when_all_requirements_are_resolved(self):
        use_case, requirement, _, _ = self.create_requirement_hierarchy()

        use_case.state = WorkItemState.IN_TEST
        requirement.state = WorkItemState.RESOLVED

        self.assert_allowed(use_case)

    def test_use_case_requires_requirements(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            WorkItemState.IN_TEST,
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        self.add_child(use_case, development_task)

        self.assert_denied(use_case)

    def test_use_case_requires_all_requirements_resolved(self):
        use_case, requirement, _, _ = self.create_requirement_hierarchy()

        use_case.state = WorkItemState.IN_TEST
        requirement.state = WorkItemState.IN_WORK

        self.assert_denied(use_case)

    def test_use_case_requires_exactly_one_development_task(self):
        use_case = self.create_item(
            "UC-1",
            WorkItemType.USE_CASE,
            WorkItemState.IN_TEST,
        )

        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        self.add_child(use_case, requirement)

        self.assert_denied(use_case)

    def test_use_case_requires_resolved_development_task(self):
        use_case, _, development_task, _ = (
            self.create_requirement_hierarchy()
        )

        use_case.state = WorkItemState.IN_TEST
        development_task.state = WorkItemState.IN_WORK

        self.assert_denied(use_case)

    # ---------------------------------------------------------
    # Feature
    # ---------------------------------------------------------

    def test_feature_can_resolve_when_all_gates_pass(self):
        hierarchy = self.create_feature_hierarchy()

        self.assert_allowed(
            hierarchy["feature"],
            review_results={
                "REVIEW-1": ReviewResult.APPROVED,
            },
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_use_cases(self):
        feature = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(
            feature,
            review_results={},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_all_use_cases_resolved(self):
        hierarchy = self.create_feature_hierarchy()
        hierarchy["use_case"].state = WorkItemState.IN_WORK

        self.assert_denied(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_feature_requires_supporting_tasks_resolved(self):
        hierarchy = self.create_feature_hierarchy()
        hierarchy["supporting_task"].state = WorkItemState.IN_WORK

        self.assert_denied(
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

    def test_active_bug_in_feature_prevents_resolution(self):
        hierarchy = self.create_feature_hierarchy()

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_WORK,
        )

        self.add_related_item(
            bug,
            hierarchy["requirement"],
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_denied(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    def test_bug_in_another_feature_does_not_block_feature(self):
        hierarchy = self.create_feature_hierarchy()

        other_feature = self.create_item(
            "FEAT-2",
            WorkItemType.FEATURE,
        )

        other_use_case = self.create_item(
            "UC-2",
            WorkItemType.USE_CASE,
        )

        other_requirement = self.create_item(
            "REQ-2",
            WorkItemType.REQUIREMENT,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_WORK,
        )

        self.add_child(other_feature, other_use_case)
        self.add_child(other_use_case, other_requirement)

        self.add_related_item(
            bug,
            other_requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_allowed(
            hierarchy["feature"],
            review_results={"REVIEW-1": ReviewResult.APPROVED},
            security_gate_passed=True,
            ci_gate_passed=True,
        )

    # ---------------------------------------------------------
    # Bug
    # ---------------------------------------------------------

    def test_bug_requires_violated_requirement(self):
        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(bug)

    def test_bug_requires_existing_requirement(self):
        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_TEST,
        )

        missing_requirement = WorkItemRelationship(
            source_id="BUG-1",
            target_id="MISSING",
            relationship_type=RelationshipType.VIOLATED_REQUIREMENT,
        )

        bug.relationships += (missing_requirement,)

        self.assert_denied(bug)

    def test_bug_requires_relationship_target_to_be_requirement(self):
        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_TEST,
        )

        self.add_related_item(
            bug,
            development_task,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_denied(bug)

    def test_bug_does_not_require_failed_test_case_when_not_applicable(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_TEST,
        )

        self.add_related_item(
            bug,
            requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.assert_allowed(bug)

    def test_bug_validates_failed_test_case_reference_when_supplied(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_TEST,
        )

        self.add_related_item(
            bug,
            requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.add_related_item(
            bug,
            development_task,
            RelationshipType.FAILED_TEST_CASE,
        )

        self.assert_denied(bug)

    def test_bug_can_resolve_with_valid_requirement_and_test_case(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        test_case = self.create_item(
            "TEST-1",
            WorkItemType.TEST_CASE,
        )

        bug = self.create_item(
            "BUG-1",
            WorkItemType.BUG,
            WorkItemState.IN_TEST,
        )

        self.add_related_item(
            bug,
            requirement,
            RelationshipType.VIOLATED_REQUIREMENT,
        )

        self.add_related_item(
            bug,
            test_case,
            RelationshipType.FAILED_TEST_CASE,
        )

        self.assert_allowed(bug)

    # ---------------------------------------------------------
    # Change Request
    # ---------------------------------------------------------

    def test_change_request_requires_affected_requirement(self):
        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(change_request)

    def test_change_request_requires_existing_requirement(self):
        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            WorkItemState.IN_TEST,
        )

        change_request.relationships += (
            WorkItemRelationship(
                source_id="CR-1",
                target_id="MISSING",
                relationship_type=RelationshipType.AFFECTED_REQUIREMENT,
            ),
        )

        self.assert_denied(change_request)

    def test_change_request_requires_requirement_target(self):
        development_task = self.create_item(
            "DEV-1",
            WorkItemType.DEVELOPMENT_TASK,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            WorkItemState.IN_TEST,
        )

        self.add_related_item(
            change_request,
            development_task,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        self.assert_denied(change_request)

    def test_change_request_can_resolve_with_affected_requirement(self):
        requirement = self.create_item(
            "REQ-1",
            WorkItemType.REQUIREMENT,
        )

        change_request = self.create_item(
            "CR-1",
            WorkItemType.CHANGE_REQUEST,
            WorkItemState.IN_TEST,
        )

        self.add_related_item(
            change_request,
            requirement,
            RelationshipType.AFFECTED_REQUIREMENT,
        )

        self.assert_allowed(change_request)

    # ---------------------------------------------------------
    # Epic
    # ---------------------------------------------------------

    def test_epic_requires_features(self):
        epic = self.create_item(
            "EPIC-1",
            WorkItemType.EPIC,
            WorkItemState.IN_TEST,
        )

        self.assert_denied(epic)

    def test_epic_requires_all_features_resolved(self):
        epic = self.create_item(
            "EPIC-1",
            WorkItemType.EPIC,
            WorkItemState.IN_TEST,
        )

        feature = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
            WorkItemState.IN_WORK,
        )

        self.add_child(epic, feature)

        self.assert_denied(epic)

    def test_epic_can_resolve_when_all_features_are_resolved(self):
        epic = self.create_item(
            "EPIC-1",
            WorkItemType.EPIC,
            WorkItemState.IN_TEST,
        )

        feature = self.create_item(
            "FEAT-1",
            WorkItemType.FEATURE,
        )

        self.add_child(epic, feature)

        self.assert_allowed(epic)


if __name__ == "__main__":
    unittest.main()
