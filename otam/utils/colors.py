from collections import defaultdict
import random

# --- Constants & Palettes (DEX Implementation) ---

SURVIVAL_COLOR_NUM = 1
SURVIVAL_COLOR_VARIATION = 0
FFA_COLOR_NUM = 1
FFA_COLOR_VARIATION = 0
COLOR_VARIATION_DELTA = 128

# Special Colors
COLOR_ARM_BLUE = "#004DFF"
COLOR_COR_RED = "#FF1005"
COLOR_SCAV_PURP = "#6809A1"
COLOR_RAPTOR_ORANGE = "#CC8914"
COLOR_GAIA_GRAY = "#7F7F7F"
COLOR_LEG_GREEN = "#0CE818"

# IceXuick Colors V6
FFA_COLORS = [
    "#004DFF", "#FF1005", "#0CE908", "#FFD200", "#F80889", "#09F5F5", "#FF6107", 
    "#F190B3", "#097E1C", "#C88B2F", "#7CA1FF", "#9F0D05", "#3EFFA2", "#F5A200", 
    "#C4A9FF", "#0B849B", "#B4FF39", "#FF68EA", "#D8EEFF", "#689E3D", "#B04523", 
    "#FFBB7C", "#3475FF", "#DD783F", "#FFAAF3", "#4A4376", "#773A01", "#B7EA63", 
    "#9F0D05", "#7EB900"
]

SURVIVAL_COLORS = [
    "#0B3EF3", "#FF1005", "#0CE908", "#ffab8c", "#09F5F5", "#FCEEA4", "#097E1C", 
    "#F190B3", "#F80889", "#3EFFA2", "#911806", "#7CA1FF", "#3c7a74", "#B04523", 
    "#B4FF39", "#773A01", "#D8EEFF", "#689E3D", "#0B849B", "#FFD200", "#971C48", 
    "#4A4376", "#764A4A", "#4F2684"
]

# Team Colors Matrix [NumTeams-1][AllyTeamID]
TEAM_COLORS = [
    [ # One Team (Index 0)
        ["#004DFF"]
    ],
    [ # Two Teams (Index 1)
        [ # Team 0 (Cool)
            "#0B3EF3", "#0CE908", "#00f5e5", "#6941f2", "#8fff94", "#1b702f", "#7cc2ff", "#a294ff", 
            "#0B849B", "#689E3D", "#4F2684", "#2C32AC", "#6968A0", "#D8EEFF", "#3475FF", "#7EB900", 
            "#4A4376", "#B7EA63", "#C4A9FF", "#37713A"
        ],
        [ # Team 1 (Warm)
            "#FF1005", "#FFD200", "#FF6107", "#F80889", "#FCEEA4", "#8a2828", "#F190B3", "#C88B2F", 
            "#B04523", "#FFBB7C", "#A35274", "#773A01", "#F5A200", "#BBA28B", "#971C48", "#FF68EA", 
            "#DD783F", "#FFAAF3", "#764A4A", "#9F0D05"
        ]
    ],
    [ # Three Teams (Index 2)
        ["#004DFF", "#09F5F5", "#7CA1FF", "#2C32AC", "#D8EEFF", "#0B849B", "#3C7AFF", "#5F6492"],
        ["#FF1005", "#FF6107", "#FFD200", "#FF6058", "#FFBB7C", "#C88B2F", "#F5A200", "#9F0D05"],
        ["#0CE818", "#B4FF39", "#097E1C", "#3EFFA2", "#689E3D", "#7EB900", "#B7EA63", "#37713A"]
    ],
    [ # Four Teams
        ["#004DFF", "#7CA1FF", "#D8EEFF", "#09F5F5", "#3475FF", "#0B849B"],
        ["#FF1005", "#FF6107", "#FF6058", "#B04523", "#F80889", "#971C48"],
        ["#0CE818", "#B4FF39", "#097E1C", "#3EFFA2", "#689E3D", "#7EB900"],
        ["#FFD200", "#F5A200", "#FCEEA4", "#FFBB7C", "#BBA28B", "#C88B2F"]
    ],
    [ # Five Teams
        ["#004DFF", "#7CA1FF", "#D8EEFF", "#09F5F5", "#3475FF"],
        ["#FF1005", "#FF6107", "#FF6058", "#B04523", "#9F0D05"],
        ["#0CE818", "#B4FF39", "#097E1C", "#3EFFA2", "#689E3D"],
        ["#FFD200", "#F5A200", "#FCEEA4", "#FFBB7C", "#C88B2F"],
        ["#F80889", "#FF68EA", "#FFAAF3", "#AA0092", "#701162"]
    ],
    [ # Six Teams
        ["#004DFF", "#7CA1FF", "#D8EEFF", "#2C32AC"],
        ["#FF1005", "#FF6058", "#B04523", "#9F0D05"],
        ["#0CE818", "#B4FF39", "#097E1C", "#3EFFA2"],
        ["#FFD200", "#F5A200", "#FCEEA4", "#9B6408"],
        ["#F80889", "#FF68EA", "#FFAAF3", "#971C48"],
        ["#FF6107", "#FFBB7C", "#DD783F", "#773A01"]
    ],
    [ # Seven Teams
        ["#004DFF", "#7CA1FF", "#2C32AC"],
        ["#FF1005", "#FF6058", "#9F0D05"],
        ["#0CE818", "#B4FF39", "#097E1C"],
        ["#FFD200", "#F5A200", "#FCEEA4"],
        ["#F80889", "#FF68EA", "#FFAAF3"],
        ["#FF6107", "#FFBB7C", "#DD783F"],
        ["#09F5F5", "#0B849B", "#D8EEFF"]
    ],
    [ # Eight Teams
        ["#004DFF", "#7CA1FF", "#2C32AC"],
        ["#FF1005", "#FF6058", "#9F0D05"],
        ["#0CE818", "#B4FF39", "#097E1C"],
        ["#FFD200", "#F5A200", "#FCEEA4"],
        ["#F80889", "#FF68EA", "#971C48"],
        ["#FF6107", "#FFBB7C", "#DD783F"],
        ["#09F5F5", "#0B849B", "#D8EEFF"],
        ["#872DFA", "#6809A1", "#C4A9FF"]
    ]
]

