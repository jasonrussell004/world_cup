import numpy as np
import pandas as pd
from pathlib import Path
from multiprocessing import Pool, cpu_count
from collections import Counter
from IPython import embed
import time

from utilities import (
    print_bracket,
    bracket_rankings,
    print_bracket_rankings,
    time_check,
    load_data,
    build_group_fixtures,
    evaluate_match,
    simulate_match,
    sort_group_with_h2h,
)

FOLDER_PATH = Path(__file__).resolve().parent
DATA_PATH = FOLDER_PATH / 'data'

SEED_BRACKET = [
    '1E', '3-1E',
    '1I', '3-1I',
    '2A', '2B',
    '1F', '2C',
    '2K', '2L',
    '1H', '2J',
    '1D', '3-1D',
    '1G', '3-1G',
    '1C', '2F',
    '2E', '2I',
    '1A', '3-1A',
    '1L', '3-1L',
    '1J', '2H',
    '2D', '2G',
    '1B', '3-1B',
    '1K', '3-1K',
]

SEED_DF = pd.read_csv(DATA_PATH / 'seeding' / 'seeding.csv')
SEED_DF = SEED_DF.filter(items=["Advancing_Groups", "1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"])
SEED_DF['Advancing_Groups'] = SEED_DF['Advancing_Groups'].str.replace(' ', '')
SEED_DF.set_index('Advancing_Groups', inplace=True)
SEED_LOOKUP = SEED_DF.to_dict('index')

def init_worker(group_data, ratings, played_dict):
    global _GROUP_DATA, _RATINGS, _PLAYED_DICT
    _GROUP_DATA, _RATINGS, _PLAYED_DICT = group_data, ratings, played_dict

def worker(seed):
    return run_single_simulation(seed, _GROUP_DATA, _RATINGS, _PLAYED_DICT)

def run_group_stage_core(group_data, ratings, played_dict, verbose=False, rng=None):
    """Executes a single processing pass of the group stage matches."""
    standings = {}
    evaluations = []
    
    for g, teams in group_data.items():
        for t in teams:
            t['points'], t['gd'], t['gf'] = 0, 0, 0
            t['wins'], t['draws'], t['losses'] = 0, 0, 0
        
        current_run_matches = {}
        
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                team_a, team_b = teams[i], teams[j]
                name_a, name_b = team_a['country'], team_b['country']
                ratings_a, ratings_b = ratings[name_a], ratings[name_b]

                # Swap team names if not in alphabetical order
                if name_a > name_b:
                    team_a, team_b = teams[j], teams[i]
                    name_a, name_b = team_a['country'], team_b['country']
                    ratings_a, ratings_b = ratings[name_a], ratings[name_b]
                
                if (name_a, name_b) in played_dict['Group']:
                    goals_a, goals_b = played_dict['Group'][(name_a, name_b)]
                else:
                    goals_a, goals_b, _, _ = simulate_match(ratings_a, ratings_b, rng=rng)
                
                if verbose:
                    match_evaluation = evaluate_match(ratings_a, ratings_b, goals_a, goals_b)
                    evaluations.append([match_evaluation["surprise_index"], f'{name_a} {goals_a} - {goals_b} {name_b}'])

                current_run_matches[(name_a, name_b)] = (goals_a, goals_b)
                current_run_matches[(name_b, name_a)] = (goals_b, goals_a)
                
                points_a = 3 if goals_a > goals_b else (1 if goals_a == goals_b else 0)
                points_b = 3 if goals_b > goals_a else (1 if goals_a == goals_b else 0)
                
                team_a['gf'] += goals_a; team_b['gf'] += goals_b
                team_a['gd'] += (goals_a - goals_b); team_b['gd'] += (goals_b - goals_a)
                team_a['points'] += points_a; team_b['points'] += points_b
                
                team_a['wins'] += 1 if points_a == 3 else 0
                team_a['draws'] += 1 if points_a == 1 else 0
                team_a['losses'] += 1 if points_a == 0 else 0
                team_b['wins'] += 1 if points_b == 3 else 0
                team_b['draws'] += 1 if points_b == 1 else 0
                team_b['losses'] += 1 if points_b == 0 else 0
        
        standings[g] = sort_group_with_h2h(teams, current_run_matches)
    
    sorted_evaluations = sorted(evaluations)
    for surprise_index, match_str in sorted_evaluations:
        print(f'{match_str}, Surprise index: {surprise_index} / 100.0\n')

    return standings

