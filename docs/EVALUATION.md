# 📊 Evaluation & Quality Metrics Guide

## Overview

The Pet Rescue System includes comprehensive evaluation and quality assurance to prevent hallucinations and ensure accuracy.

```
Every Case
    ↓
Condition Analysis (Agent 1)
    ├─ Parse JSON
    ├─ Validate severity
    ├─ Check confidence
    ├─ Inspect injuries
    └─ Hallucination score → Score 1
    ↓
Response Strategy (Agent 2)
    ├─ Validate response type
    ├─ Check urgency level
    ├─ Review first aid instructions
    └─ Safety check → Score 2
    ↓
Coordination Plan (Agent 3)
    ├─ Check plan completeness
    ├─ Validate steps
    ├─ Review resources
    └─ Quality score → Score 3
    ↓
Verification (Agent 4)
    ├─ Validate status
    ├─ Check confidence calibration
    └─ Consistency check → Score 4
    ↓
Average Scores
    ├─ Hallucination Score (0.0-1.0)
    ├─ Accuracy Score (0.0-1.0)
    └─ Store in Database
```

---

## Hallucination Detection

### What We Detect

A hallucination is when the AI generates:
- Unrealistic content (alien pets, impossible injuries)
- Contradictory information (severe but described as healthy)
- Dangerous advice (medical instructions that could harm)
- Malformed outputs (invalid JSON, missing fields)

### Hallucination Score

**Scale**: 0.0 to 1.0
- **0.0-0.2**: Excellent (no hallucinations)
- **0.2-0.5**: Good (minor issues)
- **0.5-0.8**: Warning (notable concerns)
- **0.8-1.0**: Critical (significant hallucinations)

### Detection Methods

#### 1. Input Validation

**Severity Constraints**
```python
valid = {"severe", "moderate", "mild", "unknown"}
if data["severity"] not in valid:
    hallucination_score += 0.3
```

**Confidence Bounds**
```python
if not (0.0 <= data["confidence"] <= 1.0):
    hallucination_score += 0.2
```

**Injury Realism**
```python
unrealistic_injuries = {
    "alien bite", "zombie scratch", "ghost wound",
    "magical curse", "superhuman damage"
}
for injury in data.get("injuries", []):
    if any(u in injury.lower() for u in unrealistic_injuries):
        hallucination_score += 0.3
```

#### 2. Output Validation

**Response Type Validation**
```python
valid_types = [
    "emergency_first_aid",
    "standard_rescue",
    "routine_rescue",
    "assessment_needed"
]
if response["type"] not in valid_types:
    hallucination_score += 0.3
```

**Contradiction Detection**
```python
if severity == "SEVERE" and "healthy" in description.lower():
    hallucination_score += 0.35  # Major contradiction
```

**Medical Safety Checks**
```python
dangerous_keywords = [
    "inject without", "surgery without",
    "high voltage", "poison", "acid"
]
for instruction in first_aid_list:
    if any(d in instruction.lower() for d in dangerous_keywords):
        hallucination_score += 0.5  # Critical safety issue
```

#### 3. Red Flags

| Flag | Issue | Penalty |
|------|-------|---------|
| Invalid severity | Not one of 4 values | 0.3 |
| Invalid confidence | Not 0.0-1.0 | 0.2 |
| Unrealistic injury | Alien, zombie, ghost | 0.3-0.4 |
| Too many injuries | More than 20 | 0.2 |
| Dangerous advice | Medical safety risk | 0.5 |
| Contradiction | Conflicting info | 0.3-0.35 |
| Missing fields | Incomplete response | 0.2-0.3 |
| Invalid JSON | Parse error | 0.4 |

### Example Detections

**Example 1: Unrealistic Injury**
```json
{
  "severity": "severe",
  "injuries": ["alien bite", "zombie scratch"],
  "confidence": 0.95
}
```
**Detected**: Unrealistic injuries → hallucination_score = 0.6
**Result**: ⚠️ Warning - Use with caution

---

**Example 2: Contradiction**
```json
{
  "severity": "severe",
  "description": "The dog appears healthy and happy",
  "confidence": 0.9
}
```
**Detected**: Contradiction between severity and description
**Result**: ⚠️ Warning - Confidence should be lower

