import glob
import pandas as pd

for path in sorted(glob.glob("documents/*.csv")):
    df = pd.read_csv(path)
    print("\n==", path)
    print("rows:", len(df))
    print("columns:", list(df.columns))
    