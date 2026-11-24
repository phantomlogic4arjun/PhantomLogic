
import unittest

from phantom_logic.work_items.rules.PermissionRules import AgentRole
from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemState import (
    CodeReviewState,
    WorkItemState,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.StateTransitionRules import (
    StateTransitionRules,
)


class TestStateTransitionRules(unittest.TestCase):

    def setUp(self):
        self.rules = StateTransitionRules()

    def create_item(
        self,
        work_item_type=WorkItemType.DEVELOPMENT_TASK,
        state=WorkItemState.PROPOSED,
    ):
        return WorkItem(
            id="WI-001",
            title="Test work item",
            work_item_type=work_item_type,
            created_by="ProductManager",
            state=state,
        )

    def assert_allowed(self, item, target, role, **context):
        self.assertEqual(
            [],
            self.rules.validate_transition(
                item, target, role, **context
            ),
        )

    def assert_denied(self, item, target, role, **context):
        self.assertTrue(
            self.rules.validate_transition(
                item, target, role, **context
            )
        )

    # ---------------------------------------------------------
    # Proposed -> In Work
    # ---------------------------------------------------------

    def test_product_manager_can_start_authorized_work(self):
        self.assert_allowed(
            self.create_item(),
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            work_authorized=True,
        )

    def test_work_item_manager_can_start_authorized_work(self):
        self.assert_allowed(
            self.create_item(),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            work_authorized=True,
        )

    def test_work_cannot_start_without_authorization(self):
        self.assert_denied(
            self.create_item(),
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
        )

    def test_developer_cannot_start_proposed_work(self):
        self.assert_denied(
            self.create_item(),
            WorkItemState.IN_WORK,
            AgentRole.DEVELOPER,
            work_authorized=True,
        )

    def test_qa_cannot_start_proposed_work(self):
        self.assert_denied(
            self.create_item(),
            WorkItemState.IN_WORK,
            AgentRole.QA,
            work_authorized=True,
        )

    # ---------------------------------------------------------
    # In Work -> In Test
    # ---------------------------------------------------------

    def test_developer_can_submit_ready_work_for_test(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.IN_TEST,
            AgentRole.DEVELOPER,
            implementation_ready=True,
        )

    def test_work_item_manager_can_move_ready_work_to_test(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.IN_TEST,
            AgentRole.WORK_ITEM_MANAGER,
            implementation_ready=True,
        )

    def test_work_cannot_enter_test_before_implementation_is_ready(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.IN_TEST,
            AgentRole.DEVELOPER,
        )

    def test_qa_cannot_submit_work_for_test(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.IN_TEST,
            AgentRole.QA,
            implementation_ready=True,
        )

    # ---------------------------------------------------------
    # In Test -> In Work
    # ---------------------------------------------------------

    def test_qa_can_return_failed_work_to_in_work(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.IN_WORK,
            AgentRole.QA,
        )

    def test_developer_cannot_return_tested_work_to_in_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.IN_WORK,
            AgentRole.DEVELOPER,
        )

    # ---------------------------------------------------------
    # In Test -> Resolved
    # ---------------------------------------------------------

    def test_qa_can_resolve_verified_work(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.RESOLVED,
            AgentRole.QA,
            verification_passed=True,
            completion_criteria_met=True,
        )

    def test_work_cannot_resolve_without_successful_verification(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.RESOLVED,
            AgentRole.QA,
            completion_criteria_met=True,
        )

    def test_work_cannot_resolve_without_completion_criteria(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.RESOLVED,
            AgentRole.QA,
            verification_passed=True,
        )

    def test_developer_cannot_resolve_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.RESOLVED,
            AgentRole.DEVELOPER,
            verification_passed=True,
            completion_criteria_met=True,
        )

    def test_product_manager_cannot_resolve_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.RESOLVED,
            AgentRole.PRODUCT_MANAGER,
            verification_passed=True,
            completion_criteria_met=True,
        )

    # ---------------------------------------------------------
    # Blocking
    # ---------------------------------------------------------

    def test_developer_can_block_work_with_reason(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.BLOCKED,
            AgentRole.DEVELOPER,
            reason="Waiting for implementation dependency.",
        )

    def test_product_manager_can_block_work_with_reason(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.BLOCKED,
            AgentRole.PRODUCT_MANAGER,
            reason="Scope decision is pending.",
        )

    def test_reviewer_can_block_work_with_reason(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.BLOCKED,
            AgentRole.REVIEWER,
            reason="Required review dependency is unavailable.",
        )

    def test_qa_can_block_work_with_reason(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.BLOCKED,
            AgentRole.QA,
            reason="Test environment is unavailable.",
        )

    def test_blocking_requires_reason(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.BLOCKED,
            AgentRole.DEVELOPER,
        )

    def test_blocking_rejects_blank_reason(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.BLOCKED,
            AgentRole.DEVELOPER,
            reason="   ",
        )

    def test_orchestrator_cannot_block_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.BLOCKED,
            AgentRole.ORCHESTRATOR,
            reason="Dependency unavailable.",
        )

    def test_work_item_manager_cannot_block_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.BLOCKED,
            AgentRole.WORK_ITEM_MANAGER,
            reason="Dependency unavailable.",
        )

    # ---------------------------------------------------------
    # Unblocking
    # ---------------------------------------------------------

    def test_work_item_manager_can_restore_saved_state(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.BLOCKED),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            previous_state=WorkItemState.IN_WORK,
            reason="Dependency has been resolved.",
        )

    def test_unblocking_requires_saved_state_match(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.BLOCKED),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            previous_state=WorkItemState.PROPOSED,
            reason="Dependency has been resolved.",
        )

    def test_unblocking_requires_reason(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.BLOCKED),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            previous_state=WorkItemState.IN_WORK,
        )

    def test_product_manager_cannot_unblock_directly(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.BLOCKED),
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            previous_state=WorkItemState.IN_WORK,
            reason="Dependency has been resolved.",
        )

    def test_unblocking_can_restore_proposed_state(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.BLOCKED),
            WorkItemState.PROPOSED,
            AgentRole.WORK_ITEM_MANAGER,
            previous_state=WorkItemState.PROPOSED,
            reason="The external dependency is no longer blocking.",
        )

    def test_unblocking_can_restore_in_test_state(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.BLOCKED),
            WorkItemState.IN_TEST,
            AgentRole.WORK_ITEM_MANAGER,
            previous_state=WorkItemState.IN_TEST,
            reason="The test environment is available again.",
        )

    # ---------------------------------------------------------
    # Removal
    # ---------------------------------------------------------

    def test_product_manager_can_remove_work_with_reason(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.PROPOSED),
            WorkItemState.REMOVED,
            AgentRole.PRODUCT_MANAGER,
            reason="The proposed work is no longer required.",
        )

    def test_removal_requires_reason(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.REMOVED,
            AgentRole.PRODUCT_MANAGER,
        )

    def test_developer_cannot_remove_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.REMOVED,
            AgentRole.DEVELOPER,
            reason="No longer needed.",
        )

    def test_qa_cannot_remove_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.REMOVED,
            AgentRole.QA,
            reason="No longer needed.",
        )

    # ---------------------------------------------------------
    # Reopening resolved work
    # ---------------------------------------------------------

    def test_product_manager_can_reopen_resolved_work_when_authorized(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.RESOLVED),
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            work_authorized=True,
        )

    def test_work_item_manager_can_apply_authorized_reopening(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.RESOLVED),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            work_authorized=True,
        )

    def test_resolved_work_cannot_be_reopened_without_authorization(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.RESOLVED),
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
        )

    def test_developer_cannot_reopen_resolved_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.RESOLVED),
            WorkItemState.IN_WORK,
            AgentRole.DEVELOPER,
            work_authorized=True,
        )

    # ---------------------------------------------------------
    # Invalid transitions and model validation
    # ---------------------------------------------------------

    def test_proposed_cannot_move_directly_to_resolved(self):
        self.assert_denied(
            self.create_item(),
            WorkItemState.RESOLVED,
            AgentRole.QA,
            verification_passed=True,
            completion_criteria_met=True,
        )

    def test_proposed_cannot_move_directly_to_in_test(self):
        self.assert_denied(
            self.create_item(),
            WorkItemState.IN_TEST,
            AgentRole.DEVELOPER,
            implementation_ready=True,
        )

    def test_resolved_work_cannot_move_directly_to_in_test(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.RESOLVED),
            WorkItemState.IN_TEST,
            AgentRole.DEVELOPER,
            implementation_ready=True,
        )

    def test_removed_work_cannot_be_reopened(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.REMOVED),
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            work_authorized=True,
        )

    def test_same_state_transition_is_rejected(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_WORK),
            WorkItemState.IN_WORK,
            AgentRole.DEVELOPER,
        )

    def test_invalid_work_item_is_rejected(self):
        errors = self.rules.validate_transition(
            None,
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
        )
        self.assertTrue(errors)

    def test_invalid_role_is_rejected(self):
        errors = self.rules.validate_transition(
            self.create_item(),
            WorkItemState.IN_WORK,
            "Product Manager",
            work_authorized=True,
        )
        self.assertTrue(errors)

    def test_standard_item_rejects_code_review_state(self):
        self.assert_denied(
            self.create_item(),
            CodeReviewState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            work_authorized=True,
        )

    def test_code_review_item_rejects_standard_state(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.CODE_REVIEW_TASK,
                state=CodeReviewState.PROPOSED,
            ),
            WorkItemState.IN_WORK,
            AgentRole.REVIEWER,
        )

    def test_invalid_current_state_type_is_rejected(self):
        item = self.create_item()
        item.state = CodeReviewState.IN_WORK

        self.assertTrue(
            self.rules.validate_transition(
                item,
                WorkItemState.IN_TEST,
                AgentRole.DEVELOPER,
                implementation_ready=True,
            )
        )

    def test_is_valid_transition_returns_boolean(self):
        result = self.rules.is_valid_transition(
            self.create_item(),
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            work_authorized=True,
        )
        self.assertIs(result, True)

    # ---------------------------------------------------------
    # Code Review Task lifecycle
    # ---------------------------------------------------------

    def create_review_task(self, state):
        return self.create_item(
            work_item_type=WorkItemType.CODE_REVIEW_TASK,
            state=state,
        )

    def test_reviewer_can_start_code_review_task(self):
        self.assert_allowed(
            self.create_review_task(CodeReviewState.PROPOSED),
            CodeReviewState.IN_WORK,
            AgentRole.REVIEWER,
        )

    def test_non_reviewer_cannot_start_code_review_task(self):
        self.assert_denied(
            self.create_review_task(CodeReviewState.PROPOSED),
            CodeReviewState.IN_WORK,
            AgentRole.DEVELOPER,
        )

    def test_reviewer_can_move_code_review_into_review(self):
        self.assert_allowed(
            self.create_review_task(CodeReviewState.IN_WORK),
            CodeReviewState.REVIEW,
            AgentRole.REVIEWER,
        )

    def test_developer_cannot_move_code_review_into_review(self):
        self.assert_denied(
            self.create_review_task(CodeReviewState.IN_WORK),
            CodeReviewState.REVIEW,
            AgentRole.DEVELOPER,
        )

    def test_reviewer_can_return_review_for_changes(self):
        self.assert_allowed(
            self.create_review_task(CodeReviewState.REVIEW),
            CodeReviewState.IN_WORK,
            AgentRole.REVIEWER,
            reason="Changes are required before approval.",
        )

    def test_returning_review_for_changes_requires_reason(self):
        self.assert_denied(
            self.create_review_task(CodeReviewState.REVIEW),
            CodeReviewState.IN_WORK,
            AgentRole.REVIEWER,
        )

    def test_reviewer_can_resolve_approved_code_review(self):
        self.assert_allowed(
            self.create_review_task(CodeReviewState.REVIEW),
            CodeReviewState.RESOLVED,
            AgentRole.REVIEWER,
            review_approved=True,
        )

    def test_code_review_cannot_resolve_without_approval(self):
        self.assert_denied(
            self.create_review_task(CodeReviewState.REVIEW),
            CodeReviewState.RESOLVED,
            AgentRole.REVIEWER,
        )

    def test_developer_cannot_resolve_code_review(self):
        self.assert_denied(
            self.create_review_task(CodeReviewState.REVIEW),
            CodeReviewState.RESOLVED,
            AgentRole.DEVELOPER,
            review_approved=True,
        )

    def test_code_review_cannot_skip_review_state(self):
        self.assert_denied(
            self.create_review_task(CodeReviewState.IN_WORK),
            CodeReviewState.RESOLVED,
            AgentRole.REVIEWER,
            review_approved=True,
        )

    def test_code_review_task_cannot_use_blocked_state(self):
        self.assert_denied(
            self.create_review_task(CodeReviewState.IN_WORK),
            WorkItemState.BLOCKED,
            AgentRole.REVIEWER,
            reason="Review is blocked.",
        )



    # ---------------------------------------------------------
    # Authorized Bug / Change Request propagation
    # ---------------------------------------------------------

    def test_wim_can_propagate_authorized_bug_to_affected_work(self):
        affected_types = (
            WorkItemType.BUG,
            WorkItemType.REQUIREMENT,
            WorkItemType.USE_CASE,
            WorkItemType.FEATURE,
        )

        for item_type in affected_types:
            with self.subTest(item_type=item_type):
                self.assert_allowed(
                    self.create_item(
                        work_item_type=item_type,
                        state=WorkItemState.PROPOSED,
                    ),
                    WorkItemState.IN_WORK,
                    AgentRole.WORK_ITEM_MANAGER,
                    authorized_propagation=True,
                    propagation_source_type=WorkItemType.BUG,
                    work_authorized=True,
                )

    def test_wim_can_propagate_authorized_change_request_to_affected_work(self):
        affected_types = (
            WorkItemType.CHANGE_REQUEST,
            WorkItemType.REQUIREMENT,
            WorkItemType.USE_CASE,
            WorkItemType.FEATURE,
        )

        for item_type in affected_types:
            with self.subTest(item_type=item_type):
                self.assert_allowed(
                    self.create_item(
                        work_item_type=item_type,
                        state=WorkItemState.PROPOSED,
                    ),
                    WorkItemState.IN_WORK,
                    AgentRole.WORK_ITEM_MANAGER,
                    authorized_propagation=True,
                    propagation_source_type=WorkItemType.CHANGE_REQUEST,
                    work_authorized=True,
                )

    def test_wim_can_propagate_in_test_work_back_to_in_work(self):
        for item_type in (
            WorkItemType.BUG,
            WorkItemType.CHANGE_REQUEST,
            WorkItemType.REQUIREMENT,
            WorkItemType.USE_CASE,
            WorkItemType.FEATURE,
        ):
            with self.subTest(item_type=item_type):
                self.assert_allowed(
                    self.create_item(
                        work_item_type=item_type,
                        state=WorkItemState.IN_TEST,
                    ),
                    WorkItemState.IN_WORK,
                    AgentRole.WORK_ITEM_MANAGER,
                    authorized_propagation=True,
                    propagation_source_type=WorkItemType.BUG,
                    work_authorized=True,
                )

    def test_wim_can_reopen_resolved_work_through_authorized_propagation(self):
        for item_type in (
            WorkItemType.BUG,
            WorkItemType.CHANGE_REQUEST,
            WorkItemType.REQUIREMENT,
            WorkItemType.USE_CASE,
            WorkItemType.FEATURE,
        ):
            with self.subTest(item_type=item_type):
                self.assert_allowed(
                    self.create_item(
                        work_item_type=item_type,
                        state=WorkItemState.RESOLVED,
                    ),
                    WorkItemState.IN_WORK,
                    AgentRole.WORK_ITEM_MANAGER,
                    authorized_propagation=True,
                    propagation_source_type=WorkItemType.CHANGE_REQUEST,
                    work_authorized=True,
                )

    def test_propagation_requires_work_authorization_flag(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.PROPOSED,
            ),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
        )

    def test_propagation_requires_explicit_propagation_flag(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.IN_TEST,
            ),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            work_authorized=True,
        )

    def test_product_manager_cannot_perform_propagation_transition(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.IN_TEST,
            ),
            WorkItemState.IN_WORK,
            AgentRole.PRODUCT_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_developer_cannot_perform_propagation_transition(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.IN_TEST,
            ),
            WorkItemState.IN_WORK,
            AgentRole.DEVELOPER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_qa_cannot_use_propagation_flag(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.IN_TEST,
            ),
            WorkItemState.IN_WORK,
            AgentRole.QA,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_reviewer_cannot_perform_propagation_transition(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.RESOLVED,
            ),
            WorkItemState.IN_WORK,
            AgentRole.REVIEWER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.CHANGE_REQUEST,
            work_authorized=True,
        )

    def test_orchestrator_cannot_perform_propagation_transition(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.PROPOSED,
            ),
            WorkItemState.IN_WORK,
            AgentRole.ORCHESTRATOR,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_propagation_requires_bug_or_change_request_source(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.PROPOSED,
            ),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.FEATURE,
            work_authorized=True,
        )

    def test_propagation_rejects_missing_source_type(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.PROPOSED,
            ),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            work_authorized=True,
        )

    def test_propagation_rejects_invalid_source_type(self):
        self.assert_denied(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.PROPOSED,
            ),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type="Bug",
            work_authorized=True,
        )

    def test_propagation_rejects_unrelated_work_item_types(self):
        for item_type in (
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemType.SUPPORTING_TASK,
            WorkItemType.TEST_CASE,
        ):
            with self.subTest(item_type=item_type):
                self.assert_denied(
                    self.create_item(
                        work_item_type=item_type,
                        state=WorkItemState.PROPOSED,
                    ),
                    WorkItemState.IN_WORK,
                    AgentRole.WORK_ITEM_MANAGER,
                    authorized_propagation=True,
                    propagation_source_type=WorkItemType.BUG,
                    work_authorized=True,
                )

    def test_propagation_cannot_change_code_review_task(self):
        self.assert_denied(
            self.create_review_task(CodeReviewState.PROPOSED),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_propagation_cannot_resolve_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.RESOLVED,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_propagation_cannot_remove_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.PROPOSED),
            WorkItemState.REMOVED,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_propagation_cannot_unblock_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.BLOCKED),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            previous_state=WorkItemState.IN_WORK,
            reason="Dependency resolved.",
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_propagation_rejects_removed_work(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.REMOVED),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_propagation_rejects_wrong_target_state(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.PROPOSED),
            WorkItemState.RESOLVED,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_propagation_rejects_source_type_without_propagation_flag(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.PROPOSED),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

    def test_normal_qa_return_remains_valid_without_propagation(self):
        self.assert_allowed(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.IN_WORK,
            AgentRole.QA,
        )

    def test_wim_cannot_return_in_test_work_without_propagation(self):
        self.assert_denied(
            self.create_item(state=WorkItemState.IN_TEST),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
        )

    def test_is_valid_transition_supports_authorized_propagation(self):
        result = self.rules.is_valid_transition(
            self.create_item(
                work_item_type=WorkItemType.REQUIREMENT,
                state=WorkItemState.RESOLVED,
            ),
            WorkItemState.IN_WORK,
            AgentRole.WORK_ITEM_MANAGER,
            authorized_propagation=True,
            propagation_source_type=WorkItemType.BUG,
            work_authorized=True,
        )

        self.assertIs(result, True)


if __name__ == "__main__":
    unittest.main()
