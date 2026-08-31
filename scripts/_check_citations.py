"""Check citation keys in main.tex against references.bib."""
import re

t = open("paper/main.tex", encoding="utf-8").read()
pattern = r"\\cite\{([^}]+)\}"
keys = re.findall(pattern, t)
all_keys = set()
for k in keys:
    for kk in k.split(","):
        all_keys.add(kk.strip())
print(f"Unique citation keys used: {len(all_keys)}")
for k in sorted(all_keys):
    print(f"  {k}")

bib = open("paper/references.bib", encoding="utf-8").read()
bib_keys = re.findall(r"@\w+\{(\w+),", bib)
print(f"BibTeX entries: {len(bib_keys)}")
unused = set(bib_keys) - all_keys
if unused:
    print(f"Unused entries: {unused}")
missing_from_bib = all_keys - set(bib_keys)
if missing_from_bib:
    print(f"Missing from .bib: {missing_from_bib}")
else:
    print("All cited keys exist in references.bib")
