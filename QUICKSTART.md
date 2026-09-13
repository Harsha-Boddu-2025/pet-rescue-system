# 🚀 Quick Start Guide

Get the Pet Rescue System running in **5 minutes**.

## Prerequisites

- Python 3.9 or higher
- Git
- NVIDIA NIM API Key (free)

## Step 1: Get NVIDIA NIM API Key (2 min)

1. Visit: https://build.nvidia.com/explore/discover
2. Sign up (free, no credit card needed)
3. Navigate to "API keys" section
4. Create a new key
5. Copy the key

## Step 2: Clone & Setup (2 min)

```bash
# Clone repository
git clone https://github.com/yourusername/pet-rescue-system.git
cd pet-rescue-system

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Add your API key to .env
# Edit .env and set: NVIDIA_NIM_API_KEY=your_key_here
```

## Step 3: Run the App (1 min)

```bash
streamlit run app.py
```

Your app will open at: `http://localhost:8501`

## Step 4: Test the System (1 min)

1. Go to **"🚨 Report Abandoned Pet"**
2. Enter a location: "123 Main St, City"
3. Upload any pet photo (test image)
4. Click **"🔍 Analyze Pet Condition"**
5. Watch the AI analyze and create a rescue plan!

---

## What You'll See

### Upload Phase
```
📍 Location: 123 Main St
📸 Photo: cat.jpg
```

### Analysis Phase
```
👁️ Condition Agent: Analyzing...
🔎 Response Agent: Deciding...
🚑 Coordination Agent: Planning...
```

### Results
```
Severity: Moderate
Description: Injured cat
Injuries: Visible wounds
First Aid: Not needed
Response Type: Standard rescue
Rescue Plan: 3-step plan
```

---

## Next Steps

1. **Read Documentation**
   - [ARCHITECTURE.md](docs/ARCHITECTURE.md) - How it works
   - [API_INTEGRATION.md](docs/API_INTEGRATION.md) - API details
   - [EVALUATION.md](docs/EVALUATION.md) - Quality metrics
   - [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deploy to production

2. **Explore the Code**
   - `app.py` - Streamlit interface
   - `agents.py` - AI agents
   - `evaluation.py` - Quality assurance

3. **Deploy Live**
   - Streamlit Cloud (easiest)
   - Docker
   - AWS EC2
   - DigitalOcean

---

## Troubleshooting

### API Key Error
```
ValueError: NVIDIA_NIM_API_KEY not set
```
→ Check `.env` file has your API key

### Module Not Found
```
ModuleNotFoundError: No module named 'streamlit'
```
→ Install dependencies: `pip install -r requirements.txt`

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
→ Run on different port: `streamlit run app.py --server.port 8502`

### Image Upload Error
```
Error processing image
```
→ Use a small clear pet photo (JPG or PNG)

---

## System Requirements

| Component | Minimum |
|-----------|---------|
| Python | 3.9+ |
| RAM | 512 MB |
| Disk | 100 MB |
| Internet | Required (API calls) |
| GPU | Not required (cloud inference) |

---

## What Happens Next?

1. **Your pet photo** → Uploaded to system
2. **👁️ Condition Agent** → Analyzes severity + injuries
3. **🔎 Response Agent** → Decides first aid needs
4. **🚑 Coordination Agent** → Creates rescue plan
5. **✅ Verification Agent** → Tracks success

All powered by **free NVIDIA NIM APIs** 🚀

---

## Need Help?

- **Docs**: Read [README.md](README.md)
- **Issues**: GitHub Issues tab
- **Questions**: Discussions tab
- **NVIDIA Help**: https://docs.nvidia.com/nim/

---

## What's Next After Setup?

### 1. Upload a Real Case
- Take a photo of an abandoned pet
- Upload and analyze
- System creates rescue plan

### 2. Deploy to Production
```bash
# Streamlit Cloud (recommended)
git push origin main
# → Auto-deploys to streamlit.io

# Or Docker
docker build -t pet-rescue .
docker run -p 8501:8501 -e NVIDIA_NIM_API_KEY=xxx pet-rescue
```

### 3. Monitor Quality
- View **"⚙️ System Health"** tab
- Check hallucination scores
- Track accuracy metrics

### 4. Contribute
- Add more agents
- Improve prompts
- Add NGO database
- Create mobile app

---

**Happy rescuing! 🐾**

Questions? Check [README.md](README.md) for full documentation.
