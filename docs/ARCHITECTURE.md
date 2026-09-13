# 🏗️ System Architecture

## Overview

The AI Abandoned Pet Rescue System is built on a **multi-agent orchestration pattern** where 4 specialized agents work together to rescue pets.

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│                   (Streamlit Web App)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              IMAGE UPLOAD & VALIDATION                       │
│         (Streamlit File Handler + PIL Image Processor)       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│           RESCUE ORCHESTRATOR (Main Coordinator)             │
│           (PetRescueOrchestrator in agents.py)              │
└──────┬──────────┬──────────┬──────────────────────┬──────────┘
       │          │          │                      │
       ↓          ↓          ↓                      ↓
   ┌──────┐  ┌────────┐  ┌──────────┐      ┌─────────────┐
   │  👁️  │  │   🔎   │  │   🚑     │      │     ✅      │
   │Agent1│  │ Agent2 │  │ Agent3   │      │   Agent4    │
   └──────┘  └────────┘  └──────────┘      └─────────────┘
       │          │          │                      │
       ↓          ↓          ↓                      ↓
  ┌─────────────────────────────────────────────────────────┐
  │         NVIDIA NIM API CLIENT (Unified Interface)        │
  │  (NIMClient - Handles authentication & API calls)        │
  └──────────────┬─────────────────────────────┬────────────┘
                 │                             │
                 ↓                             ↓
        ┌─────────────────┐         ┌──────────────────┐
        │  Vision Models  │         │  Reasoning Models│
        │ (Nemotron VL)   │         │(Nemotron Omni)   │
        └─────────────────┘         └──────────────────┘
                                            │
                                            ↓
                                   ┌──────────────────┐
                                   │  NVIDIA NIM APIs │
                                   │ (Cloud Inference)│
                                   └──────────────────┘
       │
       ↓
┌─────────────────────────────────────────────────────────┐
│         QUALITY ASSURANCE LAYER (Evaluation)             │
│  (Hallucination Detector + Accuracy Evaluator + QA)     │
└──────────┬──────────────────────────────────┬───────────┘
           │                                  │
           ↓                                  ↓
    ┌─────────────────┐             ┌────────────────┐
    │ Hallucination   │             │ Metrics Database│
    │ Detection       │             │ (SQLite)        │
    └─────────────────┘             └────────────────┘
           │
           ↓
┌─────────────────────────────────────────────────────────┐
│              RESCUE OUTCOME & STORAGE                    │
│  (Database + Alerts + User Feedback)                     │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Agent 1: Condition Agent 👁️

**Purpose**: Analyze pet photos/videos to assess condition

**Input**: Image (base64)

**Processing**:
```python
Vision Model: Nemotron Nano 12B Vision
Prompt: Analyze pet condition, detect injuries, classify severity
Output: JSON with severity, species, injuries, confidence
```

**Output**:
```json
{
  "severity": "severe|moderate|mild|unknown",
  "species": "dog|cat|bird|other",
  "description": "Brief condition description",
  "visible_injuries": ["injury1", "injury2"],
  "estimated_age": "puppy|adult|senior|unknown",
  "confidence": 0.0-1.0,
  "urgent_actions": ["action1", "action2"]
}
```

**Validation**:
- Severity must be one of: severe, moderate, mild, unknown
- Confidence between 0.0 and 1.0
- Max 5 injuries, 50 chars each
- No unrealistic injuries (alien, zombie, etc.)

---

### 2. Agent 2: Response Agent 🔎

**Purpose**: Decide what help is needed based on severity

**Input**: PetCondition (from Agent 1)

**Decision Logic**:
```
IF severe:
    → Emergency first aid + emergency vet alert
ELSE IF moderate:
    → Standard rescue + NGO + Vet search
ELSE IF mild:
    → Routine rescue + NGO/Shelter search
ELSE:
    → Request assessment from experts
```

