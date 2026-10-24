import unittest

from backend.policy import PolicyEngine, is_allowed, policy_reason


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.p = PolicyEngine()

    def test_default_policy_matches_spec(self):
        self.assertTrue(self.p.evaluate("red", "llm").allowed)
        self.assertTrue(self.p.evaluate("blue", "llm").allowed)
        self.assertFalse(self.p.evaluate("red", "blue").allowed)
        self.assertFalse(self.p.evaluate("blue", "red").allowed)

    def test_explicit_rules_are_labelled(self):
        self.assertEqual(self.p.evaluate("red", "blue").rule, "explicit-deny")
        self.assertEqual(self.p.evaluate("red", "llm").rule, "explicit-allow")

    def test_everything_else_is_default_deny(self):
        for s, t in [("llm", "red"), ("llm", "blue"), ("red", "red"), ("blue", "blue"), ("attacker", "llm"), ("red", "internet")]:
            d = self.p.evaluate(s, t)
            self.assertFalse(d.allowed, (s, t))
            self.assertEqual(d.rule, "default-deny")

    def test_normalisation(self):
        self.assertTrue(self.p.evaluate("  RED ", "LLM").allowed)

    def test_matrix_covers_all_pairs(self):
        m = self.p.matrix()
        self.assertEqual(len(m["rules"]), 9)
        self.assertEqual({r["action"] for r in m["rules"] if r["source"] == "red" and r["target"] == "blue"}, {"DENY"})

    def test_legacy_helpers(self):
        self.assertTrue(is_allowed("red", "llm"))
        self.assertIn("Red Team", policy_reason("red", "blue"))


if __name__ == "__main__":
    unittest.main()
