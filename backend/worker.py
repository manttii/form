import time
import random
import requests
from faker import Faker
import data_pool

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
    
    try:
        url = config['action']
        hidden_fields = config.get('hidden_fields', {})
        fields = config.get('fields', [])
        count = config['count']

        # Step 1: Save any custom entries to the persistent pool
        for field in fields:
            custom_vals = field.get('custom_values', '')
            if custom_vals:
                category = field.get('config', 'Random Words').replace(' ', '_').lower()
                vals_list = [v.strip() for v in custom_vals.split(',') if v.strip()]
                if vals_list:
                    data_pool.save_to_pool(category, vals_list)
        
        for i in range(count):
            if jobs[job_id]["status"] == "cancelled":
                break
                
            payload = dict(hidden_fields)
            
            for field in fields:
                fid = field['id']
                ftype = field.get('type', 'text')
                options = field.get('options', [])
                fconfig = field.get('config', 'Random Names')
                category_key = fconfig.replace(' ', '_').lower()
                
                # Handle custom entries for CURRENT run
                custom_vals = field.get('custom_values', '')
                only_custom = field.get('only_custom', False)
                if custom_vals:
                    custom_list = [v.strip() for v in custom_vals.split(',') if v.strip()]
                    if custom_list:
                        if only_custom or fconfig == 'Custom Only' or random.random() > 0.5:
                            payload[fid] = random.choice(custom_list)
                            continue

                # Smart choice based on type
                if ftype in ['single_choice', 'dropdown', 'linear_scale'] and options:
                    favored = field.get('favored_option')
                    if favored and favored in options and random.random() < 0.75:
                        payload[fid] = favored
                    else:
                        payload[fid] = random.choice(options)
                elif ftype == 'multiple_choice' and options:
                    num_picks = random.randint(1, len(options))
                    picks = random.sample(options, num_picks)
                    payload[fid] = picks
                elif ftype == 'date':
                    payload[fid] = fake.date_between(start_date='-30y', end_date='today').strftime('%Y-%m-%d')
                elif ftype == 'time':
                    payload[fid] = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
                elif ftype == 'paragraph':
                    payload[fid] = fake.paragraphs(nb=3)[0]
                else:
                    # Text field logic with Pooled Data integration
                    pool = data_pool.get_from_pool(category_key)
                    if pool and random.random() < 0.3:
                        payload[fid] = random.choice(pool)
                        continue

                    if fconfig == 'Random Names':
                        val = fake.name()
                    elif fconfig == 'Random Emails':
                        val = fake.email()
                    elif fconfig == 'Random Phone':
                        val = fake.phone_number()
                    elif fconfig == 'Random Ages':
                        val = str(random.randint(18, 65))
                    elif fconfig == 'Random Sentences':
                        val = fake.sentence()
                    elif fconfig == 'Random Words':
                        val = fake.word()
                    elif fconfig == 'Random Address':
                        val = fake.address().replace('\n', ', ')
                    elif fconfig == 'Random Company':
                        val = fake.company()
                    elif fconfig == 'Random City':
                        val = fake.city()
                    elif fconfig == 'Random Country':
                        val = fake.country()
                    elif fconfig == 'Random Job':
                        val = fake.job()
                    elif fconfig == 'Random Username':
                        val = fake.user_name()
                    elif fconfig == 'Random Number':
                        val = str(random.randint(1000, 99999))
                    else:
                        title_lower = field.get('title', '').lower()
                        if 'email' in title_lower: val = fake.email()
                        elif 'name' in title_lower: val = fake.name()
                        elif 'phone' in title_lower: val = fake.phone_number()
                        elif 'age' in title_lower: val = str(random.randint(18, 70))
                        elif 'address' in title_lower: val = fake.address().replace('\n', ', ')
                        elif 'city' in title_lower: val = fake.city()
                        elif 'job' in title_lower: val = fake.job()
                        elif 'company' in title_lower: val = fake.company()
                        else: val = fake.word()
                    payload[fid] = val

            try:
                time.sleep(random.uniform(1.0, 3.0))
                headers = {
                    "User-Agent": fake.user_agent(),
                    "Referer": url.replace("formResponse", "viewform"),
                    "Origin": "https://docs.google.com",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                session = requests.Session()
                res = session.post(url, data=payload, headers=headers, timeout=15, allow_redirects=True)
                
                success_indicators = ["recorded", "Thank you", "thanks", "submitted", "another response", "votre réponse a été enregistrée"]
                is_success = any(ind.lower() in res.text.lower() for ind in success_indicators)
                error_indicators = ["This is a required question", "must be a valid", "invalid email", "too many requests", "please wait", "try again later", "Something went wrong", "robot", "captcha"]
                has_errors = any(err.lower() in res.text.lower() for err in error_indicators)
                is_same_page = len(res.text) > 10000 and "formResponse" not in res.url

                if (res.status_code == 200 and is_success) or res.status_code in [201, 302]:
                    jobs[job_id]["success"] += 1
                else:
                    jobs[job_id]["error"] += 1
                    if len(jobs[job_id]["errors"]) < 10:
                        msg = "Validation/Rate-limit" if has_errors else ("Stuck on page" if is_same_page else f"HTTP {res.status_code}")
                        jobs[job_id]["errors"].append(msg)
            except Exception as e:
                jobs[job_id]["error"] += 1
                if len(jobs[job_id]["errors"]) < 10:
                    jobs[job_id]["errors"].append(str(e))
                    
            jobs[job_id]["progress"] = i + 1
            
        jobs[job_id]["status"] = "completed"
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["errors"].append(f"Critical Worker Crash: {str(e)}")
