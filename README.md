# 🐾 AI Abandoned Pet Rescue System

> **See → Assess → Find Help → Rescue → Verify 🔄**

An intelligent multi-agent AI system for coordinating abandoned pet rescue operations using NVIDIA's free NIM APIs (Nemotron models).

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![NVIDIA NIM](https://img.shields.io/badge/NVIDIA%20NIM-Free-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Overview

This system uses **4 intelligent agents** working together to rescue abandoned pets:

1. **👁️ Condition Agent** - Analyzes pet photos/videos to assess condition
2. **🔎 Response Agent** - Decides what help is needed (first aid, NGO, vet)
3. **🚑 Coordination Agent** - Creates rescue plans and coordinates resources
4. **✅ Verification Agent** - Verifies rescue success and tracks outcomes

All powered by **free NVIDIA NIM APIs** - no paid services required!

## ✨ Features

### 🤖 AI Capabilities
- **Vision Analysis**: Uses Nemotron Vision models to analyze pet condition
- **Severity Classification**: Automatic severity detection (Severe/Moderate/Mild)
- **First Aid Guidance**: Generates instant first aid instructions for critical cases
- **Plan Generation**: Creates detailed rescue execution plans
- **Outcome Verification**: Tracks rescue success with post-rescue analysis

### 🛡️ Quality & Safety
- **Hallucination Detection**: Multi-layer protection against AI hallucinations
- **Input Validation**: Ensures all data is realistic and appropriate
- **Output Validation**: Checks all AI outputs for quality and consistency
- **Accuracy Metrics**: Tracks confidence scores and model performance
- **Safety Constraints**: Prevents dangerous medical advice

### 📊 Evaluation Framework
- **Hallucination Score**: Detects unrealistic outputs (0.0-1.0)
- **Accuracy Score**: Measures prediction correctness
- **Confidence Calibration**: Ensures confidence matches actual accuracy
- **Metrics Database**: Stores and analyzes all cases

### 🎨 User Interface
- **Pet-Friendly Design**: Warm colors and friendly interface
- **Real-time Processing**: Instant case analysis
- **Step-by-step Guidance**: Clear action items for rescuers
- **Verification Tracking**: Monitor rescue progress

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- NVIDIA NIM API Key (free, get at https://build.nvidia.com/explore/discover)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/pet-rescue-system.git
cd pet-rescue-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment**
```bash
cp .env.example .env
# Edit .env and add your NVIDIA_NIM_API_KEY
```

4. **Get NVIDIA NIM API Key**
   - Visit: https://build.nvidia.com/explore/discover
   - Sign up (free)
   - Create API key
   - Add to `.env` file

5. **Run the app**
```bash
streamlit run app.py
```

6. **Open in browser**
```
http://localhost:8501
```

## 📖 Usage

### Report an Abandoned Pet

1. Go to **"🚨 Report Abandoned Pet"** section
2. Enter pet's location
3. Upload a clear photo of the pet
4. Click **"🔍 Analyze Pet Condition"**
5. System will:
   - Analyze pet condition
   - Assess severity
   - Generate first aid if needed
   - Create rescue plan
   - Dispatch resources

### Monitor Rescue Progress

1. Go to **"📊 Dashboard"**
2. View system health and metrics
3. Track accuracy and hallucination scores
4. Read recommendations

### Verify Rescue Success

1. Upload post-rescue photo
2. System compares before/after
3. Confirms rescue completion
4. Logs outcome in database

## 📁 Project Structure

```
pet-rescue-system/
├── app.py                      # Main Streamlit app
├── agents.py                   # Multi-agent orchestration
├── evaluation.py               # Quality assurance & metrics
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── README.md                  # This file
├── metrics.db                 # Evaluation database (auto-created)
├── docs/
│   ├── ARCHITECTURE.md        # System design
│   ├── API_INTEGRATION.md     # NIM API guide
│   └── EVALUATION.md          # Metrics documentation
└── tests/
    ├── test_agents.py         # Agent tests
    └── test_evaluation.py      # Evaluation tests
```

## 🏗️ Architecture

### Agent Pipeline

```
Image Upload
    ↓
👁️ Condition Agent (Vision)
    ├─ Detect pet species
    ├─ Assess visible injuries
    └─ Classify severity
    ↓
🔎 Response Agent (Reasoning)
    ├─ SEVERE → Emergency first aid + alert
    ├─ MODERATE → NGO + Vet search
    └─ MILD → Routine rescue
    ↓
🚑 Coordination Agent (Planning)
    ├─ Select best resources
    ├─ Create execution plan
    └─ Coordinate contacts
    ↓
✅ Verification Agent (Vision)
    ├─ Analyze post-rescue image
    ├─ Confirm rescue success
    └─ Update database
```

### Quality Assurance Layer

Every output is validated:
- **Hallucination Detection**: Flags unrealistic outputs
- **Input Validation**: Checks species, severities, injuries
- **Output Validation**: Ensures responses match severity
- **Metrics Collection**: Stores accuracy and confidence

## 🤖 NVIDIA NIM Models Used

| Model | Purpose | Free | Priority |
|-------|---------|------|----------|
| **Nemotron Nano 12B Vision** | Analyze pet photos/videos | ✅ | ⭐⭐⭐⭐⭐ |
| **Nemotron 3 Nano Omni 30B** | Reasoning & orchestration | ✅ | ⭐⭐⭐⭐⭐ |
| **Nemotron Embed VL 1B** | Image embeddings (optional) | ✅ | ⭐⭐⭐ |
| **Nemotron Rerank VL 1B** | Result ranking (optional) | ✅ | ⭐⭐⭐ |

All models are free tier! No credit card required for initial usage.

## 📊 Evaluation & Metrics

### Hallucination Detection

The system prevents hallucinations through:

1. **Input Validation**
   - Severity constrained to: severe, moderate, mild, unknown
   - Species validation against known animals
   - Confidence scores must be 0.0-1.0
   - Injury list limited to 5 items max

2. **Output Validation**
   - Response type must be recognized category
   - Urgency must be: CRITICAL, HIGH, MEDIUM, LOW
   - First aid checked for medical safety
   - Plan completeness verified

3. **Red Flags Detected**
   - Unrealistic injuries (alien, vampire, etc.)
   - Extreme ages (1 million years old)
   - Contradictions (severe but described as healthy)
   - Dangerous medical advice

### Accuracy Tracking

```python
# System measures:
- Severity classification accuracy
- Response appropriateness
- Plan quality score
- Verification consistency

# Target metrics:
- Hallucination Score < 0.3 (low = good)
- Accuracy Score > 0.8 (high = good)
- Confidence calibration < 0.1 error
```

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/
```

### Manual Testing
```python
from agents import PetRescueOrchestrator

# Initialize
orchestrator = PetRescueOrchestrator()

# Test with image
rescue_data = orchestrator.process_rescue_case(
    image_base64="...",
    location="123 Main St, City"
)

print(rescue_data)
```

## 📈 Monitoring

### Check System Health
```
Streamlit App → "⚙️ System Health" tab
```

### View Metrics Database
```python
from evaluation import MetricsDB

db = MetricsDB()
metrics = db.get_average_metrics()
print(metrics)
```

### Generate Report
```bash
python -c "from evaluation import MetricsDB; db = MetricsDB(); print(db.get_average_metrics())"
```

## 🚀 Deployment

### Option 1: Streamlit Cloud (Recommended)

1. Push code to GitHub
2. Go to https://streamlit.io/cloud
3. Create new app
4. Select your repo
5. Set secrets (NVIDIA_NIM_API_KEY)
6. Deploy!

### Option 2: Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t pet-rescue .
docker run -p 8501:8501 -e NVIDIA_NIM_API_KEY=your_key pet-rescue
```

### Option 3: Self-Hosted

```bash
# Install supervisor or systemd
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 🔐 Security

- **API Keys**: Stored in `.env`, never committed
- **Images**: Processed locally, not stored permanently
- **Database**: SQLite, can be encrypted
- **Validation**: All inputs validated before processing
- **Safety Checks**: First aid instructions checked for safety

## 📚 Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design details
- [API_INTEGRATION.md](docs/API_INTEGRATION.md) - NVIDIA NIM API guide
- [EVALUATION.md](docs/EVALUATION.md) - Metrics and quality framework

## 🤝 Contributing

Contributions welcome! Areas to help:

- [ ] Add more test cases
- [ ] Improve severity detection
- [ ] Add SMS/WhatsApp notifications
- [ ] Integrate with local NGO databases
- [ ] Add multi-language support
- [ ] Mobile app version

## 📝 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- NVIDIA for free NIM APIs
- Streamlit for amazing UI framework
- Pet rescue community for inspiration
- All pet lovers working to save abandoned animals

## 📞 Support

- **Issues**: GitHub Issues
- **Questions**: Discussions tab
- **NVIDIA NIM Help**: https://docs.nvidia.com/nim/
- **Streamlit Help**: https://docs.streamlit.io/

---

**Made with ❤️ for pet rescue**

🐾 Help us save more pets! Star this repo if you find it useful.
