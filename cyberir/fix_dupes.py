import re

# Fix log_incident.html - remove duplicate data sensitivity blocks
for filepath in [
    r"c:\Users\PDM\Pictures\CYBER\cyberir\frontend\templates\log_incident.html",
    r"c:\Users\PDM\Pictures\CYBER\cyberir\frontend\templates\edit_incident.html",
]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"SKIP: {filepath}")
        continue

    # The duplicated block pattern - find all occurrences
    block_pattern = r"""                <div class="full-width" style="margin-top: 15px;">
                    <div style="font-size: 1rem; font-weight: 600; color: var\(--text-dark\); margin-bottom: 10px; border-bottom: 1px solid var\(--border-color\); padding-bottom: 5px;">
                        4\. Sensitivity of Affected Data/Information
                    </div>
                    <div class="form-grid">
                        <div>
                            <label class="form-label" for="data_sensitivity_selections">Type of Sensitive Data Affected</label>
                            <select name="data_sensitivity_selections" id="data_sensitivity_selections" multiple size="5" class="multi-select-field">.*?</select>
                            <div class="multi-select-hint">.*?</div>
                            <div id="data_sensitivity_other_container".*?</div>
                        </div>
                        <div class="full-width">
                            <label class="form-label" for="data_sensitivity_additional">.*?</label>
                            <textarea.*?</textarea>
                        </div>
                    </div>
                </div>"""

    # Simpler approach: find all occurrences of the sensitivity block and track positions
    marker = '4. Sensitivity of Affected Data/Information'
    positions = []
    start = 0
    while True:
        idx = content.find(marker, start)
        if idx == -1:
            break
        positions.append(idx)
        start = idx + 1

    print(f"{filepath}: Found {len(positions)} occurrences of sensitivity block")

    if len(positions) <= 1:
        print("  Already clean, skipping")
        continue

    # Find which one is inside the Affected Resources card
    # The Affected Resources card contains "Affected Resources" in its header
    affected_resources_pos = content.find('Affected Resources')
    if affected_resources_pos == -1:
        print("  WARNING: Could not find 'Affected Resources' in file")
        continue

    # Find the next occurrence of the sensitivity block AFTER the Affected Resources header
    correct_idx = None
    for pos in positions:
        if pos > affected_resources_pos:
            correct_idx = pos
            break

    if correct_idx is None:
        print("  WARNING: No sensitivity block found after Affected Resources")
        continue

    print(f"  Affected Resources at char {affected_resources_pos}")
    print(f"  Correct sensitivity block at char {correct_idx}")
    print(f"  Removing blocks at: {[p for p in positions if p != correct_idx]}")

    # Remove all blocks EXCEPT the correct one
    # We need to find the full extent of each block
    # Each block starts with `<div class="full-width" style="margin-top: 15px;">` 
    # just before the marker, and ends with the closing `</div>\n                </div>`

    # Work backwards to avoid offset issues
    blocks_to_remove = [p for p in positions if p != correct_idx]
    blocks_to_remove.sort(reverse=True)

    for block_pos in blocks_to_remove:
        # Find the start: look backwards for the containing div
        search_start = content.rfind('<div class="full-width" style="margin-top: 15px;">', 0, block_pos)
        if search_start == -1:
            print(f"  WARNING: Could not find start of block at {block_pos}")
            continue

        # Find the end: after the block there should be closing divs
        # The pattern is: </textarea>\n                        </div>\n                    </div>\n                </div>
        # Look for the 3rd </div> after the textarea closing
        textarea_end = content.find('</textarea>', block_pos)
        if textarea_end == -1:
            continue

        # Count closing divs after textarea
        end_pos = textarea_end
        divs_to_close = 4  # </div> for textarea wrapper, form-grid, form-grid inner, full-width outer
        for _ in range(divs_to_close):
            next_div = content.find('</div>', end_pos + 1)
            if next_div == -1:
                break
            end_pos = next_div

        end_pos += len('</div>')

        # Also consume trailing whitespace/newline
        while end_pos < len(content) and content[end_pos] in '\r\n':
            end_pos += 1

        print(f"  Removing chars {search_start} to {end_pos}")
        content = content[:search_start] + content[end_pos:]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Verify
    count = content.count(marker)
    print(f"  After cleanup: {count} occurrence(s) remain")

print("Done")
