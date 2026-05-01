import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_form(url: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {"error": str(e)}

    soup = BeautifulSoup(response.text, 'html.parser')
    
    form_data = {
        "url": url,
        "action": "",
        "hidden_fields": {},
        "fields": []
    }
    
    form_tag = soup.find('form')
    if form_tag and form_tag.has_attr('action'):
        action = form_tag["action"]
        if not action.startswith("http"):
            # Handle relative URLs
            from urllib.parse import urljoin
            action = urljoin(url, action)
        form_data["action"] = action
    else:
        # Fallback for standard Google Forms URL structure
        if "viewform" in url:
            form_data["action"] = url.replace("viewform", "formResponse")
        else:
            base_url = url.split("?")[0].rstrip("/")
            form_data["action"] = f"{base_url}/formResponse"

    # Extract all hidden fields from the form
    for inp in soup.find_all('input', {'type': 'hidden'}):
        name = inp.get('name')
        if name:
            form_data["hidden_fields"][name] = inp.get('value', '')

    script_text = None
    for script in soup.find_all('script'):
        if script.string and 'var FB_PUBLIC_LOAD_DATA_ =' in script.string:
            script_text = script.string
            break
            
    fields_map = {}
    if script_text:
        # Use a more greedy match for the array to handle nested brackets correctly
        match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.*\]);', script_text, re.DOTALL)
        if match:
            try:
                json_str = match.group(1)
                # Sometimes there's extra stuff after the last bracket, let's try to be precise
                # but for most Google Forms, the regex above is sufficient.
                data = json.loads(json_str)
                
                if len(data) > 1 and len(data[1]) > 1 and isinstance(data[1][1], list):
                    for item in data[1][1]:
                        if len(item) < 4 or item[3] is None: continue
                        
                        field_type_id = item[3]
                        title = item[1] or "Untitled Field"
                        
                        # Type mapping
                        type_name = "text"
                        if field_type_id == 1: type_name = "paragraph"
                        elif field_type_id == 2: type_name = "single_choice"
                        elif field_type_id == 3: type_name = "dropdown"
                        elif field_type_id == 4: type_name = "multiple_choice"
                        elif field_type_id == 5: type_name = "linear_scale"
                        elif field_type_id == 9: type_name = "date"
                        elif field_type_id == 10: type_name = "time"
                        
                        if len(item) > 4 and isinstance(item[4], list):
                            for sub in item[4]:
                                if not isinstance(sub, list) or len(sub) < 1: continue
                                
                                entry_id = f"entry.{sub[0]}"
                                is_required = bool(sub[2]) if len(sub) > 2 else False
                                
                                options = []
                                if len(sub) > 1 and isinstance(sub[1], list):
                                    for opt in sub[1]:
                                        if isinstance(opt, list) and len(opt) > 0:
                                            options.append(str(opt[0]))
                                
                                fields_map[entry_id] = {
                                    "id": entry_id,
                                    "title": title,
                                    "type": type_name,
                                    "options": options,
                                    "required": is_required
                                }
            except Exception as e:
                pass
                
    # Fallback to HTML parsing
    if not fields_map:
        inputs = soup.find_all(['input', 'textarea', 'select'])
        for inp in inputs:
            name = inp.get('name')
            if name and name.startswith('entry.'):
                if name not in fields_map:
                    # Try to find a label by looking at parent divs
                    parent = inp.find_parent('div')
                    title = name
                    if parent:
                        # Look for text nodes in the parent that aren't empty
                        text_nodes = parent.find_all(string=True)
                        for node in text_nodes:
                            txt = node.strip()
                            if txt and len(txt) > 2:
                                title = txt
                                break
                    
                    fields_map[name] = {
                        "id": name, 
                        "title": title, 
                        "type": "text", 
                        "options": [],
                        "required": False
                    }
                
                inp_type = inp.get('type', '')
                if inp_type == 'radio':
                    fields_map[name]["type"] = "single_choice"
                elif inp_type == 'checkbox':
                    fields_map[name]["type"] = "multiple_choice"
                
                val = inp.get('value')
                if val and val != '__other_option__' and val not in fields_map[name]["options"]:
                    fields_map[name]["options"].append(val)
                            
    form_data["fields"] = list(fields_map.values())
    return form_data
