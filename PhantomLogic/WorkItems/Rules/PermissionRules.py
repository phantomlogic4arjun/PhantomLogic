

from datetime import timedelta

from enum import StrEnum

from PhantomLogic.WorkItems.Models.WorkItem import WorkItem
from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType


class AgentRole(StrEnum):
    ORCHESTRATOR = "Orchestrator"
    PRODUCT_MANAGER = "Product Manager"
    DEVELOPER = "Developer"
    REVIEWER = "Reviewer"
    QA = "QA"
    WORK_ITEM_MANAGER = "Work Item Manager"


class WorkItemOperation(StrEnum):
    CREATE_WORK_ITEM = "Create Work Item"
    CREATE_BUG = "Create Bug"
    CREATE_TEST_CASE = "Create Test Case"

    UPDATE_SCOPE = "Update Scope"
    UPDATE_IMPLEMENTATION = "Update Implementation"
    MANAGE_RELATIONSHIPS = "Manage Relationships"

    AUTHORIZE_WORK = "Authorize Work"
    START_AUTHORIZED_WORK = "Start Authorized Work"
    PROPAGATE_AUTHORIZED_WORK = "Propagate Authorized Work"

    IMPLEMENT = "Implement"
    SUBMIT_FOR_TEST = "Submit for Test"

    PERFORM_CODE_REVIEW = "Perform Code Review"
    APPROVE_CODE_REVIEW = "Approve Code Review"
    RESOLVE_CODE_REVIEW = "Resolve Code Review"

    EXECUTE_TEST_CASE = "Execute Test Case"
    RECORD_TEST_RESULT = "Record Test Result"
    RESOLVE_VERIFIED_WORK = "Resolve Verified Work"

    BLOCK = "Block"
    UNBLOCK = "Unblock"
    REMOVE = "Remove"

    COORDINATE_WORKFLOW = "Coordinate Workflow"
    ENFORCE_WORKFLOW = "Enforce Workflow"


