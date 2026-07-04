import re
import os
import time
import itertools
import pandas as pd
import numpy as np
from IPython import embed

def visible_len(text):
    """Calculates the physical length of a string on screen, ignoring ANSI codes."""
    return len(re.sub(r'\x1b\[[0-9;]*m', '', text))

def ansi_ljust(text, width):
    """Pads a string with spaces based on its visible width, not its byte length."""
    return text + (" " * (width - visible_len(text)))

def print_bracket(bracket):
    num_rounds = len(bracket)
    
    # ANSI escape sequences for bold bright green text and styling reset
    WINNER_STYLE = "\033[1;92m"
    RESET = "\033[0m"
    
    # 1. Calculate specific slot and column widths for EVERY round independently
    col_widths = []
    slot_widths = []
    for r_idx, round_matches in enumerate(bracket):
        # Flatten round elements uniformly to read their text length
        names = []
        for m in round_matches:
            if isinstance(m, (list, tuple)):
                names.extend([str(t) for t in m if t])
            elif m:
                names.append(str(m))
                
        max_in_round = max((len(name) for name in names), default=4)
        slot_width = max_in_round + 2
        slot_widths.append(slot_width)
        
        ext_width = 4 if r_idx < num_rounds - 1 else 1
        col_widths.append(slot_width + ext_width)

    # 2. Allocate the 2D grid matrix using variable column widths
    total_rows = (2 ** num_rounds) * 2
    grid = []
    for _ in range(total_rows):
        row_cells = [" " * col_widths[r] for r in range(num_rounds)]
        grid.append(row_cells)

    # 3. Populate the grid column by column
    for r_idx, round_matches in enumerate(bracket):
        initial_space = (2 ** r_idx) - 1
        stride = 2 ** (r_idx + 1)
        slot_w = slot_widths[r_idx]
        col_w = col_widths[r_idx]
        row_pointer = initial_space
        
        for match in round_matches:
            current_matchup = match if isinstance(match, (list, tuple)) else [match]
            match_rows = []
            
            # --- PRE-PROCESS HIGHLIGHTING LOOKAHEAD ---
            styled_matchup = []
            for team in current_matchup:
                if not team:
                    continue
                is_winner = False
                if r_idx + 1 < num_rounds:
                    # Flatten next round to check if this team moved forward
                    next_round_flat = []
                    for nm in bracket[r_idx + 1]:
                        if isinstance(nm, (list, tuple)):
                            next_round_flat.extend([str(t) for t in nm if t])
                        elif nm:
                            next_round_flat.append(str(nm))
                    if str(team) in next_round_flat:
                        is_winner = True
                elif r_idx == num_rounds - 1:
                    # The absolute last single entry in the data represents the grand champion
                    is_winner = True
                
                styled_matchup.append(f"{WINNER_STYLE}{team}{RESET}" if is_winner else str(team))
            
            # --- DRAWING LOGIC ---
            if len(styled_matchup) == 1:
                winner_name = styled_matchup[0]
                grid[row_pointer][r_idx] = ansi_ljust(winner_name, col_w)
                continue
                
            for team_idx, team in enumerate(styled_matchup):
                # Measure clean visible string length when computing dash sizes
                dash_padding = "─" * (slot_w - visible_len(team) - 1)
                
                if team_idx == 0:
                    text = f"{team} {dash_padding}┐"
                else:
                    text = f"{team} {dash_padding}┘"
                
                grid[row_pointer][r_idx] = ansi_ljust(text, col_w)
                match_rows.append(row_pointer)
                row_pointer += stride
            
            # 4. Draw connectors using the specific column math
            if len(match_rows) == 2:
                start_row, end_row = match_rows
                mid_row = (start_row + end_row) // 2
                for v_row in range(start_row + 1, end_row):
                    if v_row == mid_row and r_idx < num_rounds - 1:
                        dash_count = col_w - slot_w - 2
                        grid[v_row][r_idx] = " " * slot_w + "├" + "─" * dash_count + " "
                    else:
                        grid[v_row][r_idx] = " " * slot_w + "│" + " " * (col_w - slot_w - 1)

    # 5. Output the finished grid
    for row in grid:
        if any(cell.strip() for cell in row):
            print("".join(row))

