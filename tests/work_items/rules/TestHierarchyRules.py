
import unittest

from phantom_logic.work_items.models.WorkItem import WorkItem
from phantom_logic.work_items.models.WorkItemRelationship import (
    RelationshipType,
    WorkItemRelationship,
)
from phantom_logic.work_items.models.WorkItemType import WorkItemType
from phantom_logic.work_items.rules.HierarchyRules import HierarchyRules


class TestHierarchyRules(unittest.TestCase):

    def create_work_item(
        self,
        work_item_id,
        work_item_type,
        relationships=(),
        build_number=None,
    ):
        return WorkItem(
            id=work_item_id,
            title=f"Test {work_item_type.value}",
            work_item_type=work_item_type,
            created_by="ProductManager",
            relationships=relationships,
            build_number=build_number,
        )

    def create_parent_child_relationship(
        self,
        parent_id,
        child_id,
    ):
        return WorkItemRelationship(
            source_id=parent_id,
            target_id=child_id,
            relationship_type=RelationshipType.PARENT_CHILD,
        )

    def create_work_items(self):
        epic = self.create_work_item(
            "EPIC-001",
            WorkItemType.EPIC,
            (
                self.create_parent_child_relationship("EPIC-001", "FEAT-001"),
            ),
        )

        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship("FEAT-001", "UC-001"),
                self.create_parent_child_relationship("FEAT-001", "SUPPORT-001"),
                self.create_parent_child_relationship("FEAT-001", "REVIEW-001"),
            ),
        )

        use_case = self.create_work_item(
            "UC-001",
            WorkItemType.USE_CASE,
            (
                self.create_parent_child_relationship("UC-001", "REQ-001"),
                self.create_parent_child_relationship("UC-001", "DEV-001"),
            ),
        )

        requirement = self.create_work_item(
            "REQ-001",
            WorkItemType.REQUIREMENT,
            (
                self.create_parent_child_relationship("REQ-001", "TEST-001"),
            ),
        )

        development_task = self.create_work_item(
            "DEV-001",
            WorkItemType.DEVELOPMENT_TASK,
        )

        supporting_task = self.create_work_item(
            "SUPPORT-001",
            WorkItemType.SUPPORTING_TASK,
        )

        code_review_task = self.create_work_item(
            "REVIEW-001",
            WorkItemType.CODE_REVIEW_TASK,
        )

        test_case = self.create_work_item(
            "TEST-001",
            WorkItemType.TEST_CASE,
        )

        return {
            item.id: item
            for item in (
                epic,
                feature,
                use_case,
                requirement,
                development_task,
                supporting_task,
                code_review_task,
                test_case,
            )
        }

    # Parent-child relationship validation

    def test_empty_hierarchy_is_valid(self):
        self.assertEqual(
            HierarchyRules.validate_parent_child_relationships({}),
            [],
        )

    def test_valid_parent_child_hierarchy_is_accepted(self):
        errors = HierarchyRules.validate_parent_child_relationships(
            self.create_work_items()
        )
        self.assertEqual(errors, [])

    def test_all_allowed_parent_child_relationships_are_accepted(self):
        allowed_relationships = [
            (WorkItemType.EPIC, WorkItemType.FEATURE),
            (WorkItemType.FEATURE, WorkItemType.USE_CASE),
            (WorkItemType.FEATURE, WorkItemType.SUPPORTING_TASK),
            (WorkItemType.FEATURE, WorkItemType.CODE_REVIEW_TASK),
            (WorkItemType.USE_CASE, WorkItemType.REQUIREMENT),
            (WorkItemType.USE_CASE, WorkItemType.DEVELOPMENT_TASK),
            (WorkItemType.REQUIREMENT, WorkItemType.TEST_CASE),
        ]

        for index, (parent_type, child_type) in enumerate(
            allowed_relationships
        ):
            parent_id = f"PARENT-{index}"
            child_id = f"CHILD-{index}"

            parent = self.create_work_item(
                parent_id,
                parent_type,
                (
                    self.create_parent_child_relationship(
                        parent_id,
                        child_id,
                    ),
                ),
            )

            child = self.create_work_item(child_id, child_type)

            with self.subTest(
                parent_type=parent_type,
                child_type=child_type,
            ):
                errors = HierarchyRules.validate_parent_child_relationships(
                    {
                        parent_id: parent,
                        child_id: child,
                    }
                )
                self.assertEqual(errors, [])

    def test_invalid_parent_child_type_is_rejected(self):
        parent = self.create_work_item(
            "REQ-001",
            WorkItemType.REQUIREMENT,
            (
                self.create_parent_child_relationship(
                    "REQ-001",
                    "UC-001",
                ),
            ),
        )
        child = self.create_work_item("UC-001", WorkItemType.USE_CASE)

        errors = HierarchyRules.validate_parent_child_relationships(
            {"REQ-001": parent, "UC-001": child}
        )

        self.assertTrue(any("is not permitted" in error for error in errors))

    def test_relationship_with_incorrect_source_is_rejected(self):
        parent = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship(
                    "FEAT-999",
                    "UC-001",
                ),
            ),
        )
        child = self.create_work_item("UC-001", WorkItemType.USE_CASE)

        errors = HierarchyRules.validate_parent_child_relationships(
            {"FEAT-001": parent, "UC-001": child}
        )

        self.assertTrue(
            any("does not match owning work item" in error for error in errors)
        )

    def test_missing_child_is_rejected(self):
        parent = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship(
                    "FEAT-001",
                    "UC-999",
                ),
            ),
        )

        errors = HierarchyRules.validate_parent_child_relationships(
            {"FEAT-001": parent}
        )

        self.assertTrue(any("does not exist" in error for error in errors))

    def test_child_with_multiple_parents_is_rejected(self):
        first_parent = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship(
                    "FEAT-001",
                    "UC-001",
                ),
            ),
        )
        second_parent = self.create_work_item(
            "FEAT-002",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship(
                    "FEAT-002",
                    "UC-001",
                ),
            ),
        )
        child = self.create_work_item("UC-001", WorkItemType.USE_CASE)

        errors = HierarchyRules.validate_parent_child_relationships(
            {
                "FEAT-001": first_parent,
                "FEAT-002": second_parent,
                "UC-001": child,
            }
        )

        self.assertTrue(any("has multiple parents" in error for error in errors))

    def test_duplicate_parent_child_relationship_is_rejected(self):
        relationship = self.create_parent_child_relationship(
            "FEAT-001",
            "UC-001",
        )

        parent = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (relationship, relationship),
        )
        child = self.create_work_item("UC-001", WorkItemType.USE_CASE)

        errors = HierarchyRules.validate_parent_child_relationships(
            {"FEAT-001": parent, "UC-001": child}
        )

        self.assertTrue(
            any("Duplicate parent-child relationship" in error for error in errors)
        )

    def test_self_referencing_relationship_is_rejected(self):
        parent = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship(
                    "FEAT-001",
                    "FEAT-001",
                ),
            ),
        )

        errors = HierarchyRules.validate_parent_child_relationships(
            {"FEAT-001": parent}
        )

        self.assertTrue(
            any("cannot be its own parent or child" in error for error in errors)
        )

    def test_hierarchy_cycle_is_rejected(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship(
                    "FEAT-001",
                    "UC-001",
                ),
            ),
        )
        use_case = self.create_work_item(
            "UC-001",
            WorkItemType.USE_CASE,
            (
                self.create_parent_child_relationship(
                    "UC-001",
                    "FEAT-001",
                ),
            ),
        )

        errors = HierarchyRules.validate_parent_child_relationships(
            {"FEAT-001": feature, "UC-001": use_case}
        )

        self.assertTrue(
            any("Hierarchy cycle detected" in error for error in errors)
        )

    def test_dictionary_key_must_match_work_item_id(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
        )

        errors = HierarchyRules.validate_parent_child_relationships(
            {"FEAT-999": feature}
        )

        self.assertTrue(
            any("does not match work item ID" in error for error in errors)
        )

    def test_non_work_item_dictionary_entry_is_rejected(self):
        errors = HierarchyRules.validate_parent_child_relationships(
            {"FEAT-001": "Not a work item"}
        )

        self.assertTrue(
            any("is not a WorkItem instance" in error for error in errors)
        )

    def test_invalid_work_item_type_is_rejected(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
        )
        feature.work_item_type = "Feature"

        errors = HierarchyRules.validate_parent_child_relationships(
            {"FEAT-001": feature}
        )

        self.assertTrue(
            any("invalid work item type" in error for error in errors)
        )

    def test_non_parent_child_relationship_is_ignored(self):
        change_request = self.create_work_item(
            "CR-001",
            WorkItemType.CHANGE_REQUEST,
            (
                WorkItemRelationship(
                    source_id="CR-001",
                    target_id="REQ-001",
                    relationship_type=RelationshipType.AFFECTED_REQUIREMENT,
                ),
            ),
        )
        requirement = self.create_work_item(
            "REQ-001",
            WorkItemType.REQUIREMENT,
        )

        errors = HierarchyRules.validate_parent_child_relationships(
            {"CR-001": change_request, "REQ-001": requirement}
        )

        self.assertEqual(errors, [])

    def test_feature_does_not_require_an_epic_parent(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
        )

        errors = HierarchyRules.validate_required_parents(
            {"FEAT-001": feature}
        )

        self.assertEqual(errors, [])

    # Required parent validation

    def test_all_required_parent_types_are_defined(self):
        self.assertEqual(
            HierarchyRules.REQUIRED_PARENT_TYPES,
            {
                WorkItemType.USE_CASE: WorkItemType.FEATURE,
                WorkItemType.REQUIREMENT: WorkItemType.USE_CASE,
                WorkItemType.DEVELOPMENT_TASK: WorkItemType.USE_CASE,
                WorkItemType.SUPPORTING_TASK: WorkItemType.FEATURE,
                WorkItemType.CODE_REVIEW_TASK: WorkItemType.FEATURE,
                WorkItemType.TEST_CASE: WorkItemType.REQUIREMENT,
            },
        )

    def test_complete_hierarchy_has_all_required_parents(self):
        errors = HierarchyRules.validate_required_parents(
            self.create_work_items()
        )
        self.assertEqual(errors, [])

    def test_missing_required_parent_is_rejected(self):
        use_case = self.create_work_item(
            "UC-001",
            WorkItemType.USE_CASE,
        )

        errors = HierarchyRules.validate_required_parents(
            {"UC-001": use_case}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("requires a parent", errors[0])
        self.assertIn("Feature", errors[0])

    def test_requirement_requires_use_case_parent(self):
        requirement = self.create_work_item(
            "REQ-001",
            WorkItemType.REQUIREMENT,
        )

        errors = HierarchyRules.validate_required_parents(
            {"REQ-001": requirement}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Use Case", errors[0])

    def test_development_task_requires_use_case_parent(self):
        task = self.create_work_item(
            "DEV-001",
            WorkItemType.DEVELOPMENT_TASK,
        )

        errors = HierarchyRules.validate_required_parents(
            {"DEV-001": task}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Use Case", errors[0])

    def test_supporting_task_requires_feature_parent(self):
        task = self.create_work_item(
            "SUPPORT-001",
            WorkItemType.SUPPORTING_TASK,
        )

        errors = HierarchyRules.validate_required_parents(
            {"SUPPORT-001": task}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Feature", errors[0])

    def test_code_review_task_requires_feature_parent(self):
        task = self.create_work_item(
            "REVIEW-001",
            WorkItemType.CODE_REVIEW_TASK,
        )

        errors = HierarchyRules.validate_required_parents(
            {"REVIEW-001": task}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Feature", errors[0])

    def test_test_case_requires_requirement_parent(self):
        test_case = self.create_work_item(
            "TEST-001",
            WorkItemType.TEST_CASE,
        )

        errors = HierarchyRules.validate_required_parents(
            {"TEST-001": test_case}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Requirement", errors[0])

    def test_bug_and_change_request_do_not_require_hierarchy_parents(self):
        bug = self.create_work_item("BUG-001", WorkItemType.BUG)
        change_request = self.create_work_item(
            "CR-001",
            WorkItemType.CHANGE_REQUEST,
        )

        errors = HierarchyRules.validate_required_parents(
            {"BUG-001": bug, "CR-001": change_request}
        )

        self.assertEqual(errors, [])

    # Required child validation

    def test_feature_requires_exactly_one_code_review_task(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
        )

        errors = HierarchyRules.validate_required_children(
            {"FEAT-001": feature}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("exactly one Code Review Task", errors[0])
        self.assertIn("found 0", errors[0])

    def test_feature_with_one_code_review_task_is_valid(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship(
                    "FEAT-001",
                    "REVIEW-001",
                ),
            ),
        )
        review_task = self.create_work_item(
            "REVIEW-001",
            WorkItemType.CODE_REVIEW_TASK,
        )

        errors = HierarchyRules.validate_required_children(
            {"FEAT-001": feature, "REVIEW-001": review_task}
        )

        self.assertEqual(errors, [])

    def test_feature_with_multiple_code_review_tasks_is_rejected(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship("FEAT-001", "REVIEW-001"),
                self.create_parent_child_relationship("FEAT-001", "REVIEW-002"),
            ),
        )
        review_one = self.create_work_item(
            "REVIEW-001",
            WorkItemType.CODE_REVIEW_TASK,
        )
        review_two = self.create_work_item(
            "REVIEW-002",
            WorkItemType.CODE_REVIEW_TASK,
        )

        errors = HierarchyRules.validate_required_children(
            {
                "FEAT-001": feature,
                "REVIEW-001": review_one,
                "REVIEW-002": review_two,
            }
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("found 2", errors[0])

    def test_use_case_requires_exactly_one_development_task(self):
        use_case = self.create_work_item(
            "UC-001",
            WorkItemType.USE_CASE,
        )

        errors = HierarchyRules.validate_required_children(
            {"UC-001": use_case}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("exactly one Development Task", errors[0])
        self.assertIn("found 0", errors[0])

    def test_use_case_with_one_development_task_is_valid(self):
        use_case = self.create_work_item(
            "UC-001",
            WorkItemType.USE_CASE,
            (
                self.create_parent_child_relationship("UC-001", "DEV-001"),
            ),
        )
        development_task = self.create_work_item(
            "DEV-001",
            WorkItemType.DEVELOPMENT_TASK,
        )

        errors = HierarchyRules.validate_required_children(
            {"UC-001": use_case, "DEV-001": development_task}
        )

        self.assertEqual(errors, [])

    def test_use_case_with_multiple_development_tasks_is_rejected(self):
        use_case = self.create_work_item(
            "UC-001",
            WorkItemType.USE_CASE,
            (
                self.create_parent_child_relationship("UC-001", "DEV-001"),
                self.create_parent_child_relationship("UC-001", "DEV-002"),
            ),
        )
        development_one = self.create_work_item(
            "DEV-001",
            WorkItemType.DEVELOPMENT_TASK,
        )
        development_two = self.create_work_item(
            "DEV-002",
            WorkItemType.DEVELOPMENT_TASK,
        )

        errors = HierarchyRules.validate_required_children(
            {
                "UC-001": use_case,
                "DEV-001": development_one,
                "DEV-002": development_two,
            }
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("found 2", errors[0])

    def test_invalid_relationship_does_not_count_as_required_child(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
            (
                self.create_parent_child_relationship("FEAT-001", "DEV-001"),
            ),
        )
        development_task = self.create_work_item(
            "DEV-001",
            WorkItemType.DEVELOPMENT_TASK,
        )

        errors = HierarchyRules.validate_required_children(
            {"FEAT-001": feature, "DEV-001": development_task}
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Code Review Task", errors[0])

    def test_multiple_requirements_each_have_one_test_case(self):
        use_case = self.create_work_item(
            "UC-001",
            WorkItemType.USE_CASE,
            (
                self.create_parent_child_relationship("UC-001", "REQ-001"),
                self.create_parent_child_relationship("UC-001", "REQ-002"),
                self.create_parent_child_relationship("UC-001", "DEV-001"),
            ),
        )

        requirement_one = self.create_work_item(
            "REQ-001",
            WorkItemType.REQUIREMENT,
            (
                self.create_parent_child_relationship("REQ-001", "TEST-001"),
            ),
        )

        requirement_two = self.create_work_item(
            "REQ-002",
            WorkItemType.REQUIREMENT,
            (
                self.create_parent_child_relationship("REQ-002", "TEST-002"),
            ),
        )

        development_task = self.create_work_item(
            "DEV-001",
            WorkItemType.DEVELOPMENT_TASK,
        )

        test_one = self.create_work_item("TEST-001", WorkItemType.TEST_CASE)
        test_two = self.create_work_item("TEST-002", WorkItemType.TEST_CASE)

        work_items = {
            item.id: item
            for item in (
                use_case,
                requirement_one,
                requirement_two,
                development_task,
                test_one,
                test_two,
            )
        }

        errors = HierarchyRules.validate_parent_child_relationships(work_items)

        self.assertEqual(errors, [])

    # Complete hierarchy validation

    def test_complete_hierarchy_passes_all_validation(self):
        errors = HierarchyRules.validate_hierarchy(
            self.create_work_items()
        )

        self.assertEqual(errors, [])

    def test_incomplete_hierarchy_reports_missing_requirements(self):
        feature = self.create_work_item(
            "FEAT-001",
            WorkItemType.FEATURE,
        )
        use_case = self.create_work_item(
            "UC-001",
            WorkItemType.USE_CASE,
        )

        errors = HierarchyRules.validate_hierarchy(
            {"FEAT-001": feature, "UC-001": use_case}
        )

        self.assertTrue(
            any("requires a parent" in error for error in errors)
        )
        self.assertTrue(
            any("Development Task" in error for error in errors)
        )
        self.assertTrue(
            any("Code Review Task" in error for error in errors)
        )

    def test_requirement_without_test_case_is_rejected(self):
        work_items = self.create_work_items()

        requirement = work_items["REQ-001"]
        requirement.relationships = ()

        errors = HierarchyRules.validate_required_children(work_items)

        self.assertTrue(
            any(
                "Requirement 'REQ-001' must have exactly one Test Case; found 0."
                in error
                for error in errors
            )
        )


    def test_requirement_with_multiple_test_cases_is_rejected(self):
        work_items = self.create_work_items()

        requirement = work_items["REQ-001"]
        requirement.relationships = (
            self.create_parent_child_relationship("REQ-001", "TEST-001"),
            self.create_parent_child_relationship("REQ-001", "TEST-002"),
        )

        work_items["TEST-002"] = self.create_work_item(
            "TEST-002",
            WorkItemType.TEST_CASE,
        )

        errors = HierarchyRules.validate_required_children(work_items)

        self.assertTrue(
            any(
                "Requirement 'REQ-001' must have exactly one Test Case; found 2."
                in error
                for error in errors
            )
        )


    def test_requirement_and_test_case_with_matching_build_numbers_are_accepted(self):
        work_items = self.create_work_items()

        work_items["REQ-001"].build_number = "1.01"
        work_items["TEST-001"].build_number = "1.01"

        errors = HierarchyRules.validate_hierarchy(work_items)

        self.assertEqual(errors, [])


    def test_requirement_and_test_case_with_different_build_numbers_are_rejected(self):
        work_items = self.create_work_items()

        work_items["REQ-001"].build_number = "1.01"
        work_items["TEST-001"].build_number = "1.02"

        errors = HierarchyRules.validate_hierarchy(work_items)

        self.assertTrue(
            any(
                "Requirement 'REQ-001' and Test Case 'TEST-001' "
                "must have the same build number."
                in error
                for error in errors
            )
        )

if __name__ == "__main__":
    unittest.main()
