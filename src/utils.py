
import os

VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
AVATARS = ['👾', '👽', '🤖', '👨🏻‍💻', '​😎', '​​🦁​', '👹', '👺', '💀', 
           '🦄', '🐲', '🌵', '🥑', '🍄', '🐙', '🐸', '🦊', '​​🙉​​​',
           '🦁', '🐯', '🐻', '🐨', '🐼', '🐵', '🐔', '🐧', '🧙‍♂️']

# Calculate base directory (project root) relative to this file
_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_EMOJI_DIR = os.path.join(_BASE_DIR, 'static', 'img', 'emojis')


def choose_user_avatar(username):
    if not username:
        return '👤'
    
    total = sum(ord(char) for char in username)
    index = total % len(AVATARS)
    return AVATARS[index]

def clean_jira_key(raw_key):
    """
    Parses a potential Jira URL to extract just the ticket ID.
    Input: "https://jira.com/browse/PROJ-123?focus=..."
    Output: "PROJ-123"
    """
    if not raw_key: return ""
    
    key = raw_key.strip()
    
    if '/browse/' in key:
        # 1. Split by '/browse/' and take everything after it
        key = key.split('/browse/')[-1]
        
        # 2. Clean up delimiters
        for delimiter in ['/', '?', '#']:
            key = key.split(delimiter)[0]
            
    return key


def get_allowed_custom_emojis():
    """
    Scans the static/img/emojis directory and returns a set of valid web paths.
    Example: {'/static/img/emojis/dog.png', '/static/img/emojis/cat.gif'}
    """
    # Use absolute path calculated from project root for robustness
    allowed = set()
    
    if os.path.exists(_EMOJI_DIR):
        for filename in os.listdir(_EMOJI_DIR):
            # Check extension
            if any(filename.lower().endswith(ext) for ext in VALID_EXTENSIONS):
                # Construct the web-accessible path
                web_path = f'/static/img/emojis/{filename}'
                allowed.add(web_path)
                
    return allowed