---

**Example 3: Dangerous Advice**
```json
{
  "immediate_first_aid": [
    "Keep pet warm",
    "Inject high voltage to restart heart"
  ]
}
```
**Detected**: Dangerous medical instruction
**Result**: 🚫 REJECTED - Safety issue

---

## Accuracy Evaluation

### Severity Assessment Accuracy

**Scoring Logic**:
```
Severity levels: severe (3) > moderate (2) > mild (1) > unknown (0)

Perfect Match:           1.0  ✅
Off by one level:        0.7  ⚠️
Significantly wrong:     0.3  ❌
```

**Example**:
- Predicted: "moderate" (2)
- Ground truth: "moderate" (2)
- Score: 1.0 (perfect)

---

### Response Appropriateness

**Expected Mappings**:
```python
{
  "severe": ["emergency_first_aid"],
  "moderate": ["standard_rescue"],
  "mild": ["routine_rescue"],
  "unknown": ["assessment_needed"]
}
```

**Scoring**:
```
Match expected:        1.0  ✅
Doesn't match:         0.2  ❌
```

**Example**:
- Severity: "severe"
- Response: "emergency_first_aid"
- Match: Yes → score = 1.0 ✅

---

### Plan Quality Score

**Components Evaluated**:

| Component | Weight | Criteria |
|-----------|--------|----------|
| Rescue ID | 0.25 | Present and valid |
| Steps | 0.25 | 2-10 steps with realistic timing |
| Resources | 0.25 | Known resource types |
| Contacts | 0.25 | Valid priority list |

**Calculation**:
```python
score = 0.0
if "rescue_id" in plan and plan["rescue_id"]:
    score += 0.25
if len(plan.get("steps", [])) >= 2:
    score += 0.25
if plan.get("required_resources"):
    score += 0.25
if plan.get("contact_priority"):
    score += 0.25

final_score = score / 1.0  # 0.0 to 1.0
```

---

### Verification Consistency

**Principle**: Confidence should match outcome certainty

**Rules**:
```python
if outcome == "RESCUED":
    # Should have high confidence
    if confidence >= 0.6:
        score = 0.95  # ✅ Appropriate
    else:
        score = 0.4   # ⚠️ Questionable

elif outcome == "NOT_RESCUED":
    # Should have high confidence
    if confidence >= 0.6:
        score = 0.95  # ✅ Appropriate
    else:
        score = 0.4   # ⚠️ Questionable

elif outcome == "INCONCLUSIVE":
    # Should have low confidence
    if confidence < 0.6:
        score = 0.9   # ✅ Appropriate
    else:
        score = 0.5   # ⚠️ Should be less confident
```

---

## Metrics Database

### Schema

```sql
CREATE TABLE metrics (
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
);
```

### Querying Metrics

**Get Average Metrics**:
```python
from evaluation import MetricsDB

db = MetricsDB("metrics.db")
stats = db.get_average_metrics()

print(f"Average Hallucination: {stats['average_hallucination_score']}")
print(f"Average Accuracy: {stats['average_accuracy_score']}")
print(f"Total Cases: {stats['total_cases']}")
```

**Output**:
```
{
    "average_hallucination_score": 0.18,
    "average_accuracy_score": 0.87,
    "average_confidence": 0.82,
    "total_cases": 15
}
```

### Trend Analysis

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("metrics.db")
df = pd.read_sql_query("SELECT * FROM metrics", conn)

# Hallucination trend over time
hallucination_trend = df.groupby("date")["hallucination_score"].mean()
print(hallucination_trend)  # Should be decreasing ↓

# Accuracy improvement
accuracy_trend = df.groupby("date")["accuracy_score"].mean()
print(accuracy_trend)  # Should be increasing ↑
```

---

## System Health Dashboard

### Health Indicators

```
🟢 HEALTHY: hallucination_score < 0.3 AND accuracy_score > 0.8
🟡 WARNING: hallucination_score > 0.3 OR accuracy_score < 0.7
🔴 CRITICAL: hallucination_score > 0.6 OR accuracy_score < 0.5
```

### Automatic Recommendations

**When Hallucination Score > 0.3**:
```
⚠️ High hallucination rate detected
   → Review agent prompts
   → Add stricter validation rules
   → Check model temperature settings
   → Increase confidence threshold