def bracket_rankings(bracket):
    rankings = {}

    # Helper to uniformly extract a flat list of strings from any round configuration
    def flatten_round(round_data):
        flat = []
        for match in round_data:
            if isinstance(match, (list, tuple)):
                flat.extend([t for t in match if t])
            elif match:
                flat.append(match)
        return flat

    # Pre-flatten all rounds for easier collection sets
    flattened_rounds = [flatten_round(r) for r in bracket]
    num_rounds = len(flattened_rounds)
    
    # Track teams we have already assigned to a rank so they don't repeat
    ranked_teams = set()

    rankings_lookup = ['R32', 'R16', 'Quarters', 'Semis', 'Finals', 'Winner']

    # Traverse backward: Winner -> Finalist -> Semifinalists -> Quarterfinalists -> etc.
    for i in range(num_rounds - 1, -1, -1):
        current_tier_teams = flattened_rounds[i]
        
        # Identify who was eliminated at this specific tier
        tier_eliminated = []
        for team in current_tier_teams:
            if team not in ranked_teams:
                tier_eliminated.append(team)
                ranked_teams.add(team)
        
        if not tier_eliminated:
            continue
        
        rankings[rankings_lookup[i]] = tier_eliminated
    
    return rankings

def print_bracket_rankings(bracket):
    rankings = bracket_rankings(bracket)
    for label, countries in rankings.items():
        print(f'{label:<8} : {", ".join(countries)}')

def time_check(t0):
    print(f'{time.time() - t0} seconds')

def load_data(ratings_path, groups_path, matches_path=''):
    """Loads datasets and converts played matches into a quick-lookup cache dictionary."""
    if not os.path.exists(ratings_path) or not os.path.exists(groups_path):
        print(f'{ratings_path = }')
        print(f'{groups_path = }')
        raise FileNotFoundError("Please ensure 'ratings_latest.csv' and 'groups.csv' are in this folder.")
    
    df_ratings = pd.read_csv(ratings_path)
    df_groups = pd.read_csv(groups_path)
    
    for df_temp in [df_ratings, df_groups]:
        df_temp.columns = df_temp.columns.str.strip()
        for col in df_temp.select_dtypes(include='object').columns:
            df_temp[col] = df_temp[col].str.strip()
            
    df = pd.merge(df_groups, df_ratings, on='country')
    
    played_dict = {'Group': {}, 'Knockout': {}}
    if os.path.exists(matches_path):
        df_matches = pd.read_csv(matches_path, on_bad_lines='skip')
        df_matches.columns = df_matches.columns.str.strip()
        for _, row in df_matches.iterrows():
            home = str(row['Home_Team']).strip()
            away = str(row['Away_Team']).strip()
            home_score = int(row['Home_Score'])
            away_score = int(row['Away_Score'])

            if home > away:
                teams = (away, home)
                score = (away_score, home_score)
            else:
                teams = (home, away)
                score =  (home_score, away_score)
            
            stage = 'Group' if row['Matchday'] <= 3 else 'Knockout'
            
            played_dict[stage][teams] = score
            
        print(f"--> Optimized lookup cache created for {len(df_matches)} pre-played matches.")
    else:
        print(f"--> '{matches_path}' not found. Simulating completely from scratch.")
        
    return df, played_dict

def build_group_fixtures(group_data, ratings, played_dict):
    """Precompute fixed lambda values for every group-stage fixture, once."""
    fixtures = []  # list of (group, name_a, name_b, lambda_a, lambda_b, is_played, played_result)
    for g, teams in group_data.items():
        names = sorted(t['country'] for t in teams)  # alphabetical country order
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                name_a, name_b = names[i], names[j]
                if (name_a, name_b) in played_dict['Group']:
                    fixtures.append((g, name_a, name_b, None, None, True))
                else:
                    la, lb = ratings_to_lambdas(ratings[name_a], ratings[name_b])
                    fixtures.append((g, name_a, name_b, la, lb, False))
    return fixtures

