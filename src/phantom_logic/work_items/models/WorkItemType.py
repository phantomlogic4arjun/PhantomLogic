from enum import StrEnum


class WorkItemType(StrEnum):
    EPIC = "Epic"
    FEATURE = "Feature"
    USE_CASE = "Use Case"
    REQUIREMENT = "Requirement"
    DEVELOPMENT_TASK = "Development Task"
    SUPPORTING_TASK = "Supporting Task"
    TEST_CASE = "Test Case"
    BUG = "Bug"
    CHANGE_REQUEST = "Change Request"
    CODE_REVIEW_TASK = "Code Review Task"