**Output**:
```json
{
  "response_type": "emergency_first_aid|standard_rescue|routine_rescue|assessment_needed",
  "urgency": "CRITICAL|HIGH|MEDIUM|LOW",
  "immediate_first_aid": ["instruction1", "instruction2"],
  "resources_needed": ["emergency_vet", "transport"],
  "estimated_response_time": "30 mins"
}
```

**Validation**:
- Response type must be recognized
- Urgency must be CRITICAL/HIGH/MEDIUM/LOW
- First aid checked for medical safety
- No dangerous instructions

---

### 3. Agent 3: Coordination Agent 🚑

**Purpose**: Create actionable rescue plans

**Input**: 
- PetCondition
- Response strategy
- Location

**Processing**:
```python
Reasoning Model: Nemotron 3 Nano Omni 30B
Generates step-by-step rescue plan
Selects best resources
Creates contact priority list
```

**Output**:
```json
{
  "rescue_id": "RESCUE_2024_XXXXX",
  "steps": [
    {"step": 1, "action": "...", "estimated_time": "mins"},
    {"step": 2, "action": "...", "estimated_time": "mins"}
  ],
  "required_resources": ["item1", "item2"],
  "contact_priority": ["emergency_vet", "ngo"],
  "total_estimated_time": "30 mins"
}
```

**Validation**:
- Min 2 steps, max 10 steps
- All steps have realistic time estimates
- Resources are known types
- Plan is complete and actionable

---

### 4. Agent 4: Verification Agent ✅

**Purpose**: Verify rescue success

**Input**: 
- Before image (abandoned pet)
- After image (rescued/in care)
- Rescue ID

**Processing**:
```python
Vision Model: Nemotron Nano 12B Vision
Compares before/after images
Determines rescue success
```

**Output**:
```json
{
  "rescue_status": "RESCUED|NOT_RESCUED|INCONCLUSIVE",
  "confidence": 0.0-1.0,
  "observations": "detailed comparison",
  "next_action": "close|re_plan|monitor"
}
```

**Validation**:
- Status must be valid
- Confidence 0.0-1.0
- Confidence matches outcome (high for definitive, low for uncertain)
- No contradictions

---

## Quality Assurance Pipeline

### Hallucination Detection

Every agent output goes through hallucination detection:

```python
class HallucinationDetector:
    - check_condition_output()      # Agent 1
    - check_response_output()       # Agent 2
    - check_verification_output()   # Agent 4
```

**Red Flags Detected**:
- ❌ Unrealistic injuries (alien, zombie, ghost, magical)
- ❌ Impossible ages (1 million years old)
- ❌ Invalid severity (super severe, beyond severe)
- ❌ Contradictions (severe but described as healthy)
- ❌ Dangerous medical advice
- ❌ Malformed JSON

**Scoring**:
- Hallucination Score: 0.0 (good) to 1.0 (bad)
- Flags collected for each issue
- Stored in database for analysis

---

### Accuracy Evaluation

Each case is evaluated on multiple dimensions:

```python
class AccuracyEvaluator:
    - evaluate_severity_assessment()
    - evaluate_response_appropriateness()
    - evaluate_plan_quality()
    - evaluate_verification_consistency()
```

**Severity Assessment**:
- Perfect match: 1.0
- Off by one level: 0.7
- Significantly wrong: 0.3

**Response Appropriateness**:
- Matches severity: 1.0
- Doesn't match: 0.2

**Plan Quality**:
- Has all components: 1.0
- Missing components: 0.0-0.5

**Verification Consistency**:
- High confidence for definitive: 0.95
- Low confidence for inconclusive: 0.9
- Mismatched: 0.4-0.5

---

## Data Flow

### Case Processing Flow

```
1. User uploads pet photo
   ↓
2. Image validation (size, format)
   ↓
3. Convert to base64
   ↓
4. Orchestrator.process_rescue_case()
   ├─ Condition Agent analyzes
   ├─ Response Agent decides
   ├─ Coordination Agent plans
   └─ QA evaluates all outputs
   ↓
5. Store in session state
   ├─ Rescue data
   ├─ Metrics
   └─ Evaluation results
   ↓
6. Display to user
   ├─ Condition summary
   ├─ First aid (if needed)
   ├─ Rescue plan
   ├─ Quality metrics
   └─ Action buttons
```

