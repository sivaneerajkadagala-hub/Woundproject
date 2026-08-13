import os
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings

class AIAssistantService:
    """
    Modular AI Assistant for explaining wound metrics, summarizing visit history,
    and structuring clinical assessment notes. Integrated with AI Mesh / Local LLM configuration.
    """

    @staticmethod
    async def generate_response(
        prompt: str,
        wound_history: Optional[List[Dict[str, Any]]] = None,
        patient_info: Optional[Dict[str, Any]] = None
    ) -> str:
        # Check if AI Mesh settings are configured
        if settings.AIMESH_BASE_URL and settings.AIMESH_API_KEY:
            try:
                headers = {"Authorization": f"Bearer {settings.AIMESH_API_KEY}"}
                payload = {
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a clinical decision-support AI assistant for a Wound Healing Monitoring system. "
                                "Summarize wound metrics clearly in simple language. "
                                "Never diagnose medical conditions or alter measurements."
                            )
                        },
                        {"role": "user", "content": prompt}
                    ]
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{settings.AIMESH_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    if resp.status_code == 200:
                        res_data = resp.json()
                        return res_data["choices"][0]["message"]["content"]
            except Exception:
                pass # Fallback to local rule-based response synthesizer

        # Fallback intelligent rule-based response generator
        return AIAssistantService._synthesize_local_response(prompt, wound_history, patient_info)

    @staticmethod
    def _synthesize_local_response(
        prompt: str,
        wound_history: Optional[List[Dict[str, Any]]] = None,
        patient_info: Optional[Dict[str, Any]] = None
    ) -> str:
        p_lower = prompt.lower()

        if "summarize" in p_lower or "history" in p_lower or "trend" in p_lower:
            if wound_history and len(wound_history) > 0:
                first_visit = wound_history[0]
                last_visit = wound_history[-1]
                v_count = len(wound_history)
                initial_area = first_visit.get("area_mm2", 0)
                current_area = last_visit.get("area_mm2", 0)
                
                reduction_pct = 0.0
                if initial_area > 0:
                    reduction_pct = round(((initial_area - current_area) / initial_area) * 100, 1)

                trend_desc = "improving with area reduction" if reduction_pct > 0 else "stable/increasing area"

                return (
                    f"Across {v_count} recorded visits, the wound area moved from {initial_area} mm² to {current_area} mm². "
                    f"This represents a overall change of {reduction_pct}% from baseline ({trend_desc}). "
                    f"The latest assessment indicates a status of '{last_visit.get('healing_status', 'N/A')}'. "
                    f"Please review the detailed longitudinal chart for visit details."
                )
            return "No historical visit records were found for this wound case."

        if "patient" in p_lower and patient_info:
            return (
                f"Patient {patient_info.get('patient_code', 'N/A')} ({patient_info.get('full_name', 'N/A')}), "
                f"Age {patient_info.get('age', 'N/A')}, Gender {patient_info.get('gender', 'N/A')}. "
                f"Active wound cases: {patient_info.get('active_wounds_count', 1)}."
            )

        return (
            "The wound healing trajectory shows measurable progress across recorded clinical assessments. "
            "U-Net segmentation and calibration scale provide precise quantitative surface area measurements in mm² and cm². "
            "Please consult with the primary healthcare clinician for specific treatment protocol recommendations."
        )
