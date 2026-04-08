import re

with open("app.py", "r") as f:
    lines = f.readlines()

routes_to_wrap = ['dashboard', 'incidents', 'correlation', 'similarity', 'reports', 'alerts', 'settings_page']

out = []
in_route = False
route_name = ""
route_indent = ""
def_indent = ""
current_route_lines = []

def process_route_lines(rn, d_ind, r_lines):
    new_lines = []
    # find the first non-docstring, non-decorator line of the function body
    body_start_idx = 0
    for i, l in enumerate(r_lines):
        if l.strip() != "":
            body_start_idx = i
            break
            
    header = r_lines[:body_start_idx]
    body = r_lines[body_start_idx:]
    
    new_lines.extend(header)
    
    # insert try block
    body_ind = d_ind + "    "
    new_lines.append(body_ind + "try:\n")
    
    for l in body:
        if l == "\n":
            new_lines.append(l)
        else:
            new_lines.append("    " + l)
            
    # insert except block
    new_lines.append(body_ind + "except Exception as e:\n")
    new_lines.append(body_ind + "    app.logger.error(f'Error in " + rn + ": {str(e)}')\n")
    new_lines.append(body_ind + "    if request.is_json:\n")
    new_lines.append(body_ind + "        return jsonify({'success': False, 'message': 'An error occurred'}), 500\n")
    new_lines.append(body_ind + "    flash('An error occurred. Please try again.', 'error')\n")
    new_lines.append(body_ind + "    return redirect(url_for('dashboard'))\n")
    
    return new_lines

i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith('@app.route('):
        
        # Check the def line below
        j = i + 1
        while j < len(lines) and lines[j].strip().startswith('@'):
            j += 1
            
        def_line = lines[j]
        m = re.match(r'^(\s*)def\s+([a-zA-Z0-9_]+)\(', def_line)
        if m:
            func_name = m.group(2)
            if func_name in routes_to_wrap:
                # capture until next def without indent or bottom
                k = j + 1
                while k < len(lines):
                    if lines[k].startswith('@app.') or (re.match(r'^[a-zA-Z]', lines[k]) and not lines[k].startswith(' ')):
                        break
                    k += 1
                
                # We have the chunk from i to k
                header_lines = lines[i:j+1]
                body_lines = lines[j+1:k]
                
                out.extend(header_lines)
                
                d_ind = m.group(1)
                
                out.extend(process_route_lines(func_name, d_ind, body_lines))
                i = k
                continue

    out.append(line)
    i += 1

with open("app.py", "w") as f:
    f.writelines(out)

print("Done")
