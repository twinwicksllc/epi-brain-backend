"""
Debug script to capture 422 error details
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_API_KEY = "your-admin-key-here"  # Replace with actual admin key

def debug_422_error():
    """Capture detailed 422 error information"""
    
    print("=" * 80)
    print("Debugging 422 Error on Admin Usage Endpoint")
    print("=" * 80)
    
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/usage",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        params={"limit": 10}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nFull Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 422:
        error_data = response.json()
        print(f"\n=== VALIDATION ERROR DETAILS ===")
        if 'detail' in error_data:
            print(f"Detail array (shows which field failed):")
            for detail in error_data['detail']:
                print(f"\n  Location: {detail.get('loc', [])}")
                print(f"  Message: {detail.get('msg', '')}")
                print(f"  Type: {detail.get('type', '')}")
                if 'ctx' in detail:
                    print(f"  Context: {detail['ctx']}")

if __name__ == "__main__":
    debug_422_error()