def run_knockout_stage_core(survivors, ratings, played_dict, verbose=False, rng=None):
    evaluations = []

    bracket = []
    while len(survivors) > 1:
        bracket.append([survivors[i:i + 2] for i in range(0, len(survivors), 2)])
        
        survivors = []
        for name_a, name_b in bracket[-1]:
            ratings_a, ratings_b = ratings[name_a], ratings[name_b]

            # Swap team names if not in alphabetical order
            if name_a > name_b:
                name_a, name_b = name_b, name_a
                ratings_a, ratings_b = ratings[name_a], ratings[name_b]

            if (name_a, name_b) in played_dict['Knockout']:
                goals_a, goals_b = played_dict['Knockout'][(name_a, name_b)]
            else:
                goals_a, goals_b, _, _ = simulate_match(ratings_a, ratings_b, rng=rng)
            
            while goals_a == goals_b:
                goals_a, goals_b, _, _ = simulate_match(ratings_a, ratings_b, rng=rng)
            
            if goals_a > goals_b:
                survivors.append(name_a)
            elif goals_a < goals_b:
                survivors.append(name_b)
            
            if verbose:
                match_evaluation = evaluate_match(ratings_a, ratings_b, goals_a, goals_b)
                evaluations.append([match_evaluation["surprise_index"], f'{name_a} {goals_a} - {goals_b} {name_b}'])
    
    bracket.append(survivors)
    
    sorted_evaluations = sorted(evaluations)
    for surprise_index, match_str in sorted_evaluations:
        print(f'{match_str}, Surprise index: {surprise_index} / 100.0\n')

    return bracket

def run_single_simulation(seed, group_data, ratings, played_dict, sim_knockout=True, verbose=False):
    """
    Highly optimized worker function. 
    Accepts raw pre-built dictionary data to bypass slow Pandas pickling overhead.
    """
    # Fast, modern thread-safe random number generation
    rng = np.random.default_rng(seed=seed) 
    
    standings = run_group_stage_core(group_data, ratings, played_dict, verbose=verbose, rng=rng)
    
    first = {}
    second = {}
    third = {}
    fourth = {}
    third_placed = {}
    
    for group, sorted_teams in standings.items():
        first[group] = sorted_teams[0]['country']
        second[group] = sorted_teams[1]['country']
        third[group] = sorted_teams[2]['country']
        fourth[group] = sorted_teams[3]['country']
        third_placed[group] = sorted_teams[2]
    
    # sort third place teams using appropriate tiebreaker order
    sorted_thirds = sorted(third_placed.values(), key=lambda val: (val['points'], val['gd'], val['gf']), reverse=True)
    
    advancing_thirds = sorted_thirds[:8]
    advancing_thirds_countries = [t['country'] for t in advancing_thirds]
    third_elim_points = sorted_thirds[8]['points']

    if verbose:
        print("\n" + "="*60)
        print("         FINAL GROUP STAGE STANDINGS                    ")
        print("="*60)
        for g, table_dict in standings.items():
            table_df = pd.DataFrame(table_dict)
            print(f"\nGroup {g} Standings:")
            print(table_df[['country', 'points', 'wins', 'draws', 'losses', 'gd', 'gf']].to_string(index=False))
        
        df_third_sorted = pd.DataFrame(third_placed.values()).sort_values(by=['points', 'gd', 'gf'], ascending=False).reset_index(drop=True)
        print("\n" + "="*60)
        print("             3RD PLACED TEAMS RANKING            ")
        print("="*60)
        df_third_sorted.index = df_third_sorted.index + 1
        print(df_third_sorted[['country', 'points', 'gd', 'gf']].to_string())

        print("\n" + "="*60)
        print("         QUALIFIED TEAMS FOR ROUND OF 32        ")
        print("="*60)

        print(f'Group Winners:')
        print(', '.join(f'{group}: {country}' for group, country in first.items()))

        print(f'Group Runner-ups:')
        print(', '.join(f'{group}: {country}' for group, country in second.items()))
        
        print(f'Group 3rd Place Qualifiers:')
        print(', '.join(f'{team["group"]}: {team["country"]}' for team in advancing_thirds if team["group"] in advancing_thirds_countries))

    if sim_knockout:
        advancing_third_seed_groups = sorted([t['group'] for t in advancing_thirds])
        advancing_index = "".join(advancing_third_seed_groups)
        matchups_third_seed = SEED_LOOKUP[advancing_index]

        seed_bracket = SEED_BRACKET.copy()
        for index, seed in enumerate(seed_bracket):
            if seed.startswith('3-'):
                seed_bracket[index] = matchups_third_seed[seed.removeprefix('3-')]
        
        seeding_mapping = {}
        for group, country in first.items():
            seeding_mapping[f'1{group}'] = country
        for group, country in second.items():
            seeding_mapping[f'2{group}'] = country
        for group, country in third.items():
            if group in advancing_third_seed_groups:
                seeding_mapping[f'3{group}'] = country
        
        survivors = [seeding_mapping[seed] for seed in seed_bracket]
        
        bracket = run_knockout_stage_core(survivors, ratings, played_dict, verbose=verbose, rng=rng)

        rankings = bracket_rankings(bracket)

        if verbose:
            print_bracket(bracket)
            print('')
            print_bracket_rankings(bracket)
            print('')
    
    return (
        list(first.values()),
        list(second.values()),
        list(third.values()),
        list(fourth.values()),
        advancing_thirds_countries,
        third_elim_points,
        rankings
    )

