"""
Evaluation & Metrics Framework
Prevents hallucinations, tracks accuracy, ensures quality
"""

import json
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# EVALUATION METRICS
# ============================================================================

@dataclass
class EvaluationMetrics:
    """Tracks AI quality metrics"""
    
    case_id: str
    timestamp: str
    
    # Condition Analysis Metrics
    condition_confidence: float  # Model's stated confidence
    condition_severity_valid: bool  # Severity is one of: severe/moderate/mild/unknown
    injuries_count: int
    injuries_realistic: bool
    
    # Response Strategy Metrics
    response_type_valid: bool  # Valid response type selected
    urgency_level_valid: bool  # Valid urgency assigned
    
    # Verification Metrics
    verification_confidence: float
    verification_matches_plan: bool
    
    # Overall Quality
    hallucination_score: float  # 0.0 = no hallucinations, 1.0 = severe hallucinations
    accuracy_score: float  # 0.0 = completely wrong, 1.0 = perfect
    
    notes: str = ""

# ============================================================================
# HALLUCINATION DETECTOR
# ============================================================================

class HallucinationDetector:
    """Detects and flags potential hallucinations in agent outputs"""
    
    # Red flags for hallucinations
    UNREALISTIC_INJURIES = {
        "alien bite", "zombie scratch", "ghost wound", "magical curse",
        "superhuman damage", "impossible fracture", "perpetual bleeding"
    }
    
    UNREALISTIC_ANIMALS = {
        "mythical", "fantasy", "extinct (except recent)", "fictional"
    }
    
    UNREALISTIC_SEVERITIES = {
        "super severe", "beyond severe", "infinitely injured"
    }
    
    UNREALISTIC_AGES = {
        "ancient", "immortal", "one million years old"
    }
    
    def __init__(self):
        self.flags = []
    
    def check_condition_output(self, condition_data: Dict) -> Tuple[float, List[str]]:
        """
        Analyze condition output for hallucinations
        Returns: (hallucination_score: 0.0-1.0, flags: list of issues)
        """
        
        flags = []
        hallucination_score = 0.0
        
        # Check severity value
        severity = condition_data.get("severity", "").lower()
        valid_severities = ["severe", "moderate", "mild", "unknown"]
        
        if severity not in valid_severities:
            flags.append(f"Invalid severity: '{severity}'")
            hallucination_score += 0.3
        
        if any(s in severity for s in self.UNREALISTIC_SEVERITIES):
            flags.append(f"Unrealistic severity description: {severity}")
            hallucination_score += 0.4
        
        # Check confidence
        confidence = condition_data.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            flags.append(f"Invalid confidence value: {confidence}")
            hallucination_score += 0.2
        
        # Check injuries
        injuries = condition_data.get("visible_injuries", [])
        if not isinstance(injuries, list):
            flags.append("Injuries not a list")
            hallucination_score += 0.15
        
        for injury in injuries:
            if any(unrealistic in injury.lower() for unrealistic in self.UNREALISTIC_INJURIES):
                flags.append(f"Unrealistic injury: '{injury}'")
                hallucination_score += 0.3
        
        if len(injuries) > 20:
            flags.append(f"Too many injuries listed: {len(injuries)}")
            hallucination_score += 0.2
        
        # Check species
        species = condition_data.get("species", "").lower()
        if len(species) > 50:
            flags.append("Species description too long")
            hallucination_score += 0.1
        
        # Check description length
        description = condition_data.get("description", "")
        if len(description) > 1000:
            flags.append("Description unreasonably long")
            hallucination_score += 0.1
        
        # Check for contradictions
        if severity == "severe" and "healthy" in description.lower():
            flags.append("Contradiction: severe injury but described as healthy")
            hallucination_score += 0.35
        
        return min(1.0, hallucination_score), flags
    
    def check_response_output(self, response_data: Dict) -> Tuple[float, List[str]]:
        """Analyze response strategy for hallucinations"""
        
        flags = []
        hallucination_score = 0.0
        
        # Validate response type
        valid_types = ["emergency_first_aid", "standard_rescue", "routine_rescue", 
                      "assessment_needed"]
        response_type = response_data.get("response_type", "")
        
        if response_type not in valid_types:
            flags.append(f"Invalid response type: '{response_type}'")
            hallucination_score += 0.3
        
        # Validate urgency
        valid_urgencies = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        urgency = response_data.get("urgency", "")
        
        if urgency and urgency not in valid_urgencies:
            flags.append(f"Invalid urgency level: '{urgency}'")
            hallucination_score += 0.2
        
        # Check first aid instructions
        first_aid = response_data.get("immediate_first_aid", [])
        if isinstance(first_aid, list):
            for instruction in first_aid:
                if len(instruction) > 500:
                    flags.append("First aid instruction too long")
                    hallucination_score += 0.1
                    break
        
        # Check for medical hallucinations (dangerous advice)
        dangerous_keywords = ["inject", "surgery without", "high voltage", "poison", "acid"]
        for instruction in first_aid:
            if any(kw in instruction.lower() for kw in dangerous_keywords):
                flags.append(f"Potentially dangerous instruction: {instruction}")
                hallucination_score += 0.5  # High penalty for safety issues
        
        return min(1.0, hallucination_score), flags
    
    def check_verification_output(self, verification_data: Dict) -> Tuple[float, List[str]]:
        """Analyze verification for hallucinations"""
        
        flags = []
        hallucination_score = 0.0
        
        # Validate status
        valid_statuses = ["RESCUED", "NOT_RESCUED", "INCONCLUSIVE"]
        status = verification_data.get("rescue_status", "")
        
        if status not in valid_statuses:
            flags.append(f"Invalid rescue status: '{status}'")
            hallucination_score += 0.4
        
        # Validate confidence
        confidence = verification_data.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            flags.append(f"Invalid verification confidence: {confidence}")
            hallucination_score += 0.2
        
        # Check observations length
        observations = verification_data.get("observations", "")
        if len(observations) > 2000:
            flags.append("Observations unreasonably long")
            hallucination_score += 0.15
        
        # Contradiction check
        if status == "RESCUED" and confidence < 0.3:
            flags.append("Contradiction: marked RESCUED with low confidence")
            hallucination_score += 0.3
        
        return min(1.0, hallucination_score), flags

