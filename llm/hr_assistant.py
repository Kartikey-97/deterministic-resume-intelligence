import requests
import json
import re
import logging
from typing import Dict, Any

# Configure logging for enterprise-grade observability
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_json_response(raw_text: str) -> str:
    """
    Robust JSON cleaner to extract valid JSON from LLM responses that might contain
    markdown formatting or conversational fluff.
    """
    try:
        # Safely match markdown backticks using unicode hex \x60 to prevent copy-paste UI bugs
        match = re.search(r'\x60\x60\x60(?:json)?\s*(\{.*?\})\s*\x60\x60\x60', raw_text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Fallback: Find the first { and the last }
        start_idx = raw_text.find('{')
        end_idx = raw_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return raw_text[start_idx:end_idx + 1].strip()
            
        return raw_text.strip()
    except Exception as e:
        logger.error(f"Error cleaning JSON response: {e}")
        return raw_text

def analyze_candidate_llm(resume_text: str, job_description: str = "General Software Engineering Role") -> Dict[str, Any]:
    """
    Acts as an AI HR Assistant. Sends the parsed text to a local LLM to generate
    a summary, skill match, and recommendation without breaking the deterministic engine.
    
    This is executed as a purely isolated post-processing step to guarantee O(N) 
    deterministic scoring latency is completely unaffected.
    """
    
    # Truncate text to 4000 characters to prevent massive token payloads and context window overflows
    clean_text = resume_text[:4000] 
    
    system_prompt = f"""
    You are an expert HR Technical Recruiter and Senior Engineering Manager. 
    Analyze the following candidate's resume strictly against this role/domain: {job_description}.
    
    You MUST output ONLY a raw, valid JSON object. Absolutely NO markdown formatting, NO conversational text, and NO preamble.
    
    Strict Output Schema:
    {{
        "executive_overview": "A punchy, 2-sentence summary of the candidate's core value proposition, experience level, and primary tech stack.",
        "strengths": [
            "Highly specific strength 1 based on actual data", 
            "Highly specific strength 2 based on actual data", 
            "Highly specific strength 3 based on actual data"
        ],
        "missing_skills": [
            "Potential gap 1 relative to the role", 
            "Potential gap 2 relative to the role"
        ],
        "hr_recommendation": "A short, decisive 1-sentence rationale on whether to shortlist or reject this candidate for this specific role."
    }}
    """
    
    try:
        logger.info(f"Triggering LLM analysis for target role: {job_description}")
        
        # Using a local Ollama endpoint for zero-cost, private processing
        # This can be swapped to OpenAI/Gemini by changing the endpoint and adding Authorization headers
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2", 
                "system": system_prompt,
                "prompt": clean_text,
                "stream": False,
                "format": "json",
                # 🔥 THE FIX: Force the LLM to be 100% Deterministic
                "options": {
                    "temperature": 0.0,
                    "seed": 42
                }
            },
            timeout=25 
        )
        if response.status_code == 200:
            raw_result = response.json().get("response", "")
            cleaned_result = clean_json_response(raw_result)
            
            # Parse and validate the response
            parsed_json = json.loads(cleaned_result)
            
            # Ensure all keys exist to prevent frontend KeyError crashes
            return {
                "executive_overview": parsed_json.get("executive_overview", "Overview not generated."),
                "strengths": parsed_json.get("strengths", ["No specific strengths identified."]),
                "missing_skills": parsed_json.get("missing_skills", ["No missing skills identified."]),
                "hr_recommendation": parsed_json.get("hr_recommendation", "Review manually.")
            }
        else:
            logger.warning(f"LLM API returned non-200 status: {response.status_code}")
            
    except requests.exceptions.RequestException as req_err:
        logger.error(f"LLM Connection Error: Ensure Ollama is running locally. {req_err}")
    except json.JSONDecodeError as json_err:
        logger.error(f"LLM JSON Decode Error: Model returned malformed JSON. {json_err}")
    except Exception as e:
        logger.error(f"Unexpected error in LLM processing: {e}")
        
    # Enterprise Fallback Payload (Triggered if Ollama is off, times out, or fails)
    return {
        "executive_overview": "⚠️ AI Engine offline or unreachable. Please ensure the local Ollama service is running on port 11434.",
        "strengths": ["Deterministic Parsing Activated", "Structured Data Extracted", "Mathematical Scoring Completed"],
        "missing_skills": ["Generative AI Insights (Service Offline)"],
        "hr_recommendation": "Rely strictly on the deterministic score and parsed data above."
    }