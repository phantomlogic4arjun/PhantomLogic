from dataclasses import dataclass
from enum import StrEnum


class RelationshipType(StrEnum):
    PARENT_CHILD = "Parent Child"
    AFFECTED_REQUIREMENT = "Affected Requirement"
    VIOLATED_REQUIREMENT = "Violated Requirement"
    FAILED_TEST_CASE = "Failed Test Case"


@dataclass(frozen=True)
class WorkItemRelationship:
    source_id: str
    target_id: str
    relationship_type: RelationshipType