### Verification Flow

```
1. User uploads post-rescue photo
   ↓
2. Verification Agent compares
   ├─ Before image (stored)
   ├─ After image (new)
   └─ Generates assessment
   ↓
3. QA evaluates outcome
   ├─ Status validation
   ├─ Confidence calibration
   └─ Consistency checks
   ↓
4. Store in database
   ├─ Case ID
   ├─ Outcome (RESCUED/NOT_RESCUED/INCONCLUSIVE)
   ├─ Confidence
   └─ Metrics
   ↓
5. Update user
   ├─ Success confirmation
   ├─ Next actions
   └─ Thank you message
```

---

## API Integration

### NVIDIA NIM Client

Unified interface to NVIDIA NIM APIs:

```python
class NIMClient:
    def __init__(api_key, base_url):
        # Initialize with authentication
    
    def call_model(model, messages, temperature, max_tokens):
        # Text/reasoning model calls
    
    def call_vision_model(model, image_base64, prompt):
        # Vision model calls
```

**Error Handling**:
- Timeout handling (30 seconds)
- Network error recovery
- Rate limit handling
- Graceful degradation

**Rate Limiting**:
- Concurrent requests: Limited
- Per-minute: Based on NIM tier
- Queuing: Automatic for overload

---

## Database Schema

### Metrics Table

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

**Queries**:
- Average hallucination score
- Average accuracy score
- Total cases processed
- Cases by severity
- Rescue success rate

---

## Security Considerations

### Input Validation
- Image size limits (max 50MB)
- Format validation (JPG, PNG)
- Base64 validation

### Output Validation
- JSON schema validation
- Data type checking
- Range validation (0.0-1.0)
- String length limits

### API Key Management
- Stored in `.env` (never committed)
- Passed via environment variables
- Not logged or exposed

### Data Privacy
- Images not permanently stored
- Rescue data anonymized
- Database can be encrypted
- User can request deletion

---

## Performance Characteristics

### Latency
- Condition Analysis: ~2-3 seconds
- Response Decision: ~1-2 seconds
- Plan Generation: ~2-3 seconds
- Verification: ~2-3 seconds
- **Total E2E**: ~8-10 seconds

### Throughput
- Single instance: ~5-10 cases/min
- Scales horizontally with load balancing

### Cost
- All NVIDIA NIM APIs: **FREE TIER**
- Streamlit Cloud: Free tier available
- Database: SQLite (local)
- **Total cost**: $0/month ✅

---

## Extensibility

### Adding New Agents

```python
class NewAgent:
    def __init__(self, nim_client):
        self.nim = nim_client
    
    def process(self, input_data):
        # Call NIM API
        # Validate output
        # Return result
```

Then add to orchestrator:

```python
self.new_agent = NewAgent(self.nim)
```

### Adding New Metrics

```python
class AccuracyEvaluator:
    def evaluate_new_metric(self, data):
        # Implement evaluation logic
        # Return score (0.0-1.0)
```

---

## Monitoring & Observability

### Logging
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Processing rescue case...")
logger.error("API error occurred")
```

### Metrics Collection
```
- Hallucination scores per case
- Accuracy scores per case
- API latency
- Error rates
- Success rates
```

### Dashboards
- Streamlit dashboard in app
- Real-time system health
- Historical metrics
- Recommendations

---

## Future Enhancements

1. **Multi-modal Input**: Videos, audio
2. **Geo-location Integration**: Map-based rescues
3. **NGO Database**: Local rescue centers
4. **SMS/WhatsApp**: Mobile notifications
5. **Payment Integration**: Rescue fund transfers
6. **ML Fine-tuning**: On real rescue data
7. **Mobile App**: iOS/Android native
8. **Blockchain**: Immutable rescue records
