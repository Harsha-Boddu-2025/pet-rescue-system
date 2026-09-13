"""
AI Abandoned Pet Rescue - Multi-Agent Orchestration
Uses NVIDIA NIM free APIs (Nemotron models)
"""

import os
import json
import base64
import requests
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MODEL IDS (override in .env if NVIDIA renames / you pick different models)
# Browse exact IDs at https://build.nvidia.com/models
# ============================================================================

VISION_MODEL = os.getenv("NIM_VISION_MODEL", "nvidia/nemotron-nano-12b-v2-vl")
REASONING_MODEL = os.getenv("NIM_REASONING_MODEL", "nvidia/nvidia-nemotron-nano-9b-v2")

# ============================================================================
# SEVERITY LEVELS & DATA STRUCTURES
# ============================================================================

class SeverityLevel(Enum):
    SEVERE = "severe"
    MODERATE = "moderate"
    MILD = "mild"
    UNKNOWN = "unknown"

@dataclass
class PetCondition:
    severity: SeverityLevel
    description: str
    visible_injuries: List[str]
    estimated_age: str
    species: str
    urgent_actions: List[str]
    confidence: float

@dataclass
class RescueResponse:
    action_type: str  # "first_aid" | "resource_search" | "coordinate" | "verify"
    content: Dict
    metadata: Dict

# ============================================================================
# JSON HELPERS  (models often wrap JSON in prose or ``` fences)
# ============================================================================

def extract_json(text: str) -> Dict:
    """Pull the first JSON object out of a model response."""
    if not text:
        raise ValueError("Empty model response")

    cleaned = text.strip()

    # Strip markdown code fences
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                cleaned = part
                break

    # Fall back to first {...} span
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"No JSON found in response: {text[:200]}")
        cleaned = cleaned[start:end + 1]

    return json.loads(cleaned)


# ============================================================================
# NVIDIA NIM CLIENT
# ============================================================================

class NIMClient:
    """Unified client for NVIDIA NIM APIs"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        api_key: falls back to NVIDIA_NIM_API_KEY.

        One key works for every model — NIM selects the model per request, not
        per key. Pass a different key only if you want to split traffic across
        two separate NVIDIA accounts to get more free-tier headroom. Two keys
        from the SAME account share one quota, so that buys you nothing.
        """
        self.api_key = api_key or os.getenv("NVIDIA_NIM_API_KEY")
        self.base_url = base_url or os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        
        if not self.api_key:
            raise ValueError("NVIDIA_NIM_API_KEY not set. Get free access at https://build.nvidia.com/explore/discover")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def call_model(self, model: str, messages: List[Dict], temperature: float = 0.7, 
                   max_tokens: int = 1024) -> str:
        """Call NVIDIA NIM text model"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.7
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"NIM API error: {e}")
            raise
    
    def call_vision_model(self, model: str, image_base64: str, prompt: str) -> str:
        """Call NVIDIA NIM vision model"""
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1024
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"NIM Vision API error: {e}")
            raise

# ============================================================================
# AGENT 1: CONDITION AGENT 👁️
# ============================================================================

class ConditionAgent:
    """
    Analyzes abandoned pet photo/video
    Detects: animal type, visible condition, injury severity
    """
    
    MODEL = VISION_MODEL
    
    def __init__(self, nim_client: NIMClient):
        self.nim = nim_client
    
    def analyze(self, image_base64: str, image_type: str = "photo") -> PetCondition:
        """Analyze pet condition from image"""
        
        prompt = """Analyze this abandoned pet photo carefully. Respond ONLY with valid JSON (no markdown, no extra text):
{
    "severity": "severe|moderate|mild|unknown",
    "species": "dog|cat|bird|other",
    "description": "brief 1-line description of pet's condition",
    "visible_injuries": ["injury1", "injury2"],
    "estimated_age": "puppy|adult|senior|unknown",
    "confidence": 0.0-1.0,
    "urgent_actions": ["action1", "action2"]
}

