#%%
import json
from pathlib import Path

body = json.loads(Path("body.json").read_text())

print(len(body["machines"]))

print(len({machine["eti"] for machine in body["machines"]}))
# %%
