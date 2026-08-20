# utils/slug.py

import re

def slugify(title: str) -> str:
    t = title.lower()
    t = re.sub(r'[^a-z0-9\s]+', '', t)
    t = re.sub(r'\s+', '_', t)
    return t.strip('_')