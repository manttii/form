import time
import random
import requests
from faker import Faker

fake = Faker()
jobs = {}

def get_job_state(job_id: str):
    return jobs.get(job_id)

def start_job(job_id: str, config: dict):
    jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "total": config['count'],
        "success": 0,
        "error": 0,
        "errors": []
    }
    
    url = config['action']
    hidden_fields = config.get('hidden_fields', {})
    fields = config.get('fields', [])
    count = config['count']
    
    for i in range(count):
        if jobs[job_id]["status"] == "cancelled":
            break
            
        payload = dict(hidden_fields)
        
        for field in fields:
            fid = field['id']
            ftype = field.get('type', 'text')
            options = field.get('options', [])
            fconfig = field.get('config', 'Random Names') # Default fallback or if provided by UI
            
            # Smart choice based on type
            if ftype in ['single_choice', 'dropdown', 'linear_scale'] and options:
                payload[fid] = random.choice(options)
            elif ftype == 'multiple_choice' and options:
                num_picks = random.randint(1, len(options))
                picks = random.sample(options, num_picks)
                # requests handles list values by sending multiple parameters with the same name
                payload[fid] = picks
            elif ftype == 'date':
                # Google Forms usually expects YYYY-MM-DD for date fields
                payload[fid] = fake.date_between(start_date='-30y', end_date='today').strftime('%Y-%m-%d')
            elif ftype == 'time':
                # Google Forms usually expects HH:MM
                payload[fid] = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
            elif ftype == 'paragraph':
                payload[fid] = fake.paragraphs(nb=3)[0] # Just one long-ish paragraph
            else:
                # Text field logic
                if fconfig == 'Random Names':
                    val = fake.name()
                elif fconfig == 'Random Ages':
                    val = str(random.randint(18, 65))
                elif fconfig == 'Random Emails':
                    val = fake.email()
                elif fconfig == 'Random Sentences':
                    val = fake.sentence()
                elif fconfig == 'Random Words':
                    val = fake.word()
                elif fconfig == 'Random Phone':
                    val = fake.phone_number()
                elif fconfig == 'Random Address':
                    val = fake.address().replace('\n', ', ')
                elif fconfig == 'Random Company':
                    val = fake.company()
                else:
                    # Try to guess based on title if config is default
                    title_lower = field.get('title', '').lower()
                    if 'email' in title_lower: val = fake.email()
                    elif 'name' in title_lower: val = fake.name()
                    elif 'phone' in title_lower: val = fake.phone_number()
                    elif 'age' in title_lower: val = str(random.randint(18, 70))
                    elif 'address' in title_lower: val = fake.address().replace('\n', ', ')
                    else: val = fake.word()
                payload[fid] = val

        try:
            # Random delay to simulate human typing/interaction
            time.sleep(random.uniform(1.5, 4.0))
            
            headers = {
                "User-Agent": fake.user_agent(),
                "Referer": url.replace("formResponse", "viewform"),
                "Origin": "https://docs.google.com",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "max-age=0",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            # Use a session for better consistency
            session = requests.Session()
            res = session.post(url, data=payload, headers=headers, timeout=15, allow_redirects=True)
            
            # Google Forms returns 200 even on some validation errors, 
            # but usually it's a redirect to a thank you page.
            if res.status_code == 200:
                # Check if the response body contains "Your response has been recorded"
                if "Your response has been recorded" in res.text or "has been recorded" in res.text:
                    jobs[job_id]["success"] += 1
                else:
                    # Might be a validation error or multi-page form
                    jobs[job_id]["error"] += 1
                    if len(jobs[job_id]["errors"]) < 10:
                        jobs[job_id]["errors"].append("Possible validation error or incomplete form")
            elif res.status_code in [201, 302]:
                jobs[job_id]["success"] += 1
            else:
                jobs[job_id]["error"] += 1
                if len(jobs[job_id]["errors"]) < 10:
                    jobs[job_id]["errors"].append(f"HTTP {res.status_code}")
        except Exception as e:
            jobs[job_id]["error"] += 1
            if len(jobs[job_id]["errors"]) < 10:
                jobs[job_id]["errors"].append(str(e))
                
        jobs[job_id]["progress"] = i + 1
        
    jobs[job_id]["status"] = "completed"
