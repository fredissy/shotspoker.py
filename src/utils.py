
from random import choice

AVATARS = ['👾', '👽', '🤖', '👨🏻‍💻', '​😎', '​​🦁​', '👹', '👺', '💀', 
           '🦄', '🐲', '🌵', '🥑', '🍄', '🐙', '🐸', '🦊', '​​🙉​​​',
           '🦁', '🐯', '🐻', '🐨', '🐼', '🐵', '🐔', '🐧', '🧙‍♂️']

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
