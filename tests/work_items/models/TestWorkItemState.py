import unittest

from phantom_logic.work_items.models.WorkItemState import (
    WorkItemState,
    CodeReviewState,
    ReviewResult,
)


class TestWorkItemState(unittest.TestCase):

    def test_standard_work_item_states_are_defined(self):
        expected_states = {
            "Proposed",
            "In Work",
            "In Test",
            "Resolved",
            "Blocked",
            "Removed",
        }

        actual_states = {state.value for state in WorkItemState}

        self.assertEqual(actual_states, expected_states)

    def test_code_review_states_are_separate(self):
        expected_states = {
            "Proposed",
            "In Work",
            "Review",
            "Resolved",
        }

        actual_states = {state.value for state in CodeReviewState}

        self.assertEqual(actual_states, expected_states)

        self.assertNotIn("In Test", actual_states)

    def test_review_results_are_separate_from_states(self):
        expected_results = {
            "Pending",
            "Changes Requested",
            "Approved",
        }

        actual_results = {result.value for result in ReviewResult}

        self.assertEqual(actual_results, expected_results)

    def test_states_are_string_enums(self):
        self.assertEqual(WorkItemState.IN_WORK, "In Work")
        self.assertEqual(CodeReviewState.REVIEW, "Review")
        self.assertEqual(ReviewResult.APPROVED, "Approved")


if __name__ == "__main__":
    unittest.main()
