"""
Personality Modes API Endpoints
"""

from fastapi import APIRouter, Depends
from typing import List, Dict

from app.models.user import User
from app.core.dependencies import get_current_active_user

router = APIRouter()

# Available personality modes
AVAILABLE_MODES = {
    "personal_friend": {
        "name": "Personal Friend",
        "icon": "💙",
        "description": "Daily companion, emotional support, combat loneliness",
        "tier_required": "free",
        "color": "#3B82F6"
    },
    "sales_agent": {
        "name": "Sales Agent",
        "icon": "🎯",
        "description": "Sales training and NEBP practice",
        "tier_required": "pro",
        "color": "#F59E0B"
    },
    "student_tutor": {
        "name": "Student/Tutor",
        "icon": "🎓",
        "description": "Trade school training and skill development",
        "tier_required": "pro",
        "color": "#10B981"
    },
    "kids_learning": {
        "name": "Kids Learning",
        "icon": "👶",
        "description": "Early childhood education",
        "tier_required": "pro",
        "color": "#EC4899"
    },
    "christian_companion": {
        "name": "Christian Companion",
        "icon": "✝️",
        "description": "Faith-based guidance and Bible study",
        "tier_required": "pro",
        "color": "#8B5CF6"
    },
    "customer_service": {
        "name": "Customer Service",
        "icon": "💼",
        "description": "Professional customer interactions training",
        "tier_required": "pro",
        "color": "#6366F1"
    },
    "psychology_expert": {
        "name": "Psychology Expert",
        "icon": "🧠",
        "description": "Emotional intelligence and mental wellness",
        "tier_required": "pro",
        "color": "#14B8A6"
    },
    "business_mentor": {
        "name": "Business Mentor",
        "icon": "💼",
        "description": "Business growth and entrepreneurship",
        "tier_required": "pro",
        "color": "#64748B"
    },
    "weight_loss_coach": {
        "name": "Weight Loss Coach",
        "icon": "💪",
        "description": "Fitness and weight loss transformation",
        "tier_required": "pro",
        "color": "#EF4444"
    }
}


@router.get("/", response_model=List[Dict])
async def get_available_modes(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available personality modes for current user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of available modes with metadata
    """
    modes = []
    
    for mode_id, mode_data in AVAILABLE_MODES.items():
        mode_info = {
            "id": mode_id,
            **mode_data,
            "available": True
        }
        
        # Check if user has access to this mode
        if mode_data["tier_required"] == "pro":
            if current_user.is_free_tier:
                mode_info["available"] = False
                mode_info["upgrade_required"] = True
        
        modes.append(mode_info)
    
    return modes


@router.get("/{mode_id}")
async def get_mode_details(
    mode_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details for a specific personality mode
    
    Args:
        mode_id: Mode identifier
        current_user: Current authenticated user
        
    Returns:
        Mode details
    """
    from app.core.exceptions import InvalidMode
    
    if mode_id not in AVAILABLE_MODES:
        raise InvalidMode(mode_id)
    
    mode_data = AVAILABLE_MODES[mode_id]
    
    # Check if user has access
    available = True
    if mode_data["tier_required"] == "pro" and current_user.is_free_tier:
        available = False
    
    return {
        "id": mode_id,
        **mode_data,
        "available": available,
        "upgrade_required": not available
    }


@router.post("/switch")
async def switch_mode(
    mode_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Switch to a different personality mode
    
    Args:
        mode_id: Mode identifier to switch to
        current_user: Current authenticated user
        
    Returns:
        Success message with new mode
    """
    from app.core.exceptions import InvalidMode
    from fastapi import HTTPException, status
    
    if mode_id not in AVAILABLE_MODES:
        raise InvalidMode(mode_id)
    
    mode_data = AVAILABLE_MODES[mode_id]
    
    # Check if user has access
    if mode_data["tier_required"] == "pro" and current_user.is_free_tier:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Mode '{mode_data['name']}' requires Pro tier. Please upgrade."
        )
    
    return {
        "message": f"Switched to {mode_data['name']} mode",
        "mode_id": mode_id,
        "mode_name": mode_data["name"]
    }