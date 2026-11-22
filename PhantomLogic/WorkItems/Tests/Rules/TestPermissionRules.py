
import unittest
from datetime import datetime, timedelta, timezone
from PhantomLogic.WorkItems.Models.WorkItem import WorkItem
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType
from PhantomLogic.WorkItems.Rules.PermissionRules import (
    AgentRole,
    PermissionRules,
    WorkItemOperation,
)


class TestPermissionRules(unittest.TestCase):

    def create_work_item(
        self,
        work_item_type=WorkItemType.REQUIREMENT,
        assigned_agent=None,
    ):
        return WorkItem(
            id="WI-001",
            title="Test Work Item",
            work_item_type=work_item_type,
            created_by="ProductManager",
            assigned_agent=assigned_agent,
        )

    def create_authorized_work_item(
        self,
        work_item_type=WorkItemType.BUG,
    ):
        return WorkItem(
            id="WI-001",
            title="Test Work Item",
            work_item_type=work_item_type,
            created_by="QA",
            authorized_by="ProductManager-01",
            authorized_at=datetime(
                2026, 11, 21, 20, 0, tzinfo=timezone.utc
            ),
            authorization_reason="Approved for implementation.",
        )

    def validate(
        self,
        role,
        operation,
        work_item=None,
        **context,
    ):
        return PermissionRules.validate_permission(
            role,
            operation,
            work_item or self.create_work_item(),
            **context,
        )

    # Input validation

    def test_invalid_agent_role_is_rejected(self):
        errors = self.validate(
            "Developer",
            WorkItemOperation.IMPLEMENT,
        )

        self.assertTrue(any("Agent role is invalid" in e for e in errors))

    def test_invalid_operation_is_rejected(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            "Implement",
        )

        self.assertTrue(any("operation is invalid" in e for e in errors))

    def test_non_work_item_is_rejected(self):
        errors = PermissionRules.validate_permission(
            AgentRole.DEVELOPER,
            WorkItemOperation.IMPLEMENT,
            "Not a work item",
        )

        self.assertTrue(
            any("WorkItem instance" in e for e in errors)
        )

    def test_invalid_work_item_type_is_rejected(self):
        item = self.create_work_item()
        item.work_item_type = "Requirement"

        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.IMPLEMENT,
            item,
        )

        self.assertTrue(any("Work item type is invalid" in e for e in errors))

    def test_is_permitted_returns_boolean(self):
        result = PermissionRules.is_permitted(
            AgentRole.DEVELOPER,
            WorkItemOperation.IMPLEMENT,
            self.create_work_item(WorkItemType.DEVELOPMENT_TASK),
        )

        self.assertIsInstance(result, bool)
        self.assertTrue(result)

    # Work item creation

    def test_product_manager_can_create_work_items(self):
        for work_item_type in WorkItemType:
            with self.subTest(work_item_type=work_item_type):
                errors = self.validate(
                    AgentRole.PRODUCT_MANAGER,
                    WorkItemOperation.CREATE_WORK_ITEM,
                    self.create_work_item(work_item_type),
                )
                self.assertEqual(errors, [])

    def test_developer_cannot_create_work_items(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.CREATE_WORK_ITEM,
        )

        self.assertTrue(errors)

    def test_qa_can_create_bugs(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.CREATE_BUG,
            self.create_work_item(WorkItemType.BUG),
        )

        self.assertEqual(errors, [])

    def test_non_qa_cannot_create_bugs(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.CREATE_BUG,
            self.create_work_item(WorkItemType.BUG),
        )

        self.assertTrue(errors)

    def test_create_bug_rejects_non_bug_item(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.CREATE_BUG,
            self.create_work_item(WorkItemType.REQUIREMENT),
        )

        self.assertTrue(any("only be used for a Bug" in e for e in errors))

    def test_qa_can_create_test_cases(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.CREATE_TEST_CASE,
            self.create_work_item(WorkItemType.TEST_CASE),
        )

        self.assertEqual(errors, [])

    def test_product_manager_can_create_test_cases(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.CREATE_TEST_CASE,
            self.create_work_item(WorkItemType.TEST_CASE),
        )

        self.assertEqual(errors, [])

    def test_create_test_case_rejects_other_item_types(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.CREATE_TEST_CASE,
            self.create_work_item(WorkItemType.BUG),
        )

        self.assertTrue(any("only be used for a Test Case" in e for e in errors))

    # Scope and relationship management

    def test_product_manager_can_update_requirement_scope(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.UPDATE_SCOPE,
            self.create_work_item(WorkItemType.REQUIREMENT),
        )

        self.assertEqual(errors, [])

    def test_product_manager_can_update_feature_scope(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.UPDATE_SCOPE,
            self.create_work_item(WorkItemType.FEATURE),
        )

        self.assertEqual(errors, [])

    def test_developer_cannot_update_requirement_scope(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.UPDATE_SCOPE,
            self.create_work_item(WorkItemType.REQUIREMENT),
        )

        self.assertTrue(errors)

    def test_product_manager_cannot_update_implementation_through_scope_operation(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.UPDATE_SCOPE,
            self.create_work_item(WorkItemType.DEVELOPMENT_TASK),
        )

        self.assertTrue(errors)

    def test_developer_can_update_implementation(self):
        for work_item_type in PermissionRules.DEVELOPER_IMPLEMENTATION_TYPES:
            with self.subTest(work_item_type=work_item_type):
                errors = self.validate(
                    AgentRole.DEVELOPER,
                    WorkItemOperation.UPDATE_IMPLEMENTATION,
                    self.create_work_item(work_item_type),
                )
                self.assertEqual(errors, [])

    def test_developer_cannot_update_feature_implementation_directly(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.UPDATE_IMPLEMENTATION,
            self.create_work_item(WorkItemType.FEATURE),
        )

        self.assertTrue(errors)

    def test_product_manager_can_manage_relationships(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.MANAGE_RELATIONSHIPS,
        )

        self.assertEqual(errors, [])

    def test_work_item_manager_can_manage_relationships(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.MANAGE_RELATIONSHIPS,
        )

        self.assertEqual(errors, [])

    def test_developer_cannot_manage_relationships_directly(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.MANAGE_RELATIONSHIPS,
        )

        self.assertTrue(errors)


    # Authorization

    def test_product_manager_can_authorize_work_with_identity_and_reason(self):
        for work_item_type in PermissionRules.PRODUCT_MANAGER_AUTHORIZATION_TYPES:
            with self.subTest(work_item_type=work_item_type):
                errors = self.validate(
                    AgentRole.PRODUCT_MANAGER,
                    WorkItemOperation.AUTHORIZE_WORK,
                    self.create_work_item(work_item_type),
                    actor_id="ProductManager-01",
                    reason="Approved for implementation.",
                )

                self.assertEqual(errors, [])

    def test_developer_cannot_authorize_work(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.AUTHORIZE_WORK,
            actor_id="Developer-01",
            reason="Attempted authorization.",
        )

        self.assertTrue(errors)

    def test_orchestrator_cannot_authorize_work(self):
        errors = self.validate(
            AgentRole.ORCHESTRATOR,
            WorkItemOperation.AUTHORIZE_WORK,
            actor_id="Orchestrator-01",
            reason="Attempted authorization.",
        )

        self.assertTrue(errors)

    def test_qa_cannot_authorize_work(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.AUTHORIZE_WORK,
            actor_id="QA-01",
            reason="Attempted authorization.",
        )

        self.assertTrue(errors)

    def test_reviewer_cannot_authorize_work(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.AUTHORIZE_WORK,
            actor_id="Reviewer-01",
            reason="Attempted authorization.",
        )

        self.assertTrue(errors)

    def test_authorization_requires_product_manager_identity(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.AUTHORIZE_WORK,
            actor_id=None,
            reason="Approved.",
        )

        self.assertTrue(
            any("Product Manager identity is required" in e for e in errors)
        )

    def test_authorization_rejects_blank_product_manager_identity(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.AUTHORIZE_WORK,
            actor_id="   ",
            reason="Approved.",
        )

        self.assertTrue(
            any("Product Manager identity is required" in e for e in errors)
        )

    def test_authorization_requires_reason(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.AUTHORIZE_WORK,
            actor_id="ProductManager-01",
            reason=None,
        )

        self.assertTrue(
            any("authorization reason is required" in e for e in errors)
        )

    def test_authorization_rejects_blank_reason(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.AUTHORIZE_WORK,
            actor_id="ProductManager-01",
            reason=" ",
        )

        self.assertTrue(
            any("authorization reason is required" in e for e in errors)
        )

    def test_authorization_rejects_unsupported_work_item_type(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.AUTHORIZE_WORK,
            self.create_work_item(WorkItemType.TEST_CASE),
            actor_id="ProductManager-01",
            reason="Approved.",
        )

        self.assertTrue(
            any("cannot authorize work" in e for e in errors)
        )

    def test_work_cannot_start_without_authorization(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.START_AUTHORIZED_WORK,
            work_authorized=False,
        )

        self.assertTrue(
            any("explicitly authorized" in e for e in errors)
        )

    def test_product_manager_can_start_authorized_work(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.START_AUTHORIZED_WORK,
            work_authorized=True,
        )

        self.assertEqual(errors, [])

    def test_work_item_manager_can_start_authorized_work(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.START_AUTHORIZED_WORK,
            work_authorized=True,
        )

        self.assertEqual(errors, [])

    def test_developer_cannot_start_authorized_work(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.START_AUTHORIZED_WORK,
            work_authorized=True,
        )

        self.assertTrue(errors)

    # Authorized propagation

    def test_work_item_manager_can_propagate_authorized_bug(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_authorized_work_item(WorkItemType.BUG),
        )

        self.assertEqual(errors, [])

    def test_work_item_manager_can_propagate_authorized_change_request(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_authorized_work_item(
                WorkItemType.CHANGE_REQUEST
            ),
        )

        self.assertEqual(errors, [])

    def test_propagation_rejects_unauthorized_bug(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_work_item(WorkItemType.BUG),
        )

        self.assertTrue(
            any("not been explicitly authorized" in e for e in errors)
        )

    def test_propagation_rejects_unauthorized_change_request(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_work_item(WorkItemType.CHANGE_REQUEST),
        )

        self.assertTrue(errors)

    def test_propagation_rejects_incomplete_authorization_evidence(self):
        item = self.create_authorized_work_item()
        item.authorization_reason = None

        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            item,
        )

        self.assertTrue(
            any("incomplete" in e for e in errors)
        )

    def test_propagation_rejects_missing_authorization_identity(self):
        item = self.create_authorized_work_item()
        item.authorized_by = None

        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            item,
        )

        self.assertTrue(
            any("incomplete" in e for e in errors)
        )

    def test_propagation_rejects_missing_authorization_timestamp(self):
        item = self.create_authorized_work_item()
        item.authorized_at = None

        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            item,
        )

        self.assertTrue(
            any("incomplete" in e for e in errors)
        )

    def test_propagation_rejects_blank_authorization_identity(self):
        item = self.create_authorized_work_item()
        item.authorized_by = " "

        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            item,
        )

        self.assertTrue(
            any("invalid author identity" in e for e in errors)
        )

    def test_propagation_rejects_blank_authorization_reason(self):
        item = self.create_authorized_work_item()
        item.authorization_reason = " "

        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            item,
        )

        self.assertTrue(
            any("invalid reason" in e for e in errors)
        )

    def test_propagation_rejects_naive_authorization_timestamp(self):
        item = self.create_authorized_work_item()
        item.authorized_at = datetime(2026, 11, 21, 20, 0)

        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            item,
        )

        self.assertTrue(
            any("timezone-aware UTC" in e for e in errors)
        )

    def test_propagation_rejects_non_utc_authorization_timestamp(self):
        item = self.create_authorized_work_item()
        item.authorized_at = datetime(
            2026,
            11,
            21,
            20,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        )

        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            item,
        )

        self.assertTrue(
            any("timezone-aware UTC" in e for e in errors)
        )

    def test_product_manager_cannot_propagate_authorized_work(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_authorized_work_item(),
        )

        self.assertTrue(errors)

    def test_developer_cannot_propagate_authorized_work(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_authorized_work_item(),
        )

        self.assertTrue(errors)

    def test_qa_cannot_propagate_authorized_work(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_authorized_work_item(),
        )

        self.assertTrue(errors)

    def test_reviewer_cannot_propagate_authorized_work(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_authorized_work_item(),
        )

        self.assertTrue(errors)

    def test_orchestrator_cannot_propagate_authorized_work(self):
        errors = self.validate(
            AgentRole.ORCHESTRATOR,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_authorized_work_item(),
        )

        self.assertTrue(errors)

    def test_propagation_rejects_non_bug_and_non_change_request(self):
        unsupported_types = (
            WorkItemType.EPIC,
            WorkItemType.FEATURE,
            WorkItemType.USE_CASE,
            WorkItemType.REQUIREMENT,
            WorkItemType.DEVELOPMENT_TASK,
            WorkItemType.SUPPORTING_TASK,
            WorkItemType.TEST_CASE,
            WorkItemType.CODE_REVIEW_TASK,
        )

        for work_item_type in unsupported_types:
            with self.subTest(work_item_type=work_item_type):
                errors = self.validate(
                    AgentRole.WORK_ITEM_MANAGER,
                    WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
                    self.create_authorized_work_item(work_item_type),
                )

                self.assertTrue(
                    any(
                        "only be initiated by a Bug or Change Request" in e
                        for e in errors
                    )
                )

    def test_is_permitted_accepts_valid_authorized_propagation(self):
        result = PermissionRules.is_permitted(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_authorized_work_item(),
        )

        self.assertTrue(result)

    def test_is_permitted_rejects_unauthorized_propagation(self):
        result = PermissionRules.is_permitted(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.PROPAGATE_AUTHORIZED_WORK,
            self.create_work_item(WorkItemType.BUG),
        )

        self.assertFalse(result)


    # Development

    def test_developer_can_implement_development_work(self):
        for work_item_type in PermissionRules.DEVELOPER_IMPLEMENTATION_TYPES:
            with self.subTest(work_item_type=work_item_type):
                errors = self.validate(
                    AgentRole.DEVELOPER,
                    WorkItemOperation.IMPLEMENT,
                    self.create_work_item(work_item_type),
                )
                self.assertEqual(errors, [])

    def test_developer_cannot_implement_requirement(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.IMPLEMENT,
            self.create_work_item(WorkItemType.REQUIREMENT),
        )

        self.assertTrue(errors)

    def test_developer_can_submit_development_task_for_test(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.SUBMIT_FOR_TEST,
            self.create_work_item(WorkItemType.DEVELOPMENT_TASK),
        )

        self.assertEqual(errors, [])

    def test_developer_can_submit_bug_fix_for_test(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.SUBMIT_FOR_TEST,
            self.create_work_item(WorkItemType.BUG),
        )

        self.assertEqual(errors, [])

    def test_developer_cannot_submit_requirement_for_test(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.SUBMIT_FOR_TEST,
            self.create_work_item(WorkItemType.REQUIREMENT),
        )

        self.assertTrue(errors)

    def test_qa_cannot_submit_development_task_for_test(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.SUBMIT_FOR_TEST,
            self.create_work_item(WorkItemType.DEVELOPMENT_TASK),
        )

        self.assertTrue(errors)

    # Code review

    def test_reviewer_can_perform_code_review(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.PERFORM_CODE_REVIEW,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
        )

        self.assertEqual(errors, [])

    def test_developer_cannot_perform_code_review(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.PERFORM_CODE_REVIEW,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
        )

        self.assertTrue(errors)

    def test_code_review_requires_code_review_task(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.PERFORM_CODE_REVIEW,
            self.create_work_item(WorkItemType.DEVELOPMENT_TASK),
        )

        self.assertTrue(errors)

    def test_reviewer_can_approve_code_review(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.APPROVE_CODE_REVIEW,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
            actor_id="Reviewer-01",
            related_developer_id="Developer-01",
        )

        self.assertEqual(errors, [])

    def test_reviewer_cannot_approve_own_development_work(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.APPROVE_CODE_REVIEW,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
            actor_id="Agent-01",
            related_developer_id="Agent-01",
        )

        self.assertTrue(
            any("must be different agents" in e for e in errors)
        )

    def test_review_approval_requires_reviewer_identity(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.APPROVE_CODE_REVIEW,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
            related_developer_id="Developer-01",
        )

        self.assertTrue(any("Reviewer identity is required" in e for e in errors))

    def test_review_approval_requires_developer_identity(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.APPROVE_CODE_REVIEW,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
            actor_id="Reviewer-01",
        )

        self.assertTrue(any("Developer identity is required" in e for e in errors))

    def test_code_review_cannot_be_resolved_without_approval(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.RESOLVE_CODE_REVIEW,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
            actor_id="Reviewer-01",
            related_developer_id="Developer-01",
            review_approved=False,
        )

        self.assertTrue(any("without an approved review" in e for e in errors))

    def test_reviewer_can_resolve_approved_code_review(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.RESOLVE_CODE_REVIEW,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
            actor_id="Reviewer-01",
            related_developer_id="Developer-01",
            review_approved=True,
        )

        self.assertEqual(errors, [])

    def test_reviewer_cannot_resolve_requirement_through_review_operation(self):
        errors = self.validate(
            AgentRole.REVIEWER,
            WorkItemOperation.RESOLVE_CODE_REVIEW,
            self.create_work_item(WorkItemType.REQUIREMENT),
            actor_id="Reviewer-01",
            related_developer_id="Developer-01",
            review_approved=True,
        )

        self.assertTrue(errors)

    # QA testing and resolution

    def test_qa_can_execute_test_cases(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.EXECUTE_TEST_CASE,
            self.create_work_item(WorkItemType.TEST_CASE),
        )

        self.assertEqual(errors, [])

    def test_developer_cannot_execute_test_cases(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.EXECUTE_TEST_CASE,
            self.create_work_item(WorkItemType.TEST_CASE),
        )

        self.assertTrue(errors)

    def test_qa_can_record_test_results(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.RECORD_TEST_RESULT,
            self.create_work_item(WorkItemType.TEST_CASE),
        )

        self.assertEqual(errors, [])

    def test_qa_cannot_execute_non_test_case(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.EXECUTE_TEST_CASE,
            self.create_work_item(WorkItemType.REQUIREMENT),
        )

        self.assertTrue(errors)

    def test_qa_cannot_resolve_work_without_successful_verification(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.RESOLVE_VERIFIED_WORK,
            self.create_work_item(WorkItemType.REQUIREMENT),
            verification_passed=False,
            completion_criteria_met=True,
        )

        self.assertTrue(
            any("successful QA verification" in e for e in errors)
        )

    def test_qa_cannot_resolve_work_without_completion_criteria(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.RESOLVE_VERIFIED_WORK,
            self.create_work_item(WorkItemType.REQUIREMENT),
            verification_passed=True,
            completion_criteria_met=False,
        )

        self.assertTrue(
            any("completion criteria" in e for e in errors)
        )

    def test_qa_can_resolve_verified_requirement(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.RESOLVE_VERIFIED_WORK,
            self.create_work_item(WorkItemType.REQUIREMENT),
            verification_passed=True,
            completion_criteria_met=True,
        )

        self.assertEqual(errors, [])

    def test_qa_can_resolve_verified_feature(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.RESOLVE_VERIFIED_WORK,
            self.create_work_item(WorkItemType.FEATURE),
            verification_passed=True,
            completion_criteria_met=True,
        )

        self.assertEqual(errors, [])

    def test_qa_can_resolve_verified_bug(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.RESOLVE_VERIFIED_WORK,
            self.create_work_item(WorkItemType.BUG),
            verification_passed=True,
            completion_criteria_met=True,
        )

        self.assertEqual(errors, [])

    def test_qa_cannot_resolve_code_review_task(self):
        errors = self.validate(
            AgentRole.QA,
            WorkItemOperation.RESOLVE_VERIFIED_WORK,
            self.create_work_item(WorkItemType.CODE_REVIEW_TASK),
            verification_passed=True,
            completion_criteria_met=True,
        )

        self.assertTrue(errors)

    def test_developer_cannot_resolve_development_task(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.RESOLVE_VERIFIED_WORK,
            self.create_work_item(WorkItemType.DEVELOPMENT_TASK),
            verification_passed=True,
            completion_criteria_met=True,
        )

        self.assertTrue(errors)

    # Blocking and removal

    def test_authorized_roles_can_block_work_with_reason(self):
        for role in PermissionRules.BLOCKING_ROLES:
            with self.subTest(role=role):
                errors = self.validate(
                    role,
                    WorkItemOperation.BLOCK,
                    reason="Waiting for an external dependency.",
                )
                self.assertEqual(errors, [])

    def test_blocking_requires_reason(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.BLOCK,
            reason=" ",
        )

        self.assertTrue(any("reason is required" in e for e in errors))

    def test_orchestrator_cannot_block_work_directly(self):
        errors = self.validate(
            AgentRole.ORCHESTRATOR,
            WorkItemOperation.BLOCK,
            reason="Coordination issue.",
        )

        self.assertTrue(errors)

    def test_only_work_item_manager_can_unblock_work(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.UNBLOCK,
            reason="Dependency has been cleared.",
        )

        self.assertEqual(errors, [])

    def test_product_manager_cannot_unblock_work_directly(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.UNBLOCK,
            reason="Dependency has been cleared.",
        )

        self.assertTrue(errors)

    def test_unblocking_requires_reason(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.UNBLOCK,
            reason=" ",
        )

        self.assertTrue(any("reason is required" in e for e in errors))

    def test_only_product_manager_can_remove_work(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.REMOVE,
            reason="Duplicate requirement.",
        )

        self.assertEqual(errors, [])

    def test_developer_cannot_remove_work(self):
        errors = self.validate(
            AgentRole.DEVELOPER,
            WorkItemOperation.REMOVE,
            reason="No longer needed.",
        )

        self.assertTrue(errors)

    def test_removal_requires_reason(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.REMOVE,
            reason=" ",
        )

        self.assertTrue(any("reason is required" in e for e in errors))

    # Orchestrator and Work Item Manager responsibilities

    def test_orchestrator_can_coordinate_workflow(self):
        errors = self.validate(
            AgentRole.ORCHESTRATOR,
            WorkItemOperation.COORDINATE_WORKFLOW,
        )

        self.assertEqual(errors, [])

    def test_product_manager_cannot_use_orchestrator_operation(self):
        errors = self.validate(
            AgentRole.PRODUCT_MANAGER,
            WorkItemOperation.COORDINATE_WORKFLOW,
        )

        self.assertTrue(errors)

    def test_only_work_item_manager_can_enforce_workflow(self):
        errors = self.validate(
            AgentRole.WORK_ITEM_MANAGER,
            WorkItemOperation.ENFORCE_WORKFLOW,
        )

        self.assertEqual(errors, [])

    def test_orchestrator_cannot_enforce_workflow_directly(self):
        errors = self.validate(
            AgentRole.ORCHESTRATOR,
            WorkItemOperation.ENFORCE_WORKFLOW,
        )

        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
