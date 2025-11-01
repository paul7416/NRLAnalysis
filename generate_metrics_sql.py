import json

def print_sql(value):
    print(f'CREATE TABLE IF NOT EXISTS "{value}"(')
    print("    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,")
    print("    player_performance_id INTEGER NOT NULL,")
    print("    count INTEGER NOT NULL,")
    print("    FOREIGN KEY(player_performance_id) REFERENCES player_performances(id));")
    print()


with open("glossary.json", "r") as f:
    metrics = json.load(f)
for key, value in metrics.items():
    print_sql(str.lower(value))
    metrics[key] = str.lower(value)

with open("glossary.json", "w") as f:
    json.dump(metrics,f, indent=2)