Be CONSERVATIVE. Only mark SEVERE if: unconscious, heavy bleeding, pale gums, broken limbs, or difficulty breathing.
Mark MODERATE if: visible wounds, limping, distressed.
Mark MILD if: appearance OK but clearly abandoned.
"""
        
        try:
            response = self.nim.call_vision_model(
                model=self.MODEL,
                image_base64=image_base64,
                prompt=prompt
            )
            
            # Parse response carefully to avoid hallucinations
            data = extract_json(response)
            
            # Validate parsed data
            validated = self._validate_condition_data(data)
            
            logger.info(f"Condition Analysis: {validated['severity']}")
            
            return PetCondition(
                severity=SeverityLevel(validated["severity"]),
                description=validated["description"],
                visible_injuries=validated.get("visible_injuries", []),
                estimated_age=validated.get("estimated_age", "unknown"),
                species=validated.get("species", "unknown"),
                urgent_actions=validated.get("urgent_actions", []),
                confidence=validated.get("confidence", 0.5)
            )
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Condition parsing error: {e}")
            return PetCondition(
                severity=SeverityLevel.UNKNOWN,
                description="Unable to analyze - image may be unclear",
                visible_injuries=[],
                estimated_age="unknown",
                species="unknown",
                urgent_actions=[],
                confidence=0.0
            )
    
    def _validate_condition_data(self, data: Dict) -> Dict:
        """Validate and sanitize condition analysis"""
        
        # Validate severity
        valid_severities = ["severe", "moderate", "mild", "unknown"]
        severity = data.get("severity", "unknown").lower()
        if severity not in valid_severities:
            severity = "unknown"
        
        # Validate confidence
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        
        # Sanitize lists
        injuries = data.get("visible_injuries", [])
        if not isinstance(injuries, list):
            injuries = []
        injuries = [str(i)[:50] for i in injuries[:5]]  # Max 5, 50 chars each
        
        actions = data.get("urgent_actions", [])
        if not isinstance(actions, list):
            actions = []
        actions = [str(a)[:100] for a in actions[:5]]  # Max 5, 100 chars each
        
        return {
            "severity": severity,
            "species": str(data.get("species", "unknown"))[:20],
            "description": str(data.get("description", "Unknown condition"))[:200],
            "visible_injuries": injuries,
            "estimated_age": str(data.get("estimated_age", "unknown"))[:20],
            "confidence": confidence,
            "urgent_actions": actions
        }

# ============================================================================
# AGENT 2: RESPONSE AGENT 🔎
# ============================================================================

class ResponseAgent:
    """
    Decides what help is needed based on severity
    Severe: First aid guidance + emergency alerts
    Moderate: NGO + Vet search
    Mild: NGO / Shelter search
    """
    
    MODEL = REASONING_MODEL
    
    def __init__(self, nim_client: NIMClient):
        self.nim = nim_client
    
    def decide_response(self, condition: PetCondition, location: str = "Unknown") -> Dict:
        """Decide response strategy based on pet condition"""
        
        if condition.severity == SeverityLevel.SEVERE:
            return self._severe_response(condition, location)
        elif condition.severity == SeverityLevel.MODERATE:
            return self._moderate_response(condition, location)
        elif condition.severity == SeverityLevel.MILD:
            return self._mild_response(condition, location)
        else:
            return self._unknown_response(condition, location)
    
    def _severe_response(self, condition: PetCondition, location: str) -> Dict:
        """Emergency protocol for severe injuries"""
        
        prompt = f"""A {condition.species} is severely injured with: {', '.join(condition.visible_injuries)}

