
from typing import Tuple

DISCOUNT_KEYWORDS = [
    "discount", "deal", "cheaper", "lower price", "special price",
    "promotion", "offer", "coupon", "voucher"
]

MANUAL_ESCALATION_KEYWORDS = [
    "speak to", "talk to", "human", "real person", "manager",
    "staff", "employee", "someone", "actual person"
]

COMPLAINT_KEYWORDS = [
    "complaint", "unhappy", "disappointed", "terrible", "awful",
    "worst", "bad service", "not satisfied", "poor"
]

def detect_hitl_need(message: str, agent_response: str = None) -> Tuple[bool, str]:
    """
    Detect if human intervention is needed.
    
    Args:
        message: User's message
        agent_response: Agent's response (to detect uncertainty)
        
    Returns:
        (needs_human, reason)
    """
    message_lower = message.lower()
    
    # 1. Discount/special deal requests
    if any(keyword in message_lower for keyword in DISCOUNT_KEYWORDS):
        return True, "discount_request"
    
    # 2. Manual escalation (user asks for human)
    if any(keyword in message_lower for keyword in MANUAL_ESCALATION_KEYWORDS):
        return True, "manual_escalation"
    
    # 3. Complaints/negative sentiment
    if any(keyword in message_lower for keyword in COMPLAINT_KEYWORDS):
        return True, "complaint"
    
    # 4. Agent uncertainty (optional - check response)
    if agent_response and "I'm not sure" in agent_response:
        return True, "agent_uncertainty"
    
    return False, None