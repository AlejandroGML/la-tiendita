#!/usr/bin/env bash
# post-build-fix.sh — Reapplies fixes that get lost on rebuild
# Run this AFTER build-html.py every time you regenerate the study-guide.
#
# Fixes:
#   1. Disables Lenis smooth scroll (breaks position:sticky elements)
#   2. Adds contrast CSS for diagram-star SVG (text + box visibility)
#   3. Adds contrast CSS for Mermaid diagrams (text + arrow visibility)
#   4. Fixes diagram-star scroll sync offsets (sticky diagram compensation)

set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

python3 << PYEOF
import re

# --- Fix 1: Disable Lenis in main.js ---
main_js = "$DIR/assets/js/main.js"
try:
    with open(main_js) as f:
        content = f.read()
    if "new window.Lenis" in content:
        content = re.sub(
            r'function initLenis\(\) \{.*?return lenis;\s*\}',
            '''function initLenis() {
    // DISABLED: Lenis uses transform on <html> which breaks position:sticky.
    return null;
  }''',
            content,
            flags=re.DOTALL
        )
        with open(main_js, 'w') as f:
            f.write(content)
        print("Fix 1: Lenis disabled")
    else:
        print("Fix 1: already done")
except FileNotFoundError:
    print("Fix 1: main.js not found")

# --- Fix 2: Diagram-star contrast CSS ---
css = "$DIR/assets/css/components.css"
try:
    with open(css) as f:
        content = f.read()

    # Fix 2a: diagram-star text/rect contrast
    if "Ensure boxes have visible background" not in content:
        old = """.diagram-star svg {
  max-width: 100%;
  height: auto;
  display: inline-block;
}

.diagram-star svg path,
.diagram-star svg line {"""
        new = """.diagram-star svg {
  max-width: 100%;
  height: auto;
  display: inline-block;
}

/* Ensure boxes have visible background and border */
.diagram-star svg rect {
  fill: var(--bg-tertiary);
  stroke: var(--text-secondary);
  stroke-width: 1.5;
}

.diagram-star svg text {
  fill: var(--text-primary);
  font-weight: 600;
}

.diagram-star svg text[font-size="10"],
.diagram-star svg text[font-size="11"] {
  fill: var(--text-secondary);
  font-weight: 400;
}

.diagram-star svg path,
.diagram-star svg line {"""
        if old in content:
            content = content.replace(old, new)
            print("Fix 2a: diagram-star contrast added")
        else:
            print("Fix 2a: CSS block not found (skipped)")
    else:
        print("Fix 2a: already done")

    # Fix 2b: Mermaid contrast CSS
    if "Force high-contrast colors on Mermaid" not in content:
        old_mermaid = """.mermaid {
  margin: 1.5rem 0;
  text-align: center;
  background: var(--bg-secondary);
  padding: 1rem;
  border-radius: 8px;
}

.mermaid svg {
  max-width: 100%;
  height: auto;
}"""
        new_mermaid = """.mermaid {
  margin: 1.5rem 0;
  text-align: center;
  background: var(--bg-primary);
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.mermaid svg {
  max-width: 100%;
  height: auto;
}

/* Force high-contrast colors on Mermaid elements */
.mermaid text { fill: var(--text-primary) !important; color: var(--text-primary) !important; }
.mermaid .actor, .mermaid .actor-man, .mermaid .entity { fill: var(--bg-tertiary) !important; stroke: var(--text-secondary) !important; }
.mermaid .messageLine, .mermaid .loopLine { stroke: var(--text-secondary) !important; }
.mermaid .messageText { fill: var(--text-primary) !important; stroke: none !important; }
.mermaid .note { fill: var(--bg-tertiary) !important; stroke: var(--accent) !important; }
.mermaid .label, .mermaid .edgeLabel { color: var(--text-primary) !important; fill: var(--text-primary) !important; }
.mermaid .cluster rect { fill: var(--bg-secondary) !important; stroke: var(--border) !important; }
.mermaid .edgePath .path { stroke: var(--text-secondary) !important; }"""
        if old_mermaid in content:
            content = content.replace(old_mermaid, new_mermaid)
            print("Fix 2b: Mermaid contrast added")
        else:
            print("Fix 2b: Mermaid block not found (skipped)")
    else:
        print("Fix 2b: already done")

    with open(css, 'w') as f:
        f.write(content)
except FileNotFoundError:
    print("Fix 2: components.css not found")

# --- Fix 3: Diagram-star scroll sync offsets ---
diag_js = "$DIR/assets/js/diagram-star.js"
try:
    with open(diag_js) as f:
        content = f.read()
    if 'start: "top 60%"' in content:
        content = content.replace('start: "top 60%"', 'start: "top 55%"')
        content = content.replace('end: "bottom 40%"', 'end: "bottom 45%"')
        with open(diag_js, 'w') as f:
            f.write(content)
        print("Fix 3: scroll sync offsets adjusted")
    else:
        print("Fix 3: already done or pattern not found")
except FileNotFoundError:
    print("Fix 3: diagram-star.js not found")

print("\nAll fixes applied.")
PYEOF
