import requests
import re
import random
import string
import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

# ---------------------------------------------------------------------------
# Numerical Data Generators
# ---------------------------------------------------------------------------

# Weighted age distribution: (min_age, max_age, weight)
AGE_DISTRIBUTION = [
    (18, 24, 0.12),
    (25, 34, 0.22),
    (35, 44, 0.22),
    (45, 54, 0.20),
    (55, 64, 0.15),
    (65, 80, 0.09),
]

def generate_age():
    """Pick an age from a realistic population-weighted distribution."""
    rand = random.random()
    cumulative = 0.0
    for min_age, max_age, weight in AGE_DISTRIBUTION:
        cumulative += weight
        if rand <= cumulative:
            return random.randint(min_age, max_age)
    return random.randint(18, 80)  # fallback

def generate_birthday(age):
    """Generate a realistic birthday consistent with the given age."""
    today = datetime.date.today()
    birth_year = today.year - age
    birth_month = random.randint(1, 12)
    max_day = 28 if birth_month == 2 else (30 if birth_month in [4, 6, 9, 11] else 31)
    birth_day = random.randint(1, max_day)
    birth_date = datetime.date(birth_year, birth_month, birth_day)
    # If birthday hasn't occurred yet this year, they're still the previous age
    if birth_date > today:
        birth_date = birth_date.replace(year=birth_year - 1)
    return birth_date.strftime("%Y-%m-%d")

def generate_ssn():
    """Generate a fake SSN in XXX-XX-XXXX format."""
    area = random.randint(100, 899)
    group = random.randint(10, 99)
    serial = random.randint(1000, 9999)
    return f"{area:03d}-{group:02d}-{serial:04d}"

def generate_phone():
    """Generate a realistic US phone number."""
    area = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"({area}) {prefix}-{line}"

def generate_gender():
    return random.choice(["Male", "Female"])

def generate_mutation_id():
    """Generates a random string to force the AI to deviate from previous patterns."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ---------------------------------------------------------------------------
# Prompt Builders
# ---------------------------------------------------------------------------

SHARED_CONSTRAINTS = """
<task_constraints>
1. Output EXACTLY 9 lines.
2. Format: KEY: Value (e.g., NAME: John Doe).
3. NO MARKDOWN: Do not use brackets [], parentheses (), or asterisks **.
4. EMAIL: Provide a plain text email address only. No links.
5. EMOJI: Provide ONLY the emoji character on the same line as the key.
6. Ensure the industry reflects real-world variety.
</task_constraints>

<output_format>
NAME: [A common, realistic first and last name only]
EMOJI: [One Emoji for their industry]
JOB: [Company name]
POSITION: [Job Title]
BIO: [One unique sentence bio]
INTERESTS: [3-4 comma separated hobbies or interests]
EDUCATION: [University and Degree]
EMAIL: [ONE Mock Email]
ADDRESS: [Street, City, State, Zip]
</output_format>"""

def build_random_prompt(gender, age, mutation_seed, user_context=None):
    context_str = f"CONTEXT TO INCORPORATE: {user_context}" if user_context else ""
    system = f"""<system_instructions>
    <persona>
    You are a Random Identity Generation Engine. Your goal is to create a grounded, realistic individual.
    </persona>
    {SHARED_CONSTRAINTS}
</system_instructions>"""

    user = f"""
Gender: {gender}
Age: {age}
Simulation Seed: {mutation_seed}
Context: {context_str}
Instruction: Generate a unique, realistic individual with no parents to base them on.
If context is provided, wrap their job, bio, and interests around it.
    """
    return system, user

def build_merge_prompt(p1, p2, gender, age, mutation_seed, user_context=None):
    context_str = f"EXTRA CONTEXT: {user_context}" if user_context else ""
    p1_age = p1.get('personal_info', {}).get('age', 'Unknown')
    p2_age = p2.get('personal_info', {}).get('age', 'Unknown')

    system = f"""<system_instructions>
<persona>
You are a Random Identity Generation Engine. Your goal is to create a grounded, UNIQUE merged identity
whose traits are a plausible blend of two parents. The offspring MUST feel distinct from both parents.
</persona>
{SHARED_CONSTRAINTS}
</system_instructions>"""

    user = f"""
