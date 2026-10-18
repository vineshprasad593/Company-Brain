import glob, os, sqlite3
import pandas as pd

conn = sqlite3.connect("company.db")
for path in sorted(glob.glob("documents/*.csv")):
    table = os.path.splitext(os.path.basename(path))[0]
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    for c in df.select_dtypes("object").columns:
        df[c] = df[c].str.strip()
    df.to_sql(table, conn, if_exists="replace", index=False)
    print(f"{table}: {len(df)} rows")
conn.close()