from enum import StrEnum


class WorkItemState(StrEnum):
    PROPOSED = "Proposed"
    IN_WORK = "In Work"
    IN_TEST = "In Test"
    RESOLVED = "Resolved"
    BLOCKED = "Blocked"
    REMOVED = "Removed"


class CodeReviewState(StrEnum):
    PROPOSED = "Proposed"
    IN_WORK = "In Work"
    REVIEW = "Review"
    RESOLVED = "Resolved"


class ReviewResult(StrEnum):
    PENDING = "Pending"
    CHANGES_REQUESTED = "Changes Requested"
    APPROVED = "Approved"