# ============================================================================
# ACCURACY EVALUATOR
# ============================================================================

class AccuracyEvaluator:
    """Evaluates accuracy of rescue operations"""
    
    def __init__(self):
        self.cases = []
    
    def evaluate_severity_assessment(self, 
                                     predicted_severity: str,
                                     ground_truth_severity: str) -> float:
        """
        Evaluate severity prediction accuracy
        Severity levels: severe > moderate > mild
        """
        
        severity_order = {"severe": 3, "moderate": 2, "mild": 1, "unknown": 0}
        
        pred_score = severity_order.get(predicted_severity.lower(), 0)
        truth_score = severity_order.get(ground_truth_severity.lower(), 0)
        
        if pred_score == truth_score:
            return 1.0  # Perfect match
        elif abs(pred_score - truth_score) == 1:
            return 0.7  # Off by one level
        else:
            return 0.3  # Significantly wrong
    
    def evaluate_response_appropriateness(self,
                                         severity: str,
                                         response_type: str) -> float:
        """
        Evaluate if response type matches severity
        """
        
        # Expected mappings
        mappings = {
            "severe": ["emergency_first_aid"],
            "moderate": ["standard_rescue"],
            "mild": ["routine_rescue"],
            "unknown": ["assessment_needed"]
        }
        
        expected = mappings.get(severity.lower(), [])
        
        if response_type in expected:
            return 1.0
        else:
            return 0.2
    
    def evaluate_plan_quality(self, plan: Dict) -> float:
        """
        Evaluate rescue plan quality
        """
        
        score = 0.0
        max_score = 0.0
        
        # Check if plan has essential components
        essential_keys = ["rescue_id", "steps", "required_resources", "contact_priority"]
        
        for key in essential_keys:
            max_score += 0.25
            if key in plan and plan[key]:
                score += 0.25
        
        # Check steps are valid
        steps = plan.get("steps", [])
        max_score += 0.5
        
        if isinstance(steps, list) and len(steps) >= 2:
            score += 0.5
        elif isinstance(steps, list) and len(steps) == 1:
            score += 0.25
        
        return min(1.0, score / max_score) if max_score > 0 else 0.0
    
    def evaluate_verification_consistency(self,
                                         outcome: str,
                                         verification_confidence: float) -> float:
        """
        Evaluate if verification outcome has appropriate confidence
        """
        
        if outcome == "INCONCLUSIVE":
            # Low confidence is appropriate for inconclusive
            if verification_confidence < 0.6:
                return 0.9
            else:
                return 0.5
        else:
            # High confidence expected for definitive outcomes
            if verification_confidence >= 0.6:
                return 0.95
            else:
                return 0.4

# ============================================================================
# METRICS DATABASE
# ============================================================================