Provide ONLY JSON:
{{
    "response_type": "emergency_first_aid",
    "urgency": "CRITICAL",
    "immediate_first_aid": [
        "instruction 1",
        "instruction 2"
    ],
    "resources_needed": ["emergency_vet", "transport"],
    "estimated_response_time": "minutes"
}}
"""
        
        try:
            response = self.nim.call_model(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3  # Lower temp for critical decisions
            )
            data = extract_json(response)
            return self._sanitize_response(data)
        except Exception as e:
            logger.error(f"Severe response error: {e}")
            return {
                "response_type": "emergency_first_aid",
                "urgency": "CRITICAL",
                "immediate_first_aid": ["Keep pet warm", "Don't move injured limbs", "Stop bleeding if visible"],
                "resources_needed": ["emergency_vet", "transport"]
            }
    
    def _moderate_response(self, condition: PetCondition, location: str) -> Dict:
        """Standard protocol for moderate injuries"""
        return {
            "response_type": "standard_rescue",
            "urgency": "HIGH",
            "search_resources": ["vet_clinics", "ngos", "shelters"],
            "estimated_response_time": "hours"
        }
    
    def _mild_response(self, condition: PetCondition, location: str) -> Dict:
        """Routine rescue for mild/no visible injury"""
        return {
            "response_type": "routine_rescue",
            "urgency": "MEDIUM",
            "search_resources": ["ngos", "shelters"],
            "estimated_response_time": "same_day"
        }
    
    def _unknown_response(self, condition: PetCondition, location: str) -> Dict:
        """Fallback for unknown/unclear situations"""
        return {
            "response_type": "assessment_needed",
            "urgency": "MEDIUM",
            "search_resources": ["ngos", "veterinary_experts"],
            "note": "Initial image unclear - needs expert assessment"
        }
    
    def _sanitize_response(self, data: Dict) -> Dict:
        """Validate response data"""
        valid_types = ["emergency_first_aid", "standard_rescue", "routine_rescue", "assessment_needed"]
        response_type = data.get("response_type", "assessment_needed")
        if response_type not in valid_types:
            response_type = "assessment_needed"
        
        data["response_type"] = response_type
        return data

# ============================================================================
# AGENT 3: COORDINATION AGENT 🚑
# ============================================================================

class CoordinationAgent:
    """
    Coordinates rescue execution
    Selects best NGO/rescuer, creates plan
    """
    
    MODEL = REASONING_MODEL
    
    def __init__(self, nim_client: NIMClient):
        self.nim = nim_client
    
    def create_rescue_plan(self, condition: PetCondition, response: Dict, 
                          location: str = "Unknown") -> Dict:
        """Create actionable rescue plan"""
        
        prompt = f"""Create a rescue plan for a {condition.species} at {location}.
        
Condition: {condition.description}
Severity: {condition.severity.value}
Required resources: {response.get('search_resources', [])}

Respond ONLY with JSON:
{{
    "rescue_id": "RESCUE_2024_XXXXX",
    "steps": [
        {{"step": 1, "action": "...", "estimated_time": "mins"}},
        {{"step": 2, "action": "...", "estimated_time": "mins"}}
    ],
    "required_resources": ["item1", "item2"],
    "contact_priority": ["emergency_vet", "ngo"],
    "total_estimated_time": "30 mins"
}}
"""
        
        try:
            response_text = self.nim.call_model(
                model=self.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            data = extract_json(response_text)
            return self._sanitize_plan(data)
        except Exception as e:
            logger.error(f"Coordination error: {e}")
            return self._default_plan()
    
    def _sanitize_plan(self, data: Dict) -> Dict:
        """Validate rescue plan"""
        plan = {
            "rescue_id": str(data.get("rescue_id", "RESCUE_AUTO"))[:50],
            "steps": data.get("steps", [])[:10],
            "required_resources": data.get("required_resources", [])[:10],
            "contact_priority": data.get("contact_priority", [])[:5],
            "total_estimated_time": str(data.get("total_estimated_time", "Unknown"))[:50]
        }
        return plan
    
    def _default_plan(self) -> Dict:
        """Fallback plan"""
        return {
            "rescue_id": "RESCUE_FALLBACK",
            "steps": [
                {"step": 1, "action": "Locate pet and ensure safety"},
                {"step": 2, "action": "Contact nearest veterinary clinic"},
                {"step": 3, "action": "Contact local animal rescue"}
            ],
            "required_resources": ["transport", "first_aid_kit"],
            "contact_priority": ["emergency_vet", "local_ngo"],
            "total_estimated_time": "Varies"
        }

# ============================================================================
# AGENT 4: VERIFICATION AGENT ✅
# ============================================================================

class VerificationAgent:
    """
    Verifies rescue outcome
    Analyzes post-rescue image
    """
    
    MODEL = VISION_MODEL
    
    def __init__(self, nim_client: NIMClient):
        self.nim = nim_client
    
    def verify_rescue(self, before_image: str, after_image: str, 
                     rescue_id: str) -> Tuple[str, Dict]:
        """
        Verify if rescue was successful
        Returns: (status, details)
        """
        
        prompt = """Compare these pet images (before rescue, after rescue).
        
Respond ONLY with JSON:
{
    "rescue_status": "RESCUED|NOT_RESCUED|INCONCLUSIVE",
    "confidence": 0.0-1.0,
    "observations": "detailed comparison",
    "next_action": "close|re_plan|monitor"
}

