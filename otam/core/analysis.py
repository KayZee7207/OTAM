#import google.generativeai as genai
import json
import os

# Load secrets
try:
    with open("secrets.json", "r") as f:
        secrets = json.load(f)
        API_KEY = secrets.get("GEMINI_API_KEY")
        if API_KEY:
            genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Error loading secrets: {e}")
    API_KEY = None

COC = """
OFFICIAL CODE OF CONDUCT:

SECTION A - BE NICE TO EACH OTHER
1. Respect for all other members is mandatory.
2. Harassment and baiting of any community member is not acceptable.
3. Intentionally making false accusations is abusive.
4. "It was just a joke" does not excuse harassment.
5. Do not flame players for using strategies which may seem subjectively suboptimal.
6. Team Games: Disregarding teamwork or refusing to cooperate is not acceptable.
7. Spoiling Games: Dragging out won games, leaving early without valid reason, or pausing to disrupt is unsportsmanlike.
8. Boss Abuse: Using boss mode to abuse players (e.g., kickbanning rule-abiding players) is forbidden.

SECTION B - RULES FOR FUN
1. Inappropriate Topics: No illegal topics, gambling, drugs, self-harm, crypto scams, politics, or sexually explicit chat.
2. Discrimination: Abuse based on gender, race, sexual orientation, disability, religion, etc., is never acceptable.
3. Offensive Names: No offensive nicknames, impersonation, or politically charged names.
4. Griefing: No teamkilling, hurting/imprisoning allies, stealing units, or throwing games.
   - Reclaiming allied wrecks (except commanders for tech rush) is allowed.
   - Self-destructing units to deny them to your team is griefing.
5. Unfair Advantages: No cheating, map hacking, spec cheating, or smurfing.
6. Communications Abuse: No spamming, inappropriate drawings, or obscuring views with pings/draws.

SECTION C - UNACCEPTABLE BEHAVIOR
1. Malicious Behavior: No constant unwarranted negative information or taking credit for others' work.
2. Malicious Speech: No hate speech, self-harm encouragement, real-life threats, or celebration of horrific events.
3. Hacking/Doxxing: No hacking accounts/infrastructure or revealing personal info.
4. Circumvention: Do not create new accounts to evade bans.
"""

def analyze_chat_logs(chat_lines):
    """
    Analyzes chat logs using Gemini AI.
    chat_lines: list of (timestamp, player_name, msg_content)
    """
    if not API_KEY:
        return {
            "summary": "Error: Gemini API Key not found in secrets.json",
            "toxicity_score": 0,
            "flagged_messages": [],
            "recommendation": "Check configuration"
        }

    print(f"Analyzing {len(chat_lines)} chat lines with AI...")
    
    # Format chat for the prompt
    chat_text = "\n".join([f"[{t:.1f}s] {p}: {m}" for t, p, m in chat_lines])
    
    prompt = f"""
    You are a strict moderator for the game Beyond All Reason. Analyze the following game chat log for SEVERE violations of the Code of Conduct.
    
    {COC}
    
    CHAT log:
    {chat_text}
    
    INSTRUCTIONS:
    1. Focus ONLY on severe and toxic behavior (e.g., hate speech, slurs, griefing, persistent harassment).
    2. IGNORE minor arguments, "silly fights", or frustration that does not cross the line into abuse.
    3. For each violation, cite the specific Section and Paragraph from the COC (e.g., "Section A, Para 2").
    
    OUTPUT FORMAT (JSON):
    {{
        "summary": "Brief summary of the chat interaction and any issues.",
        "toxicity_score": (0-10 integer, where 0 is clean and 10 is severe toxicity),
        "flagged_messages": [
            {{ 
                "player": "PlayerName", 
                "message": "The toxic message", 
                "coc_violation": "Section X, Para Y",
                "comment": "Brief explanation of why this is a violation"
            }}
        ],
        "toxic_players": ["PlayerName1", "PlayerName2"]
    }}
    
    Analyze strictly based on the provided chat. If the chat is clean or only contains minor bickering, return score 0 and empty flagged_messages.
    """
    
    print(f"DEBUG: Prompt sent to API:\n{prompt}")
    
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        
        print(f"DEBUG: API Response:\n{response.text}")
        
        try:
            result = json.loads(response.text, strict=False)
        except json.JSONDecodeError:
            print(f"Raw AI response: {response.text}")
            raise
        return result
    except Exception as e:
        print(f"AI Analysis failed: {e}")
        return {
            "summary": f"AI Analysis failed: {str(e)}",
            "toxicity_score": 0,
            "flagged_messages": [],
            "recommendation": "Error"
        }
