import pytest
from app.model import normalise_title

# ---------------------------
# Unit tests for pure function
# ---------------------------

@pytest.mark.unit
@pytest.mark.parametrize(
    "messy,expected",
    [
        # Baseline happy paths from the spec
        ("BILLY THE EXTERMINATOR-DAY (R)", "BILLY THE EXTERMINATOR"),
        ("GOTHAM -RPT", "GOTHAM"),
        ("HOT SEAT -5PM", "HOT SEAT"),
        ("MIXOLOGY-EARLY(R)", "MIXOLOGY"),
        ("SHOW S01 E02 -POST MATCH [LIVE]", "SHOW"),         # Multiple rules + recursion
        ("M- BREAKING NEWS 2 EP3", "BREAKING NEWS"),         # Remove 'M-' prefix and numeric tail
        ("PROGRAM 10 FEED2", "PROGRAM"),
        ("PROGRAM 10 SESSION2", "PROGRAM"),
        ("SOMETHING - MON", "SOMETHING"),                    # Day-of-week
        ("SOMETHING - NIGHT", "SOMETHING"),                  # Time-of-day bucket
        ("SOMETHING - ENCORE", "SOMETHING"),                 # Replay marker
        # NOTE: tabs are NOT matched by the rules' `[ -]+` pattern; only spaces/hyphens are.
        ("SOMETHING \t - \t 5PM ", "SOMETHING \t -"),        # Matches '- 5PM' but leaves '\t -'
        ("Pokémon - ENCORE", "Pokémon"),                     # Unicode should be preserved
        ("", ""),                                            # Empty input → empty output (no crash)
        ("ALREADY CLEAN", "ALREADY CLEAN"),                  # No-op when no patterns match

        # ---------- Additional edge cases (selected to exercise each rule family) ----------

        # AM/PM + TX/FEED/EP/SESSION/PART endings
        ("VET ON THE HILL -PM TX1", "VET ON THE HILL"),          # '-PM' and 'TX1'
        ("MILLION DOLLAR COLD CASE-PART 2", "MILLION DOLLAR COLD CASE"),
        ("THE BIG BANG THEORY-EP.2", "THE BIG BANG THEORY"),     # 'EP.2' with a dot
        ("HOT SEAT -5PM", "HOT SEAT"),

        # DAY/EV/LE/EM/EARLY/NIGHT/LATE endings
        ("THE AMAZING RACE-DAY", "THE AMAZING RACE"),
        ("ANTIQUES ROADSHOW -EV", "ANTIQUES ROADSHOW"),
        ("POIROT -LE", "POIROT"),
        ("HARDCORE PAWN-EARLY", "HARDCORE PAWN"),

        # Day-of-week variants (note: recursion will then remove trailing LATE)
        ("NINE NEWS LATE -THU", "NINE NEWS"),

        # Combinations requiring multiple passes (recursion)
        # After removing "- SESSION 1" we get "... GAME 9", then trailing " 9" is removed by ` \d+$`
        ("CRICKET: WOMEN'S BIG BASH LEAGUE GAME 9 - SESSION 1", "CRICKET: WOMEN'S BIG BASH LEAGUE GAME"),
        ("SEVEN'S TENNIS: 2018 AUSTRALIAN OPEN-DAY 2 FEED2", "SEVEN'S TENNIS: 2018 AUSTRALIAN OPEN"),

        # Season/Day with optional 'RAIN DEL'
        ("SEVEN'S CRICKET: FOURTH TEST - AUSTRALIA V INDIA D4 S2 RAIN DEL",
         "SEVEN'S CRICKET: FOURTH TEST - AUSTRALIA V INDIA"),

        # NOTE: "-S1" is NOT removed by any rule (they expect a preceding space), so it remains unchanged.
        ("SEVEN'S CRICKET: BIG BASH LEAGUE GRAND FINAL-S1",
         "SEVEN'S CRICKET: BIG BASH LEAGUE GRAND FINAL-S1"),

        # 'M-' prefix
        ("M- RESIDENT EVIL: APOCALYPSE-PM", "RESIDENT EVIL: APOCALYPSE"),

        # 'DAY <num>' and trailing pure number combination (needs recursion)
        ("SEVEN'S TENNIS: 2017 AUSTRALIAN OPEN - DAY 1", "SEVEN'S TENNIS: 2017 AUSTRALIAN OPEN"),

        # '(R)' replay flag
        ("BILLY THE EXTERMINATOR-DAY (R)", "BILLY THE EXTERMINATOR"),
    ],
)
def test_normalise_title_cases(messy, expected):
    """Parameterized table of representative + edge inputs and expected outputs."""
    assert normalise_title(messy) == expected


@pytest.mark.unit
def test_normalise_title_idempotent():
    """Applying the function twice should not change the already-clean result."""
    s = "SHOW -RPT"
    once = normalise_title(s)
    twice = normalise_title(once)
    assert once == twice


@pytest.mark.unit
def test_normalise_title_only_noise_reduces_but_keeps_leading_tokens():
    """
    A 'mostly-noise' string reduces to leading 'S01 E02' because rules only remove
    ' Sxx Exx' when preceded by a space or when at the end with a leading space.
    The artifact does NOT remove leading 'Sxx Exx' at the start of the string.
    """
    s = "M- S01 E02 -POST MATCH -RPT (R) 5PM"
    assert normalise_title(s) == "S01 E02"
