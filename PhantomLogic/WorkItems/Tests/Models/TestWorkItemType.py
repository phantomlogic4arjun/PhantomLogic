import unittest

from PhantomLogic.WorkItems.Models.WorkItemType import WorkItemType


class TestWorkItemType(unittest.TestCase):

    def test_all_work_item_types_are_defined(self):
        expected_types = {
            "Epic",
            "Feature",
            "Use Case",
            "Requirement",
            "Development Task",
            "Supporting Task",
            "Test Case",
            "Bug",
            "Change Request",
            "Code Review Task",
        }

        actual_types = {item.value for item in WorkItemType}

        self.assertEqual(actual_types, expected_types)

    def test_work_item_type_is_a_string_enum(self):
        self.assertEqual(WorkItemType.FEATURE, "Feature")
        self.assertIsInstance(WorkItemType.FEATURE, str)


if __name__ == "__main__":
    unittest.main()
