# world_cup

A simulator for the FIFA World Cup based on team ratings from [Elo Ratings](https://eloratings.net).

---

## Example Output

Below is an example output for a **100,000 case Monte Carlo (MC) simulation** starting in the Round of 16.

```text
--> Optimized lookup cache created for 88 pre-played matches.

Select Simulation Execution Engine:
1. Single Tournament Mode (Resolves remaining schedule once & prints complete final standings & bracket)
N. Monte Carlo Mode (Runs remaining unplayed matches N times to calculate custom projections)
(No input). Default Monte Carlo Mode (Runs remaining unplayed matches 100,000 times to calculate custom projections)
Enter choice: 

Initializing parallel pool using 12 CPU cores...
Running 100,000 Monte Carlo Simulations...

=====================================================================================
              MONTE CARLO PROBABILITY PROJECTIONS                                 
=====================================================================================
               Country Group  1st %  2nd %  3rd %  4th %  Advance %  Win %  Finals %  Semis %  Quarters %  R16 %  R32 %
             Argentina     J  100.0    0.0    0.0    0.0      100.0  26.59     20.68    19.49       22.77  10.46    0.0
                France     I  100.0    0.0    0.0    0.0      100.0  24.38     16.90    30.74       13.83  14.15    0.0
                 Spain     H  100.0    0.0    0.0    0.0      100.0  23.70     14.45    22.31       11.47  28.07    0.0
               England     L  100.0    0.0    0.0    0.0      100.0   6.62      9.68    22.16       27.90  33.65    0.0
                Brazil     C  100.0    0.0    0.0    0.0      100.0   5.49      8.68    20.72       30.74  34.37    0.0
              Colombia     K  100.0    0.0    0.0    0.0      100.0   3.60      6.63    10.42       40.27  39.10    0.0
              Portugal     K    0.0  100.0    0.0    0.0      100.0   3.55      5.07    11.29        8.16  71.93    0.0
               Belgium     G  100.0    0.0    0.0    0.0      100.0   1.27      3.36    10.35       52.71  32.31    0.0
           Switzerland     B  100.0    0.0    0.0    0.0      100.0   1.18      2.85     6.58       28.50  60.90    0.0
                Mexico     A  100.0    0.0    0.0    0.0      100.0   1.08      2.97     9.69       19.91  66.35    0.0
                Norway     I    0.0  100.0    0.0    0.0      100.0   1.00      2.64     9.28       21.46  65.63    0.0
               Morocco     C    0.0  100.0    0.0    0.0      100.0   0.96      3.29    12.39       52.46  30.90    0.0
              Paraguay     D    0.0    0.0  100.0    0.0      100.0   0.25      1.06     5.21        7.63  85.85    0.0
         United States     D  100.0    0.0    0.0    0.0      100.0   0.17      0.82     3.66       27.66  67.69    0.0
                Canada     B    0.0  100.0    0.0    0.0      100.0   0.12      0.64     4.05       26.08  69.10    0.0
                 Egypt     G    0.0  100.0    0.0    0.0      100.0   0.04      0.28     1.67        8.46  89.54    0.0
               Germany     E  100.0    0.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
           Netherlands     F  100.0    0.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
          South Africa     A    0.0  100.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
             Australia     D    0.0  100.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
           Ivory Coast     E    0.0  100.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
                 Japan     F    0.0  100.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
            Cabo Verde     H    0.0  100.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
               Austria     J    0.0  100.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
               Croatia     L    0.0  100.0    0.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
Bosnia and Herzegovina     B    0.0    0.0  100.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
               Ecuador     E    0.0    0.0  100.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
                Sweden     F    0.0    0.0  100.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
               Senegal     I    0.0    0.0  100.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
               Algeria     J    0.0    0.0  100.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
              DR Congo     K    0.0    0.0  100.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
                 Ghana     L    0.0    0.0  100.0    0.0      100.0   0.00      0.00     0.00        0.00   0.00  100.0
           South Korea     A    0.0    0.0  100.0    0.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
              Scotland     C    0.0    0.0  100.0    0.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
                  Iran     G    0.0    0.0  100.0    0.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
               Uruguay     H    0.0    0.0  100.0    0.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
               Czechia     A    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
                 Qatar     B    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
                 Haiti     C    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
                Turkey     D    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
               Curacao     E    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
               Tunisia     F    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
           New Zealand     G    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
          Saudi Arabia     H    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
                  Iraq     I    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
                Jordan     J    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
            Uzbekistan     K    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
                Panama     L    0.0    0.0    0.0  100.0        0.0   0.00      0.00     0.00        0.00   0.00    0.0
=====================================================================================
              POST-PROCESSING: 3RD PLACE WITH 4 POINTS ANALYSIS               
=====================================================================================
3 points: 100.00%