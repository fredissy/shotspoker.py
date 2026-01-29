
import os

EMOJI_REL_PATH = '../static/img/emojis'
VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
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


def get_allowed_custom_emojis():
    """
    Scans the static/img/emojis directory and returns a set of valid web paths.
    Example: {'/static/img/emojis/dog.png', '/static/img/emojis/cat.gif'}
    """
    # Calculate absolute path relative to this file (src/utils.py)
    base_dir = os.path.dirname(__file__)
    emoji_dir = os.path.join(base_dir, EMOJI_REL_PATH)
    
    # Resolve to absolute path to prevent path traversal
    emoji_dir_real = os.path.realpath(emoji_dir)
    
    allowed = set()
    
    if os.path.exists(emoji_dir_real):
        for filename in os.listdir(emoji_dir_real):
            file_path = os.path.join(emoji_dir_real, filename)
            
            # Resolve symbolic links and verify the file is within the intended directory
            file_real_path = os.path.realpath(file_path)
            
            # Security check: ensure the resolved path is still within emoji_dir
            if not file_real_path.startswith(emoji_dir_real + os.sep):
                continue
            
            # Only include regular files, not directories
            if not os.path.isfile(file_real_path):
                continue
            
            # Check extension
            if any(filename.lower().endswith(ext) for ext in VALID_EXTENSIONS):
                # Construct the web-accessible path
                web_path = f'/static/img/emojis/{filename}'
                allowed.add(web_path)
                
    return allowed