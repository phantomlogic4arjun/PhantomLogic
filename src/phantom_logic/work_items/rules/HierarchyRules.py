
from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.RelationshipRules import RelationshipRules


class HierarchyRules:

    REQUIRED_PARENT_TYPES = {
        WorkItemType.USE_CASE: WorkItemType.FEATURE,
        WorkItemType.REQUIREMENT: WorkItemType.USE_CASE,
        WorkItemType.DEVELOPMENT_TASK: WorkItemType.USE_CASE,
        WorkItemType.SUPPORTING_TASK: WorkItemType.FEATURE,
        WorkItemType.CODE_REVIEW_TASK: WorkItemType.FEATURE,
        WorkItemType.TEST_CASE: WorkItemType.REQUIREMENT,
    }

    @classmethod
    def validate_parent_child_relationships(
        cls,
        work_items: dict[str, WorkItem],
    ) -> list[str]:

        errors = []
        parent_map = {}
        graph = {}
        seen_edges = set()

        for work_item_id, work_item in work_items.items():

            if not isinstance(work_item, WorkItem):
                errors.append(
                    f"Work item entry '{work_item_id}' is not a WorkItem instance."
                )
                continue

            if work_item.id != work_item_id:
                errors.append(
                    f"Work item dictionary key '{work_item_id}' "
                    f"does not match work item ID '{work_item.id}'."
                )

            if not isinstance(work_item.work_item_type, WorkItemType):
                errors.append(
                    f"Work item '{work_item_id}' has an invalid work item type."
                )
                continue

            for relationship in work_item.relationships:

                if not isinstance(relationship, WorkItemRelationship):
                    errors.append(
                        f"Work item '{work_item_id}' contains an invalid relationship object."
                    )
                    continue

                if relationship.relationship_type != RelationshipType.PARENT_CHILD:
                    continue

                if relationship.source_id != work_item.id:
                    errors.append(
                        f"Parent relationship source '{relationship.source_id}' "
                        f"does not match owning work item '{work_item.id}'."
                    )
                    continue

                if relationship.target_id == work_item.id:
                    errors.append(
                        f"Work item '{work_item.id}' cannot be its own parent or child."
                    )
                    continue

                target = work_items.get(relationship.target_id)

                if target is None:
                    errors.append(
                        f"Child work item '{relationship.target_id}' "
                        f"does not exist."
                    )
                    continue

                if not isinstance(target, WorkItem):
                    errors.append(
                        f"Child work item '{relationship.target_id}' "
                        "is not a WorkItem instance."
                    )
                    continue

                edge = (work_item.id, target.id)

                if edge in seen_edges:
                    errors.append(
                        f"Duplicate parent-child relationship from "
                        f"'{work_item.id}' to '{target.id}'."
                    )
                    continue

                seen_edges.add(edge)
                graph.setdefault(work_item.id, []).append(target.id)

                existing_parent = parent_map.get(target.id)

                if existing_parent is not None and existing_parent != work_item.id:
                    errors.append(
                        f"Work item '{target.id}' has multiple parents: "
                        f"'{existing_parent}' and '{work_item.id}'."
                    )
                else:
                    parent_map[target.id] = work_item.id

                if not isinstance(target.work_item_type, WorkItemType):
                    errors.append(
                        f"Child work item '{target.id}' has an invalid work item type."
                    )
                    continue

                if not RelationshipRules.is_valid_relationship(
                    work_item.work_item_type,
                    RelationshipType.PARENT_CHILD,
                    target.work_item_type,
                ):
                    errors.append(
                        f"Parent-child relationship from '{work_item.id}' "
                        f"({work_item.work_item_type.value}) to "
                        f"'{target.id}' ({target.work_item_type.value}) "
                        "is not permitted."
                    )

        errors.extend(cls._validate_cycles(graph))

        return errors

    @staticmethod
    def _validate_cycles(
        graph: dict[str, list[str]],
    ) -> list[str]:

        errors = []
        visited = set()
        active_path = set()

        def visit(work_item_id: str) -> None:

            if work_item_id in active_path:
                errors.append(
                    f"Hierarchy cycle detected involving '{work_item_id}'."
                )
                return

            if work_item_id in visited:
                return

            visited.add(work_item_id)
            active_path.add(work_item_id)

            for child_id in graph.get(work_item_id, []):
                visit(child_id)

            active_path.remove(work_item_id)

        for work_item_id in graph:
            visit(work_item_id)

        return errors

    @classmethod
    def validate_required_parents(
        cls,
        work_items: dict[str, WorkItem],
    ) -> list[str]:

        errors = []
        parent_types = {}

        for work_item in work_items.values():

            if not isinstance(work_item, WorkItem):
                continue

            if not isinstance(work_item.work_item_type, WorkItemType):
                continue

            for relationship in work_item.relationships:

                if not isinstance(relationship, WorkItemRelationship):
                    continue

                if relationship.relationship_type != RelationshipType.PARENT_CHILD:
                    continue

                if relationship.source_id != work_item.id:
                    continue

                target = work_items.get(relationship.target_id)

                if not isinstance(target, WorkItem):
                    continue

                if not isinstance(target.work_item_type, WorkItemType):
                    continue

                if RelationshipRules.is_valid_relationship(
                    work_item.work_item_type,
                    RelationshipType.PARENT_CHILD,
                    target.work_item_type,
                ):
                    parent_types.setdefault(target.id, []).append(
                        work_item.work_item_type
                    )

        for work_item_id, work_item in work_items.items():

            if not isinstance(work_item, WorkItem):
                continue

            required_parent_type = cls.REQUIRED_PARENT_TYPES.get(
                work_item.work_item_type
            )

            if required_parent_type is None:
                continue

            actual_parent_types = parent_types.get(work_item_id, [])

            if required_parent_type not in actual_parent_types:
                errors.append(
                    f"Work item '{work_item_id}' "
                    f"({work_item.work_item_type.value}) requires a parent "
                    f"of type '{required_parent_type.value}'."
                )

        return errors

    @classmethod
    def validate_required_children(
        cls,
        work_items: dict[str, WorkItem],
    ) -> list[str]:

        errors = []
        development_task_counts = {}
        code_review_task_counts = {}
        test_case_counts = {}

        for work_item in work_items.values():

            if not isinstance(work_item, WorkItem):
                continue

            if not isinstance(work_item.work_item_type, WorkItemType):
                continue

            for relationship in work_item.relationships:

                if not isinstance(relationship, WorkItemRelationship):
                    continue

                if relationship.relationship_type != RelationshipType.PARENT_CHILD:
                    continue

                if relationship.source_id != work_item.id:
                    continue

                target = work_items.get(relationship.target_id)

                if not isinstance(target, WorkItem):
                    continue

                if not isinstance(target.work_item_type, WorkItemType):
                    continue

                if not RelationshipRules.is_valid_relationship(
                    work_item.work_item_type,
                    RelationshipType.PARENT_CHILD,
                    target.work_item_type,
                ):
                    continue

                if target.work_item_type == WorkItemType.DEVELOPMENT_TASK:
                    development_task_counts[work_item.id] = (
                        development_task_counts.get(work_item.id, 0) + 1
                    )

                if target.work_item_type == WorkItemType.CODE_REVIEW_TASK:
                    code_review_task_counts[work_item.id] = (
                        code_review_task_counts.get(work_item.id, 0) + 1
                    )

                if target.work_item_type == WorkItemType.TEST_CASE:
                    test_case_counts[work_item.id] = (
                        test_case_counts.get(work_item.id, 0) + 1
                    )

        for work_item_id, work_item in work_items.items():

            if not isinstance(work_item, WorkItem):
                continue

            if work_item.work_item_type == WorkItemType.USE_CASE:
                count = development_task_counts.get(work_item_id, 0)

                if count != 1:
                    errors.append(
                        f"Use Case '{work_item_id}' must have exactly one "
                        f"Development Task; found {count}."
                    )

            if work_item.work_item_type == WorkItemType.FEATURE:
                count = code_review_task_counts.get(work_item_id, 0)

                if count != 1:
                    errors.append(
                        f"Feature '{work_item_id}' must have exactly one "
                        f"Code Review Task; found {count}."
                    )

            if work_item.work_item_type == WorkItemType.REQUIREMENT:
                count = test_case_counts.get(work_item_id, 0)

                if count != 1:
                    errors.append(
                        f"Requirement '{work_item_id}' must have exactly one "
                        f"Test Case; found {count}."
                    )

        return errors

    @classmethod
    def validate_requirement_test_case_build_numbers(
        cls,
        work_items: dict[str, WorkItem],
    ) -> list[str]:

        errors = []

        for work_item in work_items.values():

            if not isinstance(work_item, WorkItem):
                continue

            if work_item.work_item_type != WorkItemType.REQUIREMENT:
                continue

            for relationship in work_item.relationships:

                if not isinstance(relationship, WorkItemRelationship):
                    continue

                if relationship.relationship_type != RelationshipType.PARENT_CHILD:
                    continue

                if relationship.source_id != work_item.id:
                    continue

                test_case = work_items.get(relationship.target_id)

                if not isinstance(test_case, WorkItem):
                    continue

                if test_case.work_item_type != WorkItemType.TEST_CASE:
                    continue

                if work_item.build_number != test_case.build_number:
                    errors.append(
                        f"Requirement '{work_item.id}' and Test Case "
                        f"'{test_case.id}' must have the same build number."
                    )

        return errors


    @classmethod
    def validate_hierarchy(
        cls,
        work_items: dict[str, WorkItem],
    ) -> list[str]:

        errors = []

        errors.extend(
            cls.validate_parent_child_relationships(work_items)
        )

        errors.extend(
            cls.validate_required_parents(work_items)
        )

        errors.extend(
            cls.validate_required_children(work_items)
        )

        errors.extend(
            cls.validate_requirement_test_case_build_numbers(work_items)
        )

        return errors
