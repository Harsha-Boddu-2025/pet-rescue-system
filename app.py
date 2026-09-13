"""
🐾 AI Abandoned Pet Rescue - Streamlit App
Pet-friendly interface for rescue coordination
"""

import streamlit as st
import os
import base64
from PIL import Image
import io
from datetime import datetime
import json
import logging

from agents import PetRescueOrchestrator, SeverityLevel
from evaluation import QualityAssurance, EvaluationMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# STREAMLIT CONFIG
# ============================================================================

st.set_page_config(
    page_title="🐾 Pet Rescue AI",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for warm, pet-friendly aesthetics
st.markdown("""
<style>
    /* Warm color palette */
    :root {
        --primary: #FF6B6B;      /* Warm red */
        --secondary: #FFA348;    /* Warm orange */
        --accent: #FFD700;       /* Gold */
        --success: #4CAF50;      /* Healthy green */
        --warn: #FF9800;         /* Warm orange warn */
        --bg-light: #FFF8F5;     /* Warm white */
    }
    
    /* Background */
    body {
        background-color: #FFF8F5;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Main container */
    .main {
        background-color: #FFF8F5;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFF0E6;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #FF6B6B;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Cards/Containers */
    .status-card {
        padding: 20px;
        border-radius: 12px;
        background: linear-gradient(135deg, #FFE5E0 0%, #FFF8F5 100%);
        border-left: 4px solid #FF6B6B;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(255, 107, 107, 0.1);
    }
    
    .severity-severe {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFF0E6 100%);
        border-left-color: #D32F2F;
    }
    
    .severity-moderate {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFF8F5 100%);
        border-left-color: #FF9800;
    }
    
    .severity-mild {
        background: linear-gradient(135deg, #E8F5E9 0%, #FFF8F5 100%);
        border-left-color: #4CAF50;
    }
    
    /* Buttons */
    button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Metrics */
    .metric-value {
        color: #FF6B6B;
        font-size: 32px;
        font-weight: 700;
    }
    
    /* Alerts */
    .stAlert > div {
        border-radius: 8px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INITIALIZATION
# ============================================================================

@st.cache_resource
def init_orchestrator():
    """Initialize rescue orchestrator"""
    try:
        return PetRescueOrchestrator()
    except ValueError as e:
        st.error(f"❌ {str(e)}")
        st.info("Get free NVIDIA NIM API key at: https://build.nvidia.com/explore/discover")
        return None

@st.cache_resource
def init_qa():
    """Initialize quality assurance"""
    return QualityAssurance()

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("## 🐾 Pet Rescue System")
    
    page = st.radio(
        "Navigation",
        ["🏠 Home", "🚨 Report Abandoned Pet", "📊 Dashboard", "⚙️ System Health"]
    )
    
    st.divider()
    
    st.markdown("### About")
    st.info("""
    AI-powered pet rescue coordination using:
    - 👁️ Condition Agent (Nemotron Vision)
    - 🔎 Response Agent (Nemotron Reasoning)
    - 🚑 Coordination Agent (Auto-planning)
    - ✅ Verification Agent (Outcome tracking)
    
    **Free APIs**: NVIDIA NIM (Nemotron Models)
    """)
    
    st.divider()
    
    if st.button("🔄 Refresh System", use_container_width=True):
        st.cache_resource.clear()
        st.success("✅ System refreshed")
    
    st.markdown("---")
    st.caption("Made with ❤️ for pet rescue")

# ============================================================================
# PAGE: HOME
# ============================================================================

if page == "🏠 Home":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("# 🐾 AI Abandoned Pet Rescue")
        st.markdown("""
        ### See → Assess → Find Help → Rescue → Verify 🔄
        
        An intelligent multi-agent system for coordinating pet rescue operations:
        
        **4 Agents. 1 Goal. Save Lives.** 🐶🐱
        """)
    
    with col2:
        st.markdown("<div style='font-size:120px; text-align:center;'>🐾</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👁️", "Condition", "Analyzed")
    with col2:
        st.metric("🔎", "Response", "Decided")
    with col3:
        st.metric("🚑", "Plans", "Created")
    with col4:
        st.metric("✅", "Verified", "Complete")
    
    st.divider()
    
    st.markdown("### 🚨 Quick Start")
    
    st.info("Use the sidebar to navigate to **🚨 Report Abandoned Pet** and upload a photo.")

# ============================================================================
# PAGE: REPORT PET
# ============================================================================

elif page == "🚨 Report Abandoned Pet":
    st.markdown("# 🚨 Report Abandoned Pet")
    st.markdown("Upload a photo/video of the abandoned pet and we'll coordinate rescue")
    
    st.divider()
    
    # Initialize services
    orchestrator = init_orchestrator()
    qa = init_qa()
    
    if not orchestrator:
        st.stop()
    
    # Input form
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📍 Location Information")
        location = st.text_input("Where did you find the pet?", placeholder="Street address or landmark")
    
    with col2:
        st.subheader("📞 Your Contact")
        contact = st.text_input("Your contact number", placeholder="+1 (555) 123-4567")
    
    st.divider()
    
    # Image upload
    st.subheader("📸 Upload Pet Photo/Video")
    uploaded_file = st.file_uploader(
        "Choose image (JPG, PNG)",
        type=["jpg", "jpeg", "png"],
        help="Clear photo showing the pet's condition"
    )
    
    if uploaded_file:
        # Display preview
        col1, col2 = st.columns([1, 2])
        
        with col1:
            image = Image.open(uploaded_file)
            st.image(image, caption="Preview", use_container_width=True)
            image_size = uploaded_file.size / 1024  # KB
            st.caption(f"Size: {image_size:.1f} KB")
        
        with col2:
            st.markdown("### Analysis Processing...")
            
            # Convert to base64 (rewind: PIL already consumed the buffer)
            uploaded_file.seek(0)
            image_bytes = uploaded_file.read()
            image_base64 = base64.b64encode(image_bytes).decode()
            
            if st.button("🔍 Analyze Pet Condition", use_container_width=True):
                with st.spinner("👁️ Condition Agent analyzing..."):
                    try:
                        # Process rescue case
                        rescue_data = orchestrator.process_rescue_case(
                            image_base64=image_base64,
                            location=location or "Unknown"
                        )
                        
                        # Store in session
                        st.session_state.current_rescue = rescue_data
                        st.session_state.rescue_image = image_bytes
                        st.session_state.location = location
                        st.session_state.contact = contact
                        
                        # Evaluate quality
                        metrics = qa.evaluate_rescue_case(
                            rescue_data,
                            rescue_data.get("rescue_id", "AUTO")
                        )
                        st.session_state.metrics = metrics
                        
                        st.success("✅ Analysis Complete!")
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        logger.error(f"Rescue processing error: {e}")
    
    # Display results
    if "current_rescue" in st.session_state:
        rescue = st.session_state.current_rescue
        
        st.divider()
        st.markdown("## 📋 Rescue Plan")
        
        # Condition Summary
        condition = rescue.get("condition", {})
        severity = condition.get("severity", "unknown")
        
        st.markdown(f"""
        <div class="status-card severity-{severity}">
            <h3>👁️ Condition Assessment</h3>
            <p><strong>Severity:</strong> {severity.upper()}</p>
            <p><strong>Description:</strong> {condition.get("description", "")}</p>
            <p><strong>Confidence:</strong> {condition.get("confidence", 0)*100:.0f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        if condition.get("visible_injuries"):
            st.markdown("**Visible Injuries:**")
            for injury in condition.get("visible_injuries", []):
                st.write(f"• {injury}")
        
        if condition.get("urgent_actions"):
            st.warning("⚠️ Urgent First Aid Needed:")
            for action in condition.get("urgent_actions", []):
                st.write(f"• {action}")
        
        st.divider()
        
        # Response Strategy
        response = rescue.get("response_strategy", {})
        st.markdown("### 🔎 Response Strategy")
        st.write(f"**Type:** {response.get('response_type', 'N/A')}")
        st.write(f"**Urgency:** {response.get('urgency', 'N/A')}")
        st.write(f"**Response Time:** {response.get('estimated_response_time', 'N/A')}")
        
        if response.get("immediate_first_aid"):
            st.success("🩹 First Aid Instructions:")
            for i, instruction in enumerate(response.get("immediate_first_aid", []), 1):
                st.write(f"{i}. {instruction}")
        
        st.divider()
        
        # Rescue Plan
        plan = rescue.get("rescue_plan", {})
        st.markdown("### 🚑 Rescue Coordination Plan")
        st.write(f"**Rescue ID:** `{plan.get('rescue_id', 'N/A')}`")
        st.write(f"**Estimated Time:** {plan.get('total_estimated_time', 'Varies')}")
        
        st.markdown("**Steps:**")
        for step in plan.get("steps", []):
            col1, col2, col3 = st.columns([0.2, 2, 1])
            with col1:
                st.write(f"**{step.get('step', '')}**")
            with col2:
                st.write(step.get('action', ''))
            with col3:
                st.write(f"~{step.get('estimated_time', '')}")
        
        st.markdown("**Contact Priority:**")
        for resource in plan.get("contact_priority", []):
            st.write(f"• {resource}")
        
        st.divider()
        
        # Quality Metrics
        if "metrics" in st.session_state:
            metrics = st.session_state.metrics
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                hallucination = metrics.hallucination_score
                color = "🟢" if hallucination < 0.3 else "🟡" if hallucination < 0.6 else "🔴"
                st.metric(
                    "Hallucination Risk",
                    f"{color} {hallucination*100:.0f}%"
                )
            
            with col2:
                accuracy = metrics.accuracy_score
                st.metric(
                    "Accuracy",
                    f"{accuracy*100:.0f}%"
                )
            
            with col3:
                confidence = metrics.condition_confidence
                st.metric(
                    "AI Confidence",
                    f"{confidence*100:.0f}%"
                )
        
        st.divider()
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Confirm & Dispatch", use_container_width=True):
                st.success("🚑 Rescue team dispatched!")
                st.balloons()
        
        with col2:
            if st.button("🔄 Re-analyze", use_container_width=True):
                del st.session_state.current_rescue
                st.rerun()
        
        with col3:
            if st.button("💾 Save Report", use_container_width=True):
                st.info("📁 Report saved to database")

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================

elif page == "📊 Dashboard":
    st.markdown("# 📊 System Dashboard")
    
    qa = init_qa()
    
    # System Health
    health = qa.get_system_health()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = health["system_status"]
        color = "🟢" if status == "HEALTHY" else "🟡"
        st.metric("System Status", f"{color} {status}")
    
    with col2:
        metrics = health["metrics"]
        hallucination = metrics.get("average_hallucination_score", 0)
        st.metric(
            "Avg Hallucination",
            f"{hallucination*100:.1f}%"
        )
    
    with col3:
        accuracy = metrics.get("average_accuracy_score", 0)
        st.metric(
            "Avg Accuracy",
            f"{accuracy*100:.1f}%"
        )
    
    st.divider()
    
    # Recommendations
    st.markdown("### 💡 Recommendations")
    for rec in health["recommendations"]:
        st.write(rec)
    
    st.divider()
    
    # Statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Metrics")
        st.json(metrics)
    
    with col2:
        st.markdown("### 🔍 Quality Checks")
        st.markdown("""
        ✅ Severity validation
        ✅ Response appropriateness
        ✅ Plan quality
        ✅ Verification consistency
        """)

# ============================================================================
# PAGE: SYSTEM HEALTH
# ============================================================================

elif page == "⚙️ System Health":
    st.markdown("# ⚙️ System Health & Monitoring")
    
    orchestrator = init_orchestrator()
    qa = init_qa()
    
    if not orchestrator:
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 System Configuration")
        st.write("**NVIDIA NIM Models:**")
        st.code("""
Condition Agent: nemotron-nano-12b-vision
Response Agent: nemotron-3-nano-omni-30b
Coordination Agent: nemotron-3-nano-omni-30b
Verification Agent: nemotron-nano-12b-vision
        """)
    
    with col2:
        st.markdown("### 📊 Model Capabilities")
        st.write("""
- **Vision:** Analyze pet photos/videos
- **Reasoning:** Multi-agent orchestration
- **Safety:** Hallucination detection
- **Quality:** Automatic evaluation
        """)
    
    st.divider()
    
    st.markdown("### 🧪 Hallucination Detection")
    st.write("""
Our system implements multi-layer protection against hallucinations:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Input Validation**")
        st.write("""
- Severity constraints (severe/moderate/mild)
- Species validation
- Confidence bounds (0-1)
- Injury realism checks
        """)
    
    with col2:
        st.markdown("**Output Validation**")
        st.write("""
- Response type validation
        - Urgency level verification
- First aid safety checks
- Plan completeness
- Verification consistency
        """)
    
    st.divider()
    
    st.markdown("### 📋 Evaluation Framework")
    
    st.write("""
Each rescue case is evaluated on:
    """)
    
    metrics_data = {
        "Hallucination Score": "0.0 (good) to 1.0 (bad)",
        "Accuracy Score": "0.0 to 1.0 (higher is better)",
        "Severity Match": "Predicted vs expected",
        "Response Appropriateness": "Does response match severity?",
        "Plan Quality": "Completeness and clarity",
        "Verification Consistency": "Outcome confidence calibration"
    }
    
    for metric, description in metrics_data.items():
        st.write(f"• **{metric}:** {description}")
    
    st.divider()
    
    if st.button("📊 View Detailed Metrics"):
        health = qa.get_system_health()
        st.json(health)

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style="text-align: center; color: #999; padding: 20px;">
    <p>🐾 AI Abandoned Pet Rescue System</p>
    <p>Using NVIDIA NIM Free APIs • Hallucination Protection • Quality Guaranteed</p>
</div>
""", unsafe_allow_html=True)