def hex2rgb(hex_str):
    """Converts hex string to normalized RGB tuple."""
    return (
        int(hex_str[1:3], 16) / 255.0,
        int(hex_str[3:5], 16) / 255.0,
        int(hex_str[5:7], 16) / 255.0,
    )

def setupTeamColors(game: dict):
    """
    Assigns colors to players based on team configuration using DEX logic.
    """
    is_survival = False
    for ai in game.get("ai", ()):
        shortname = ai.get("shortname")
        if shortname in ["ScavengersAI", "RaptorsAI"]:
            is_survival = True

    # Count entries per AllyTeam to detect game size
    players_by_ally_team = defaultdict(lambda: 0)
    for player in game["player"]:
        if player.get("team") is None: continue
        team = game["team"][player["team"]]
        ally_team = team["allyteam"]
        players_by_ally_team[ally_team] += 1
    
    if not players_by_ally_team:
        return {}

    # Logic from DEX: Max allyTeam ID determines the index in TEAM_COLORS
    teams_size_idx = max(players_by_ally_team.keys())
    
    # Heuristic for FFA
    num_distinct_teams = len(players_by_ally_team)
    max_players_per_team = max(players_by_ally_team.values())
    
    use_ffa = (teams_size_idx >= len(TEAM_COLORS)) or \
              (num_distinct_teams >= 2 and max_players_per_team <= 1)

    color_num_by_team = defaultdict(lambda: 0)
    color_by_player = {}
    
    for team_id, team in enumerate(game["team"]):
        # Find player for this team
        # Note: Using next() with generator as in original code
        player_entry = next(
            ((pid, p) for pid, p in enumerate(game["player"]) if p.get("team", -1) == team_id), 
            (-1, None)
        )
        player_id, player = player_entry
        
        if not team or not player: continue

        ally_team_id = team["allyteam"]
        
        # Determine Palette Source
        if is_survival:
            ally_team_id = -1
            colors = SURVIVAL_COLORS
        elif use_ffa:
            ally_team_id = -1
            colors = FFA_COLORS
        else:
            # Safe access to TEAM_COLORS
            safe_idx = min(teams_size_idx, len(TEAM_COLORS) - 1)
            # If ally_team_id exceeds the sub-array (e.g. spectator weirdness), fallback
            if ally_team_id < len(TEAM_COLORS[safe_idx]):
                colors = TEAM_COLORS[safe_idx][ally_team_id]
            else:
                colors = FFA_COLORS

        # Assign color based on count within this team (or global if FFA/Survival)
        color_num = color_num_by_team[ally_team_id]
        color_num_by_team[ally_team_id] += 1
        
        color_variation = 0.0
        
        # Original logic: handle overflow if too many players for the palette
        current_colors = colors # Reference
        actual_len = len(current_colors)
        
        while color_num >= actual_len:
            color_variation += COLOR_VARIATION_DELTA / 255.0
            color_num -= actual_len

        base_hex = current_colors[color_num]
        r, g, b = hex2rgb(base_hex)
        
        # Apply variation + random noise (Original DEX feature)
        # tuple(max(0, min(c + colorVariation * random.uniform(-1, 1), 1)) for c in hex2RGB)
        
        if color_variation > 0:
             r = max(0.0, min(r + color_variation * random.uniform(-1, 1), 1.0))
             g = max(0.0, min(g + color_variation * random.uniform(-1, 1), 1.0))
             b = max(0.0, min(b + color_variation * random.uniform(-1, 1), 1.0))
             
        color_by_player[player_id] = (r, g, b)

    return color_by_player
