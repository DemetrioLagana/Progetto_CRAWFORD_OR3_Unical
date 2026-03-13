import pandas as pd
import instancegenerator as ig
import matheuristic as mh
import mathmodel as mm

nodes_df = pd.read_csv("crawford/data/ZONE.csv")
density_df = pd.read_csv("crawford/data/population_density.csv")

generator = ig.InstanceGenerator(nodes_df, density_df)
instance = generator.load_commodities('crawford/data/DMNDP-K10-0.csv')
#instance = generator.generate(scenario='non-critical')    # 'non-critical' or 'critical'

# Optionally, print a summary
#generator.summary()

# Build and solve the model
model = mm.MathematicalModel(instance, nodes_df)
result = model.solve(model_type='binary')  # 'binary' or 'relaxed'
if result is not None:
    model.solution_summary2()
    #model.visualize_solution()
else:
    print("No solution found.")                        

# BUild and solve the matheuristic
mth = mh.MathEuristic(instance, K_paths=5, nodes_df=nodes_df, density_df=density_df)
model = mth.solve()
#mh.visualize_solution(nodes_df, mth.P, mth.x , mth.F_p)