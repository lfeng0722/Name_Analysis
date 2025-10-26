import re

RULES = [
    re.compile(r" (S\d+ D\d+|S\d+|D\d+)( RAIN DEL)?$"),
    re.compile(r"[ -]+(SESSION ?\d+|PART ?\d+|EP ?\.?\d+|TX\d+|FEED\d+)$"),
    re.compile(r"[ -]+(\d+)?(AM|PM)$"),
    re.compile(r"[ -]+(PRE MATCH|POST MATCH|POST GAME|POST-GAME)( RAIN DEL)?$"),
    re.compile(r"[ -]+(RPT|ENCORE|GEM|RAIN DEL)$"),
    re.compile(r"[ -]+(DAY|EV|LE|EM|EARLY|NIGHT|LATE)$"),
    re.compile(r"[ -]+(MON|TUE|WED|THU|FRI|SAT|SUN)$"),
    re.compile(r" ?\([R]\)$"),
    re.compile(r" \[LIVE\]$"),
    re.compile(r" S\d+ E\d+$"),
    re.compile(r" \d+ (SESSION|PART|EP|TX|FEED)\d*$"),
    re.compile(r" \d+$"),
    re.compile(r"^M- ")
]


def normalise_title(messy_title: str) -> str:
    """Recursively apply regex rules to clean a TV title."""
    clean_title = messy_title
    original_title = clean_title

    for rule in RULES:
        clean_title = rule.sub("", clean_title)

    clean_title = clean_title.strip()

    if clean_title != original_title and clean_title:
        return normalise_title(clean_title)

    return clean_title