```

**When Accuracy Score < 0.7**:
```
⚠️ Low accuracy detected
   → Collect more labeled test cases
   → Fine-tune model on domain data
   → Review ground truth labels
   → Check for data quality issues
```

**When Cases < 10**:
```
📊 Insufficient test data
   → Process more cases
   → Build larger evaluation set
   → Run baseline comparisons
   → Establish statistical significance
```

---

## Quality Gates

### Before Deployment

✅ **Must Pass**:
1. Hallucination score < 0.25 on test cases
2. Accuracy score > 0.85 on test cases
3. No dangerous/unsafe outputs in test suite
4. JSON parsing success rate = 100%
5. Response time < 10 seconds per case

### Before Production

✅ **Should Pass**:
1. Hallucination score < 0.15 on 100+ cases
2. Accuracy score > 0.90 on 100+ cases
3. User satisfaction survey > 4.0/5.0
4. Zero safety incidents
5. P99 latency < 15 seconds

---

## Testing

### Unit Tests

```python
from evaluation import HallucinationDetector, AccuracyEvaluator

def test_hallucination_detection():
    detector = HallucinationDetector()
    
    # Test unrealistic injury
    data = {"severity": "severe", "injuries": ["alien bite"]}
    score, flags = detector.check_condition_output(data)
    
    assert score > 0.3, "Should detect unrealistic injury"
    assert any("unrealistic" in f.lower() for f in flags)
    print("✅ Hallucination detection works")

def test_accuracy_scoring():
    evaluator = AccuracyEvaluator()
    
    # Perfect match
    score = evaluator.evaluate_severity_assessment("severe", "severe")
    assert score == 1.0, "Perfect match should score 1.0"
    
    # Off by one
    score = evaluator.evaluate_severity_assessment("moderate", "severe")
    assert score == 0.7, "Off by one should score 0.7"
    
    print("✅ Accuracy scoring works")
```

---

## Reporting

### Generate System Report

```python
from evaluation import QualityAssurance

qa = QualityAssurance()
health = qa.get_system_health()

print(f"""
📊 SYSTEM HEALTH REPORT
========================
Status: {health['system_status']}
Cases Processed: {health['metrics']['total_cases']}

Performance:
  Hallucination Score: {health['metrics']['average_hallucination_score']}
  Accuracy Score: {health['metrics']['average_accuracy_score']}
  Confidence: {health['metrics']['average_confidence']}

Recommendations:
{chr(10).join(health['recommendations'])}
""")
```

---

## Continuous Improvement

### Feedback Loop

```
1. Process Case
   ↓
2. Evaluate Quality
   ↓
3. Store Metrics
   ↓
4. Calculate Stats
   ↓
5. Generate Insights
   ↓
6. Update Prompts/Rules
   ↓
7. Repeat
```

### Monthly Review

- [ ] Check hallucination trends
- [ ] Review accuracy improvements
- [ ] Identify failure patterns
- [ ] Update model prompts
- [ ] Refine validation rules
- [ ] Communicate insights to team

---

## Benchmarking

### Baseline Metrics

```
Model Version 1.0 (Baseline):
  Hallucination Score: 0.22
  Accuracy Score: 0.84
  Confidence Calibration: 0.09 error
  Processing Time: 8.5 seconds
```

### Target Metrics

```
Model Version 2.0 (Target):
  Hallucination Score: < 0.15  (↓ 33%)
  Accuracy Score: > 0.90       (↑ 7%)
  Confidence Calibration: < 0.05 error (↓ 44%)
  Processing Time: < 10 seconds (↔ stable)
```

---

## Best Practices

1. **Monitor Continuously**: Check metrics daily
2. **Act on Insights**: Update rules when issues arise
3. **Test Thoroughly**: Use 80/20 train/test split
4. **Document Changes**: Log all prompt/rule updates
5. **Collect Feedback**: Get user input on outputs
6. **Iterate Quickly**: Continuous improvement mindset

---

Last updated: 2024