def run_monte_carlo_parallel(df, played_dict, n_simulations):
    """Distributes execution loads across all physical CPU cores using multiprocessing."""
    cores = round(cpu_count() * 0.75)
    print(f"\nInitializing parallel pool using {cores} CPU cores...")
    print(f"Running {n_simulations:,} Monte Carlo Simulations...")
    
    first_counts = {c: 0 for c in df['country']}
    second_counts = {c: 0 for c in df['country']}
    third_counts = {c: 0 for c in df['country']}
    fourth_counts = {c: 0 for c in df['country']}
    advancing_third_counts = {c: 0 for c in df['country']}
    third_elim_point_counts = Counter()
    winner_counts = {c: 0 for c in df['country']}
    finals_counts = {c: 0 for c in df['country']}
    semis_counts = {c: 0 for c in df['country']}
    quarters_counts = {c: 0 for c in df['country']}
    r16_counts = {c: 0 for c in df['country']}
    r32_counts = {c: 0 for c in df['country']}
    
    # Pre-build group data once as a plain dict/list structure
    groups = sorted(df['group'].unique())
    group_data = {g: df[df['group'] == g].drop('rating', axis=1).copy().to_dict('records') for g in groups}
    ratings = df.drop('group', axis=1).set_index('country').squeeze().to_dict()
    
    master_seed = np.random.SeedSequence()
    case_seeds = master_seed.spawn(n_simulations)

    if n_simulations > 1:
        # Process matches using Parallel Worker Pools
        with Pool(processes=cores, initializer=init_worker,
                  initargs=(group_data, ratings, played_dict)) as pool:
            results = pool.map(worker, case_seeds, chunksize=1000)
    else:
        results = [run_single_simulation(case_seeds[0], group_data, ratings, played_dict, verbose=True)]

    # Aggregate stats harvested from our concurrent workers
    for first, second, third, fourth, advancing_thirds, elim_points, rankings in results:
        third_elim_point_counts[elim_points] += 1
        for t in first:
            first_counts[t] += 1
        for t in second:
            second_counts[t] += 1
        for t in third:
            third_counts[t] += 1
        for t in fourth:
            fourth_counts[t] += 1
        for t in advancing_thirds:
            advancing_third_counts[t] += 1
        for t in rankings['Winner']:
            winner_counts[t] += 1
        for t in rankings['Finals']:
            finals_counts[t] += 1
        for t in rankings['Semis']:
            semis_counts[t] += 1
        for t in rankings['Quarters']:
            quarters_counts[t] += 1
        for t in rankings['R16']:
            r16_counts[t] += 1
        for t in rankings['R32']:
            r32_counts[t] += 1
    
    summary = []
    for _, row in df.iterrows():
        c = row['country']
        first = (first_counts[c] / n_simulations) * 100
        second = (second_counts[c] / n_simulations) * 100
        third = (third_counts[c] / n_simulations) * 100
        fourth = (fourth_counts[c] / n_simulations) * 100
        advancing_third = (advancing_third_counts[c] / n_simulations) * 100
        advance = first + second + advancing_third
        winner = (winner_counts[c] / n_simulations) * 100
        finals = (finals_counts[c] / n_simulations) * 100
        semis = (semis_counts[c] / n_simulations) * 100
        quarters = (quarters_counts[c] / n_simulations) * 100
        r16 = (r16_counts[c] / n_simulations) * 100
        r32 = (r32_counts[c] / n_simulations) * 100

        summary.append({
            'Country': c, 'Group': row['group'],
            '1st %': round(first, 2), '2nd %': round(second, 2),
            '3rd %': round(third, 2), '4th %': round(fourth, 2),
            'Advance %': round(advance, 2),
            'Win %': round(winner, 2), 'Finals %': round(finals, 2),
            'Semis %': round(semis, 2), 'Quarters %': round(quarters, 2),
            'R16 %': round(r16, 2), 'R32 %': round(r32, 2),
        })
    
    group_sort = ['Advance %', '1st %', '2nd %', '3rd %', '4th %']
    knockout_sort = ['Win %', 'Finals %', 'Semis %', 'Quarters %', 'R16 %', 'R32 %']

    # df_sort = group_sort + knockout_sort
    df_sort = knockout_sort + group_sort

    df_summary = pd.DataFrame(summary).sort_values(by=df_sort, ascending=False)
    
    print("\n" + "="*85)
    print("              MONTE CARLO PROBABILITY PROJECTIONS                            ")
    print("="*85)
    print(df_summary.to_string(index=False))
    
    print("="*85)
    print("             POST-PROCESSING: 3RD PLACE WITH 4 POINTS ANALYSIS               ")
    print("="*85)

    # Calculate and print percentages
    for points, count in sorted(third_elim_point_counts.items(), reverse=True):
        pct = (count / n_simulations) * 100
        print(f"{points} points: {pct:.2f}%")

if __name__ == "__main__":
    default_n_simulations = 100_000

    ratings_csv = DATA_PATH / 'ratings' / 'ratings_latest.csv'
    groups_csv = DATA_PATH / 'groups.csv'
    matches_csv = DATA_PATH / 'matches.csv'

    df, played_matches = load_data(ratings_csv, groups_csv, matches_csv)
    
    print("\nSelect Simulation Execution Engine:")
    print("1. Single Tournament Mode (Resolves remaining schedule once & prints complete final standings & bracket)")
    print("N. Monte Carlo Mode (Runs remaining unplayed matches N times to calculate custom projections)")
    print(f"(No input). Default Monte Carlo Mode (Runs remaining unplayed matches {default_n_simulations:,} times to calculate custom projections)")
    choice = input("Enter choice: ").strip()
    

    if choice == '':
        choice = str(default_n_simulations)
    
    if choice.isdigit() and len(choice) > 0:
        n_simulations = int(choice)

        t0 = time.time()
        run_monte_carlo_parallel(df, played_matches, n_simulations)
        time_check(t0)
    else:
        print("Invalid input. Defaulting to Single Tournament Mode...")
        run_monte_carlo_parallel(df, played_matches, 1)