def ratings_to_lambdas(rating_a, rating_b, base_total_goals=2.70):
    # 1. Calculate standard win expectation percentage for Team A (0.0 to 1.0)
    # This is the gold-standard official FIFA/Elo win probability formula
    exp_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    exp_b = 1 - exp_a
    
    # 2. Allocate the 2.70 base match goals proportionally based on skill
    # We apply a slight compression dampener (0.7) so expected goals stay realistic
    lambda_a = base_total_goals * (0.5 + 0.7 * (exp_a - 0.5))
    lambda_b = base_total_goals * (0.5 + 0.7 * (exp_b - 0.5))
    
    # Ensure lambda never drops below a baseline competitive floor (e.g., 0.2 goals)
    lambda_a = max(0.2, lambda_a)
    lambda_b = max(0.2, lambda_b)

    return lambda_a, lambda_b

def evaluate_match(rating_a, rating_b, score_a, score_b, base_total_goals=2.70):
    """
    Evaluates match surprise based on Outcome Probability (Win/Draw/Loss) 
    instead of raw scoreline variance.
    """
    # 1. Determine actual outcome
    if score_a > score_b:
        actual_outcome = "W" # Team A Win
    elif score_a < score_b:
        actual_outcome = "L" # Team A Loss
    else:
        actual_outcome = "D" # Draw
        
    # 2. Calculate model expectations
    lambda_a, lambda_b = ratings_to_lambdas(rating_a, rating_b, base_total_goals=base_total_goals)
    
    # 3. Simulate the match 10,000 times to find the true outcome distribution
    sim_size = 10_000
    sim_goals_a = np.random.poisson(lambda_a, sim_size)
    sim_goals_b = np.random.poisson(lambda_b, sim_size)
    
    sim_wins = np.sum(sim_goals_a > sim_goals_b)
    sim_losses = np.sum(sim_goals_a < sim_goals_b)
    sim_draws = np.sum(sim_goals_a == sim_goals_b)
    
    # 4. Get the probability of the outcome that actually happened
    if actual_outcome == "W":
        outcome_prob = sim_wins / sim_size
    elif actual_outcome == "L":
        outcome_prob = sim_losses / sim_size
    elif actual_outcome == "D":
        outcome_prob = sim_draws / sim_size
        
    # 5. Calculate Surprise Index based on the outcome probability
    # If something has a 100% chance of happening, surprise is 0.
    # If something has a 0% chance, surprise approaches 100.
    surprise_index = (1.0 - outcome_prob) * 100
    
    return {
        "expected_goals_a": round(lambda_a, 2),
        "expected_goals_b": round(lambda_b, 2),
        "actual_outcome": actual_outcome,
        "outcome_probability": round(outcome_prob * 100, 2),
        "surprise_index": round(surprise_index, 1)
    }

def simulate_match(rating_a, rating_b, base_total_goals=2.70, rng=None):
    """
    Simulates a match using a Linear Skill Margin to eliminate extreme blowouts
    while maintaining accurate real-world win/draw/loss probabilities.
    """
    lambda_a, lambda_b = ratings_to_lambdas(rating_a, rating_b, base_total_goals=base_total_goals)
    
    # Generate individual goal outputs
    if rng is None:
        goals_a = np.random.poisson(lambda_a)
        goals_b = np.random.poisson(lambda_b)
    else:
        goals_a = rng.poisson(lambda_a)
        goals_b = rng.poisson(lambda_b)
    
    if goals_a > goals_b:
        return goals_a, goals_b, 3, 0
    elif goals_a < goals_b:
        return goals_a, goals_b, 0, 3
    else:
        return goals_a, goals_b, 1, 1

