import base64
import re

def is_base64_encoded(s: str) -> bool:
    # Remove whitespace
    s = s.strip()
    # Check length
    if len(s) % 4 != 0:
        return False
    # Check allowed characters
    if not re.fullmatch(r'[A-Za-z0-9+/]*={0,2}', s):
        return False
    try:
        # Try to decode, validate ensures only valid base64
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False