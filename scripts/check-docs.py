"""Check local documentation links, fences, and product spelling without network I/O."""
from pathlib import Path
import re
from urllib.parse import unquote

errors = []
for path in [Path("README.md"), *Path("docs").rglob("*.md")]:
    body = path.read_text()
    if re.search(r"CloudDesk|Clouddesk|CLOUDDESK", body):
        errors.append(f"{path}: incorrect product spelling")
    if len(re.findall(r"^```", body, re.M)) % 2:
        errors.append(f"{path}: unbalanced code fences")
    for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", body):
        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:|#", link):
            continue
        target = path.parent / unquote(link.split("#", 1)[0])
        if not target.exists():
            errors.append(f"{path}: missing link {link}")
if errors:
    raise SystemExit("\n".join(errors))
print("Documentation links, fences, and naming: PASS")