def sort_group_with_h2h(teams, match_results):
    """
    Sorts group teams applying Head-to-Head criteria for tied teams.
    Tie-breaker order: Points -> Head-to-Head -> GD -> GF -> 
    """
    # Step 1: Initial broad sort based on primary criteria
    teams.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
    
    # Step 2: Look for consecutive subsets of teams that are completely tied
    i = 0
    while i < len(teams) - 1:
        j = i + 1
        while j < len(teams) and teams[i]['points'] == teams[j]['points']:
            j += 1
            
        # If j > i + 1, we found a cluster of tied teams from index i to j-1
        if j - i > 1:
            tied_cluster = teams[i:j]
            tied_names = [t['country'] for t in tied_cluster]
            
            h2h_points = {name: 0 for name in tied_names}
            h2h_gd = {name: 0 for name in tied_names}
            h2h_gf = {name: 0 for name in tied_names}
            
            # Extract match results exclusively involving the tied teams
            for name_a, name_b in itertools.combinations(tied_names, 2):
                if (name_a, name_b) in match_results:
                    goals_a, goals_b = match_results[(name_a, name_b)]
                    
                    h2h_gf[name_a] += goals_a
                    h2h_gf[name_b] += goals_b
                    h2h_gd[name_a] += (goals_a - goals_b)
                    h2h_gd[name_b] += (goals_b - goals_a)
                    
                    if goals_a > goals_b:
                        h2h_points[name_a] += 3
                    elif goals_a < goals_b:
                        h2h_points[name_b] += 3
                    else:
                        h2h_points[name_a] += 1
                        h2h_points[name_b] += 1
            
            # Re-sort using isolated head-to-head metrics, fallback to absolute Elo rating
            tied_cluster.sort(
                key=lambda x: (
                    h2h_points[x['country']], 
                    h2h_gd[x['country']], 
                    h2h_gf[x['country']]
                ), 
                reverse=True
            )
            
            # Splice back into the array
            teams[i:j] = tied_cluster
            
        i = j 

    return teams

# def run_single_simulation_old(df, played_dict):
    # """Runs a single iteration of the tournament and details full tables & qualifiers."""
    # # Pre-build group data once as a plain dict/list structure
    # groups = sorted(df['group'].unique())
    # group_data = {g: df[df['group'] == g].drop('rating', axis=1).copy().to_dict('records') for g in groups}
    # ratings = df.drop('group', axis=1).set_index('country').squeeze().to_dict()
    
    # standings = run_group_stage_core(group_data, ratings, played_dict, verbose=True)
    
    # print("\n" + "="*60)
    # print("         FINAL GROUP STAGE STANDINGS                    ")
    # print("="*60)
    
    # first, second, third_placed = [], [], []
    # for g, table_dict in standings.items():
    #     table_df = pd.DataFrame(table_dict)
    #     print(f"\nGroup {g} Standings:")
    #     print(table_df[['country', 'points', 'wins', 'draws', 'losses', 'gd', 'gf']].to_string(index=False))
        
    #     first.append(table_dict[0])
    #     second.append(table_dict[1])
    #     third_placed.append(table_dict[2])
        
    # df_third_sorted = pd.DataFrame(third_placed).sort_values(by=['points', 'gd', 'gf'], ascending=False).reset_index(drop=True)
    
    # print("\n" + "="*60)
    # print("             3RD PLACED TEAMS RANKING            ")
    # print("="*60)
    # df_third_sorted.index = df_third_sorted.index + 1
    # print(df_third_sorted[['country', 'points', 'gd', 'gf']].to_string())
    
    # print("\n" + "="*60)
    # print("         QUALIFIED TEAMS FOR ROUND OF 32        ")
    # print("="*60)
    # first_df = pd.DataFrame(first)
    # first_df['seed'] = '1' + first_df['group']
    # second_df = pd.DataFrame(second)
    # second_df['seed'] = '2' + second_df['group']
    # third_df = df_third_sorted.head(8).copy()
    # third_df['seed'] = '3' + third_df['group']
    # qualified = pd.concat([first_df, second_df, third_df], ignore_index=True)
    # for g in groups:
    #     print(f'Group {g}:')
    #     print(*qualified['country'][qualified['group'] == g], sep=', ')
    #     print('')
    # seeding_mapping = qualified[['seed', 'country']].set_index('seed').squeeze()

    # advancing_3rd_seed_groups = sorted(df_third_sorted['group'].iloc[:8])
    # advancing_index = "".join(advancing_3rd_seed_groups)
    # matchups_third_seed = SEED_LOOKUP[advancing_index]

    # seed_bracket = SEED_BRACKET.copy()
    # for index, seed in enumerate(seed_bracket):
    #     if seed.startswith('3-'):
    #         seed_bracket[index] = matchups_third_seed[seed.removeprefix('3-')]
    
    # survivors = [seeding_mapping[seed] for seed in seed_bracket]
    
    # bracket = run_knockout_stage_core(survivors, ratings, played_dict, verbose=True)
    
    # print_bracket(bracket)
    # print('')
    # print_bracket_rankings(bracket)
    # print('')