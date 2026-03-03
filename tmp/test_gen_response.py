
import sys
import os

# Add project root to sys.path
project_root = r"c:\Users\UdayGupta\OneDrive - Meridian Solutions\Documents\GitHub\NEW\assignment"
sys.path.append(project_root)

from services.response_generator import generate_response
from models.schemas import PersonaType
from services.knowledge_base import search_knowledge_base

def test_responses():
    persona = PersonaType.GENERAL_USER
    test_inputs = ["hi", "billing", "thanks", "Connect me with a manager", "random message"]
    
    for msg in test_inputs:
        kb = search_knowledge_base(msg, persona)
        # Simulate escalation for the manager request
        should_esc = "manager" in msg.lower()
        
        resp, sugg = generate_response(msg, persona, kb, should_esc, 0.0)
        # Remove emojis for clean terminal output
        resp_clean = resp.encode('ascii', 'ignore').decode('ascii')
        print(f"INPUT: '{msg}'")
        print(f"HAS KB ARTICLE: {len(kb) > 0}")
        print(f"RESPONSE:\n{resp_clean}")
        print("-" * 50)

if __name__ == "__main__":
    test_responses()