Parent A: {p1['name']}, {p1['position']} (Age: {p1_age})
Parent B: {p2['name']}, {p2['position']} (Age: {p2_age})
Gender: {gender}
Age: {age}
Simulation Seed: {mutation_seed}
Context: {context_str}
Instruction: Merge the two parents into a unique individual distinct from any previous iterations.
If extra context is provided, lean the new identity toward that context.
    """
    return system, user

# ---------------------------------------------------------------------------
# Core Generation
# ---------------------------------------------------------------------------

def _call_ollama(system, user):
    payload = {
        "model": MODEL_NAME,
        "system": system,
        "prompt": user,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "top_p": 0.9,
            "seed": random.randint(1, 1000000)
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get('response', '')
    except Exception as e:
        print(f"!!! DEBUG: REQUEST ERROR: {e}")
        return None

def process_identity_generation(p1=None, p2=None, user_context=None):
    """Generate a random identity. If p1 and p2 are provided, merge them."""
    mutation_seed = generate_mutation_id()
    age = generate_age()
    birthday = generate_birthday(age)
    ssn = generate_ssn()
    phone = generate_phone()
    gender = generate_gender()

    if p1 and p2:
        system, user = build_merge_prompt(p1, p2, gender, age, mutation_seed, user_context)
    else:
        system, user = build_random_prompt(gender, age, mutation_seed, user_context)

    raw_text = _call_ollama(system, user)
    if not raw_text:
        print("!!! DEBUG: No response from Ollama")
        return None

    print(f"--- RAW OLLAMA RESPONSE ---\n{raw_text}\n--- END ---")

    identity = parse_identity_text(raw_text)

    # Validate that essential fields were actually parsed
    if not identity or identity.get('name') == 'N/A' or not identity.get('name'):
        print(f"!!! DEBUG: Parsing failed or name missing. Got: {identity}")
        return None

    # Inject pre-generated numerical fields
    identity['personal_info']['age'] = str(age)
    identity['personal_info']['birthday'] = birthday
    identity['personal_info']['ssn'] = ssn
    identity['personal_info']['phone'] = phone
    identity['personal_info']['gender'] = gender

    return identity

# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

EMOJI_PATTERN = re.compile(
    "[\U0001F300-\U0001F9FF"
    "\U00002600-\U000027BF"
    "\U0000FE00-\U0000FEFF"
    "\U00002500-\U00002BEF"
    "\U00010000-\U0010FFFF]",
    flags=re.UNICODE,
)

def parse_identity_text(text):
    def extract(key):
        pattern = rf"(?i){key}\s*:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text)

        value = "N/A"
        if match:
            value = match.group(1).strip()
        elif key == "EMOJI":
            # Fallback 1: lone emoji on its own line
            emoji_match = re.search(r"^\s*([\U00010000-\U0010ffff]|\u263a)\s*$", text, re.MULTILINE)
            if emoji_match:
                value = emoji_match.group(1)
            else:
                # Fallback 2: emoji appended to the NAME line
                name_match = re.search(r"(?i)NAME\s*:\s*(.+?)(?:\n|$)", text)
                if name_match:
                    emojis_in_name = EMOJI_PATTERN.findall(name_match.group(1))
                    if emojis_in_name:
                        value = emojis_in_name[0]

        # Post-processing: Remove Markdown links [text](link) and asterisks
        value = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", value)
        value = value.replace('*', '')

        # Strip stray emojis from non-emoji fields
        if key != "EMOJI":
            value = EMOJI_PATTERN.sub('', value).strip()

        return value.strip()

    # Extract the raw emoji and validate it
    raw_emoji = extract("EMOJI")
    # If raw_emoji is text (e.g., "Laptop") or "N/A", use the placeholder 👤
    final_emoji = raw_emoji if EMOJI_PATTERN.search(raw_emoji) else "👤"

    return {
        "name": extract("NAME"),
        "emoji": final_emoji,
        "job": extract("JOB"),
        "position": extract("POSITION"),
        "bio": extract("BIO"),
        "interests": extract("INTERESTS"),  
        "personal_info": {
            "education": extract("EDUCATION"),
            "email": extract("EMAIL"),
            "address": extract("ADDRESS"),
        }
    }
