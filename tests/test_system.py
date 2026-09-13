"""
Test suite for Pet Rescue System.
Run: python -m pytest tests/ -v
These tests require NO API key — they test parsing, validation and scoring only.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agents import extract_json, SeverityLevel
from evaluation import HallucinationDetector, AccuracyEvaluator


class TestJSONExtraction:
    def test_plain_json(self):
        assert extract_json('{"severity": "mild"}')["severity"] == "mild"

    def test_markdown_fenced(self):
        raw = '```json\n{"severity": "severe", "confidence": 0.9}\n```'
        assert extract_json(raw)["severity"] == "severe"

    def test_json_with_surrounding_prose(self):
        raw = 'Here is my analysis: {"severity": "moderate"} Let me know if you need more.'
        assert extract_json(raw)["severity"] == "moderate"

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            extract_json("")

    def test_no_json_raises(self):
        with pytest.raises(ValueError):
            extract_json("I cannot analyze this image.")


class TestHallucinationDetection:
    def setup_method(self):
        self.detector = HallucinationDetector()

    def test_clean_output_scores_zero(self):
        data = {
            "severity": "moderate",
            "visible_injuries": ["limping", "small cut"],
            "confidence": 0.8,
            "description": "Dog with injured rear leg",
        }
        score, flags = self.detector.check_condition_output(data)
        assert score == 0.0
        assert flags == []

    def test_unrealistic_injury_flagged(self):
        data = {"severity": "severe", "visible_injuries": ["alien bite"], "confidence": 0.9}
        score, flags = self.detector.check_condition_output(data)
        assert score > 0.2
        assert any("nrealistic" in f for f in flags)

    def test_contradiction_flagged(self):
        data = {
            "severity": "severe",
            "visible_injuries": [],
            "confidence": 0.9,
            "description": "The dog looks healthy and playful",
        }
        score, flags = self.detector.check_condition_output(data)
        assert score > 0.3
        assert any("ontradiction" in f for f in flags)

    def test_invalid_severity_flagged(self):
        data = {"severity": "catastrophically doomed", "confidence": 0.5}
        score, flags = self.detector.check_condition_output(data)
        assert score > 0.0

    def test_out_of_range_confidence_flagged(self):
        data = {"severity": "mild", "confidence": 7.5}
        score, flags = self.detector.check_condition_output(data)
        assert score > 0.0

    def test_dangerous_first_aid_heavily_penalised(self):
        data = {
            "response_type": "emergency_first_aid",
            "urgency": "CRITICAL",
            "immediate_first_aid": ["Apply high voltage to the chest"],
        }
        score, flags = self.detector.check_response_output(data)
        assert score >= 0.5
        assert any("angerous" in f for f in flags)

    def test_safe_first_aid_passes(self):
        data = {
            "response_type": "emergency_first_aid",
            "urgency": "CRITICAL",
            "immediate_first_aid": ["Keep the animal warm", "Apply gentle pressure to bleeding"],
        }
        score, flags = self.detector.check_response_output(data)
        assert score == 0.0


class TestAccuracyEvaluation:
    def setup_method(self):
        self.evaluator = AccuracyEvaluator()

    def test_exact_severity_match(self):
        assert self.evaluator.evaluate_severity_assessment("severe", "severe") == 1.0

    def test_off_by_one_severity(self):
        assert self.evaluator.evaluate_severity_assessment("moderate", "severe") == 0.7

    def test_badly_wrong_severity(self):
        assert self.evaluator.evaluate_severity_assessment("mild", "severe") == 0.3

    def test_response_matches_severity(self):
        assert self.evaluator.evaluate_response_appropriateness("severe", "emergency_first_aid") == 1.0

    def test_response_mismatched(self):
        assert self.evaluator.evaluate_response_appropriateness("severe", "routine_rescue") < 0.5

    def test_complete_plan_scores_high(self):
        plan = {
            "rescue_id": "R1",
            "steps": [{"step": 1, "action": "a"}, {"step": 2, "action": "b"}],
            "required_resources": ["transport"],
            "contact_priority": ["vet"],
        }
        assert self.evaluator.evaluate_plan_quality(plan) > 0.8

    def test_empty_plan_scores_low(self):
        assert self.evaluator.evaluate_plan_quality({}) < 0.3

    def test_confident_rescued_is_consistent(self):
        assert self.evaluator.evaluate_verification_consistency("RESCUED", 0.9) > 0.9

    def test_unconfident_rescued_is_inconsistent(self):
        assert self.evaluator.evaluate_verification_consistency("RESCUED", 0.2) < 0.5


class TestSeverityEnum:
    def test_all_levels_exist(self):
        assert {s.value for s in SeverityLevel} == {"severe", "moderate", "mild", "unknown"}