class MetricsDB:
    """Store and retrieve evaluation metrics"""
    
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize metrics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            case_id TEXT PRIMARY KEY,
            timestamp TEXT,
            condition_confidence REAL,
            condition_severity_valid INTEGER,
            injuries_count INTEGER,
            injuries_realistic INTEGER,
            response_type_valid INTEGER,
            urgency_level_valid INTEGER,
            verification_confidence REAL,
            verification_matches_plan INTEGER,
            hallucination_score REAL,
            accuracy_score REAL,
            notes TEXT
        )
        """)
        
        conn.commit()
        conn.close()
    
    def save_metrics(self, metrics: EvaluationMetrics):
        """Save evaluation metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT OR REPLACE INTO metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.case_id,
            metrics.timestamp,
            metrics.condition_confidence,
            int(metrics.condition_severity_valid),
            metrics.injuries_count,
            int(metrics.injuries_realistic),
            int(metrics.response_type_valid),
            int(metrics.urgency_level_valid),
            metrics.verification_confidence,
            int(metrics.verification_matches_plan),
            metrics.hallucination_score,
            metrics.accuracy_score,
            metrics.notes
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Metrics saved for case {metrics.case_id}")
    
    def get_average_metrics(self) -> Dict:
        """Get average metrics across all cases"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT 
            AVG(hallucination_score) as avg_hallucination,
            AVG(accuracy_score) as avg_accuracy,
            AVG(condition_confidence) as avg_confidence,
            COUNT(*) as total_cases
        FROM metrics
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[3] > 0:
            return {
                "average_hallucination_score": round(result[0], 3),
                "average_accuracy_score": round(result[1], 3),
                "average_confidence": round(result[2], 3),
                "total_cases": result[3]
            }
        
        return {"total_cases": 0}

# ============================================================================
# QUALITY ASSURANCE
# ============================================================================

class QualityAssurance:
    """Comprehensive QA for rescue operations"""
    
    def __init__(self):
        self.detector = HallucinationDetector()
        self.evaluator = AccuracyEvaluator()
        self.metrics_db = MetricsDB()
    
    def evaluate_rescue_case(self, case_data: Dict, case_id: str) -> EvaluationMetrics:
        """
        Evaluate complete rescue case
        """
        
        # Extract components
        condition = case_data.get("condition", {})
        response = case_data.get("response_strategy", {})
        plan = case_data.get("rescue_plan", {})
        verification = case_data.get("verification_details", {})
        
        # Condition analysis
        hal_score_cond, flags_cond = self.detector.check_condition_output(condition)
        severity_accuracy = self.evaluator.evaluate_severity_assessment(
            condition.get("severity", "unknown"),
            "unknown"  # In real scenario, compare with ground truth
        )
        
        # Response strategy analysis
        hal_score_resp, flags_resp = self.detector.check_response_output(response)
        response_accuracy = self.evaluator.evaluate_response_appropriateness(
            condition.get("severity", "unknown"),
            response.get("response_type", "")
        )
        
        # Verification analysis
        hal_score_verif, flags_verif = self.detector.check_verification_output(verification)
        verification_accuracy = self.evaluator.evaluate_verification_consistency(
            verification.get("rescue_status", "INCONCLUSIVE"),
            verification.get("confidence", 0.5)
        )
        
        # Plan quality
        plan_quality = self.evaluator.evaluate_plan_quality(plan)
        
        # Overall metrics
        overall_hallucination = (hal_score_cond + hal_score_resp + hal_score_verif) / 3
        overall_accuracy = (severity_accuracy + response_accuracy + verification_accuracy + plan_quality) / 4
        
        all_flags = flags_cond + flags_resp + flags_verif
        
        metrics = EvaluationMetrics(
            case_id=case_id,
            timestamp=datetime.now().isoformat(),
            condition_confidence=condition.get("confidence", 0.5),
            condition_severity_valid=condition.get("severity", "").lower() in ["severe", "moderate", "mild", "unknown"],
            injuries_count=len(condition.get("visible_injuries", [])),
            injuries_realistic=len(all_flags) == 0,
            response_type_valid=response.get("response_type", "") in ["emergency_first_aid", "standard_rescue", "routine_rescue", "assessment_needed"],
            urgency_level_valid=response.get("urgency", "") in ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            verification_confidence=verification.get("confidence", 0.5),
            verification_matches_plan=response.get("response_type") in ["emergency_first_aid", "standard_rescue"],
            hallucination_score=overall_hallucination,
            accuracy_score=overall_accuracy,
            notes="; ".join(all_flags[:5])  # Top 5 issues
        )
        
        self.metrics_db.save_metrics(metrics)
        
        return metrics
    
    def get_system_health(self) -> Dict:
        """Get overall system health metrics"""
        
        avg_metrics = self.metrics_db.get_average_metrics()
        
        health = {
            "system_status": "HEALTHY" if avg_metrics.get("average_hallucination_score", 1.0) < 0.3 else "NEEDS_ATTENTION",
            "metrics": avg_metrics,
            "recommendations": self._get_recommendations(avg_metrics)
        }
        
        return health
    
    def _get_recommendations(self, metrics: Dict) -> List[str]:
        """Generate recommendations based on metrics"""
        
        recommendations = []
        
        hallucination_score = metrics.get("average_hallucination_score", 0.0)
        accuracy_score = metrics.get("average_accuracy_score", 0.0)
        
        if hallucination_score > 0.3:
            recommendations.append("⚠️ High hallucination rate - review agent prompts and add stricter validation")
        
        if accuracy_score < 0.7:
            recommendations.append("⚠️ Low accuracy - consider adding ground truth labels for retraining")
        
        if metrics.get("total_cases", 0) < 10:
            recommendations.append("📊 Need more test cases for reliable metrics")
        
        if not recommendations:
            recommendations.append("✅ System performing well - continue monitoring")
        
        return recommendations
