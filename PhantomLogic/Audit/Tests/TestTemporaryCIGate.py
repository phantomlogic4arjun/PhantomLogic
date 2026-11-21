
import unittest


class TestTemporaryCIGate(unittest.TestCase):

    def test_ci_merge_gate_rejects_failure(self):
        self.fail("Temporary test: verifying GitHub CI merge protection.")


if __name__ == "__main__":
    unittest.main()