RESCUED: Pet is visibly in better condition, receiving care, in shelter/vet.
NOT_RESCUED: Pet still abandoned or condition worsened.
INCONCLUSIVE: Can't determine from images.
"""
        
        try:
            response = self.nim.call_vision_model(
                model=self.MODEL,
                image_base64=after_image,
                prompt=prompt + f"\n\nRescue ID: {rescue_id}"
            )
            
            data = extract_json(response)
            status = data.get("rescue_status", "INCONCLUSIVE")
            
            return status, self._sanitize_verification(data)
        
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return "INCONCLUSIVE", {"error": str(e)}
    
    def _sanitize_verification(self, data: Dict) -> Dict:
        """Validate verification result"""
        valid_statuses = ["RESCUED", "NOT_RESCUED", "INCONCLUSIVE"]
        status = data.get("rescue_status", "INCONCLUSIVE")
        if status not in valid_statuses:
            status = "INCONCLUSIVE"
        
        return {
            "rescue_status": status,
            "confidence": max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
            "observations": str(data.get("observations", ""))[:500],
            "next_action": data.get("next_action", "monitor")
        }

# ============================================================================
# ORCHESTRATOR
# ============================================================================

class PetRescueOrchestrator:
    """Main orchestrator - coordinates all 4 agents"""
    
    def __init__(self, api_key: str = None,
                 vision_api_key: str = None,
                 reasoning_api_key: str = None):
        """
        Normal setup: set NVIDIA_NIM_API_KEY only. All four agents share it.

        Optional split: set NIM_VISION_API_KEY and/or NIM_REASONING_API_KEY to
        route the vision agents (Condition, Verification) and the reasoning
        agents (Response, Coordination) through different keys. Worth doing
        only when the two keys belong to different NVIDIA accounts — keys from
        one account share a single quota.
        """
        shared = api_key or os.getenv("NVIDIA_NIM_API_KEY")

        vision_key = vision_api_key or os.getenv("NIM_VISION_API_KEY") or shared
        reasoning_key = reasoning_api_key or os.getenv("NIM_REASONING_API_KEY") or shared

        # Reuse one client when the keys match, so we don't open two identical sessions
        self.vision_nim = NIMClient(api_key=vision_key)
        self.reasoning_nim = (
            self.vision_nim if reasoning_key == vision_key else NIMClient(api_key=reasoning_key)
        )

        # Kept for backwards compatibility with code that referenced .nim
        self.nim = self.vision_nim

        self.condition_agent = ConditionAgent(self.vision_nim)
        self.response_agent = ResponseAgent(self.reasoning_nim)
        self.coordination_agent = CoordinationAgent(self.reasoning_nim)
        self.verification_agent = VerificationAgent(self.vision_nim)
    
    def process_rescue_case(self, image_base64: str, location: str = "Unknown") -> Dict:
        """
        Full end-to-end rescue processing
        1. Analyze condition
        2. Decide response
        3. Create plan
        """
        
        logger.info("🐾 Starting rescue case processing...")
        
        # Step 1: Analyze condition
        logger.info("👁️ Condition Agent: Analyzing pet...")
        condition = self.condition_agent.analyze(image_base64)
        
        # Step 2: Decide response
        logger.info("🔎 Response Agent: Determining response strategy...")
        response = self.response_agent.decide_response(condition, location)
        
        # Step 3: Create plan
        logger.info("🚑 Coordination Agent: Creating rescue plan...")
        plan = self.coordination_agent.create_rescue_plan(condition, response, location)
        
        return {
            "status": "plan_created",
            "rescue_id": plan.get("rescue_id"),
            "condition": {
                "severity": condition.severity.value,
                "description": condition.description,
                "visible_injuries": condition.visible_injuries,
                "confidence": condition.confidence
            },
            "response_strategy": response,
            "rescue_plan": plan
        }
    
    def verify_rescue_outcome(self, rescue_id: str, after_image: str) -> Dict:
        """Verify rescue completion"""
        
        logger.info(f"✅ Verification Agent: Checking outcome for {rescue_id}...")
        
        status, details = self.verification_agent.verify_rescue(
            before_image="",
            after_image=after_image,
            rescue_id=rescue_id
        )
        
        return {
            "rescue_id": rescue_id,
            "outcome": status,
            "verification_details": details
        }