class PermissionRules:
    """
    Defines which agent roles may perform work-item operations.

    This class validates authorization only. It does not execute operations,
    change work-item state, or replace state-transition and completion rules.
    """

    PRODUCT_MANAGER_SCOPE_TYPES = {
        WorkItemType.EPIC,
        WorkItemType.FEATURE,
        WorkItemType.USE_CASE,
        WorkItemType.REQUIREMENT,
        WorkItemType.CHANGE_REQUEST,
    }

    PRODUCT_MANAGER_AUTHORIZATION_TYPES = {
        WorkItemType.FEATURE,
        WorkItemType.USE_CASE,
        WorkItemType.REQUIREMENT,
        WorkItemType.DEVELOPMENT_TASK,
        WorkItemType.SUPPORTING_TASK,
        WorkItemType.BUG,
        WorkItemType.CHANGE_REQUEST,
    }

    AUTHORIZED_PROPAGATION_TYPES = {
        WorkItemType.BUG,
        WorkItemType.CHANGE_REQUEST,
    }

    DEVELOPER_IMPLEMENTATION_TYPES = {
        WorkItemType.DEVELOPMENT_TASK,
        WorkItemType.SUPPORTING_TASK,
        WorkItemType.BUG,
        WorkItemType.CHANGE_REQUEST,
    }

    DEVELOPER_TEST_SUBMISSION_TYPES = {
        WorkItemType.DEVELOPMENT_TASK,
        WorkItemType.SUPPORTING_TASK,
        WorkItemType.BUG,
        WorkItemType.CHANGE_REQUEST,
    }

    QA_RESOLUTION_TYPES = {
        WorkItemType.TEST_CASE,
        WorkItemType.DEVELOPMENT_TASK,
        WorkItemType.SUPPORTING_TASK,
        WorkItemType.REQUIREMENT,
        WorkItemType.USE_CASE,
        WorkItemType.FEATURE,
        WorkItemType.BUG,
        WorkItemType.CHANGE_REQUEST,
    }

    BLOCKING_ROLES = {
        AgentRole.PRODUCT_MANAGER,
        AgentRole.DEVELOPER,
        AgentRole.REVIEWER,
        AgentRole.QA,
    }

    @classmethod
    def validate_permission(
        cls,
        agent_role: AgentRole,
        operation: WorkItemOperation,
        work_item: WorkItem,
        *,
        actor_id: str | None = None,
        related_developer_id: str | None = None,
        reason: str | None = None,
        work_authorized: bool = False,
        review_approved: bool = False,
        verification_passed: bool = False,
        completion_criteria_met: bool = False,
    ) -> list[str]:
        """
        Return permission errors for an attempted operation.

        An empty list means the role is authorized by these rules.
        Other business rules and state-transition checks must still pass.
        """

        if not isinstance(agent_role, AgentRole):
            return ["Agent role is invalid."]

        if not isinstance(operation, WorkItemOperation):
            return ["Work item operation is invalid."]

        if not isinstance(work_item, WorkItem):
            return ["Work item must be a WorkItem instance."]

        if not isinstance(work_item.work_item_type, WorkItemType):
            return ["Work item type is invalid."]

        if operation == WorkItemOperation.CREATE_WORK_ITEM:
            if agent_role != AgentRole.PRODUCT_MANAGER:
                return cls._denied(agent_role, operation)

            return []

        if operation == WorkItemOperation.CREATE_BUG:
            if agent_role != AgentRole.QA:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type != WorkItemType.BUG:
                return [
                    "Create Bug can only be used for a Bug work item."
                ]

            return []

        if operation == WorkItemOperation.CREATE_TEST_CASE:
            if agent_role not in {
                AgentRole.PRODUCT_MANAGER,
                AgentRole.QA,
            }:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type != WorkItemType.TEST_CASE:
                return [
                    "Create Test Case can only be used for a Test Case."
                ]

            return []

        if operation == WorkItemOperation.UPDATE_SCOPE:
            if agent_role != AgentRole.PRODUCT_MANAGER:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type not in cls.PRODUCT_MANAGER_SCOPE_TYPES:
                return [
                    f"Product Manager cannot update the scope of "
                    f"'{work_item.work_item_type.value}' through this operation."
                ]

            return []

        if operation == WorkItemOperation.UPDATE_IMPLEMENTATION:
            if agent_role != AgentRole.DEVELOPER:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type not in cls.DEVELOPER_IMPLEMENTATION_TYPES:
                return [
                    f"Developer cannot update implementation details for "
                    f"'{work_item.work_item_type.value}'."
                ]

            return []

        if operation == WorkItemOperation.MANAGE_RELATIONSHIPS:
            if agent_role not in {
                AgentRole.PRODUCT_MANAGER,
                AgentRole.WORK_ITEM_MANAGER,
            }:
                return cls._denied(agent_role, operation)

            return []

        if operation == WorkItemOperation.AUTHORIZE_WORK:
            if agent_role != AgentRole.PRODUCT_MANAGER:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type not in cls.PRODUCT_MANAGER_AUTHORIZATION_TYPES:
                return [
                    f"Product Manager cannot authorize work for "
                    f"'{work_item.work_item_type.value}' through this operation."
                ]

            if not cls._valid_identity(actor_id):
                return [
                    "Product Manager identity is required to authorize work."
                ]

            if not cls._valid_reason(reason):
                return [
                    "An authorization reason is required."
                ]

            return []

        if operation == WorkItemOperation.START_AUTHORIZED_WORK:
            if agent_role not in {
                AgentRole.PRODUCT_MANAGER,
                AgentRole.WORK_ITEM_MANAGER,
            }:
                return cls._denied(agent_role, operation)

            if not work_authorized:
                return [
                    "Work must be explicitly authorized before it can start."
                ]

            return []

        if operation == WorkItemOperation.PROPAGATE_AUTHORIZED_WORK:
            if agent_role != AgentRole.WORK_ITEM_MANAGER:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type not in cls.AUTHORIZED_PROPAGATION_TYPES:
                return [
                    "Authorized propagation can only be initiated by "
                    "a Bug or Change Request."
                ]

            authorization_errors = cls._validate_authorization_evidence(
                work_item
            )

            if authorization_errors:
                return authorization_errors

            return []

        if operation == WorkItemOperation.IMPLEMENT:
            if agent_role != AgentRole.DEVELOPER:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type not in cls.DEVELOPER_IMPLEMENTATION_TYPES:
                return [
                    f"Developer cannot implement "
                    f"'{work_item.work_item_type.value}' through this operation."
                ]

            return []

        if operation == WorkItemOperation.SUBMIT_FOR_TEST:
            if agent_role != AgentRole.DEVELOPER:
                return cls._denied(agent_role, operation)

            if (
                work_item.work_item_type
                not in cls.DEVELOPER_TEST_SUBMISSION_TYPES
            ):
                return [
                    f"Developer cannot submit "
                    f"'{work_item.work_item_type.value}' for testing."
                ]

            return []

        if operation == WorkItemOperation.PERFORM_CODE_REVIEW:
            if agent_role != AgentRole.REVIEWER:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type != WorkItemType.CODE_REVIEW_TASK:
                return [
                    "Code review can only be performed on a Code Review Task."
                ]

            return []

        if operation in {
            WorkItemOperation.APPROVE_CODE_REVIEW,
            WorkItemOperation.RESOLVE_CODE_REVIEW,
        }:
            if agent_role != AgentRole.REVIEWER:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type != WorkItemType.CODE_REVIEW_TASK:
                return [
                    "Only a Code Review Task can be approved or resolved "
                    "through code-review operations."
                ]

            if not cls._valid_identity(actor_id):
                return ["Reviewer identity is required."]

            if not cls._valid_identity(related_developer_id):
                return ["Related Developer identity is required."]

            if actor_id.strip() == related_developer_id.strip():
                return [
                    "The Developer and Reviewer must be different agents."
                ]

            if operation == WorkItemOperation.RESOLVE_CODE_REVIEW:
                if not review_approved:
                    return [
                        "Code Review Task cannot be resolved "
                        "without an approved review."
                    ]

            return []

        if operation == WorkItemOperation.EXECUTE_TEST_CASE:
            if agent_role != AgentRole.QA:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type != WorkItemType.TEST_CASE:
                return [
                    "QA can execute tests only on Test Case work items."
                ]

            return []

        if operation == WorkItemOperation.RECORD_TEST_RESULT:
            if agent_role != AgentRole.QA:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type != WorkItemType.TEST_CASE:
                return [
                    "Test results can only be recorded against Test Cases."
                ]

            return []

        if operation == WorkItemOperation.RESOLVE_VERIFIED_WORK:
            if agent_role != AgentRole.QA:
                return cls._denied(agent_role, operation)

            if work_item.work_item_type not in cls.QA_RESOLUTION_TYPES:
                return [
                    f"QA cannot resolve '{work_item.work_item_type.value}' "
                    "through the verification operation."
                ]

            if not verification_passed:
                return [
                    "Work cannot be resolved without successful QA verification."
                ]

            if not completion_criteria_met:
                return [
                    "Work cannot be resolved until its completion criteria are met."
                ]

            return []

        if operation == WorkItemOperation.BLOCK:
            if agent_role not in cls.BLOCKING_ROLES:
                return cls._denied(agent_role, operation)

            if not cls._valid_reason(reason):
                return ["A reason is required when blocking work."]

            return []

        if operation == WorkItemOperation.UNBLOCK:
            if agent_role != AgentRole.WORK_ITEM_MANAGER:
                return cls._denied(agent_role, operation)

            if not cls._valid_reason(reason):
                return ["A reason is required when clearing a blocker."]

            return []

        if operation == WorkItemOperation.REMOVE:
            if agent_role != AgentRole.PRODUCT_MANAGER:
                return cls._denied(agent_role, operation)

            if not cls._valid_reason(reason):
                return ["A reason is required when removing work."]

            return []

        if operation == WorkItemOperation.COORDINATE_WORKFLOW:
            if agent_role != AgentRole.ORCHESTRATOR:
                return cls._denied(agent_role, operation)

            return []

        if operation == WorkItemOperation.ENFORCE_WORKFLOW:
            if agent_role != AgentRole.WORK_ITEM_MANAGER:
                return cls._denied(agent_role, operation)

            return []

        return [
            f"Operation '{operation.value}' is not supported."
        ]

    @classmethod
    def _validate_authorization_evidence(
        cls,
        work_item: WorkItem,
    ) -> list[str]:
        """
        Validate persisted authorization evidence before propagation.

        All three authorization fields must be present and valid.
        """

        authorized_by = work_item.authorized_by
        authorized_at = work_item.authorized_at
        authorization_reason = work_item.authorization_reason

        fields = (
            authorized_by,
            authorized_at,
            authorization_reason,
        )

        if all(value is None for value in fields):
            return [
                "Work has not been explicitly authorized by the Product Manager."
            ]

        if any(value is None for value in fields):
            return [
                "Authorization evidence is incomplete."
            ]

        if not cls._valid_identity(authorized_by):
            return [
                "Authorization evidence contains an invalid author identity."
            ]

        if not cls._valid_reason(authorization_reason):
            return [
                "Authorization evidence contains an invalid reason."
            ]

        if not cls._valid_utc_timestamp(authorized_at):
            return [
                "Authorization timestamp must be timezone-aware UTC."
            ]

        return []

    @staticmethod
    def _valid_identity(value: str | None) -> bool:
        return (
            isinstance(value, str)
            and bool(value.strip())
        )

    @staticmethod
    def _valid_reason(value: str | None) -> bool:
        return (
            isinstance(value, str)
            and bool(value.strip())
        )

    @staticmethod
    def _valid_utc_timestamp(value) -> bool:
        if value is None:
            return False

        if not hasattr(value, "tzinfo"):
            return False

        if value.tzinfo is None:
            return False

        try:
            return value.utcoffset() == timedelta(0)
        except (TypeError, ValueError):
            return False

    @classmethod
    def is_permitted(
        cls,
        agent_role: AgentRole,
        operation: WorkItemOperation,
        work_item: WorkItem,
        **context,
    ) -> bool:
        """Return True only when the permission validation succeeds."""

        return not cls.validate_permission(
            agent_role,
            operation,
            work_item,
            **context,
        )

    @staticmethod
    def _denied(
        agent_role: AgentRole,
        operation: WorkItemOperation,
    ) -> list[str]:
        return [
            f"Agent role '{agent_role.value}' is not authorized "
            f"to perform '{operation.value}'."
        ]
