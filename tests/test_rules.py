"""Rules that decide what counts. None of these need the data."""
import numpy as np
import pytest

import extract_hansard as xh
import hansard_index as hi
import ngram_index as ni
from words import (BY_KEY, WORDS, masks_for, norm, notation_prone, queries, resolve_mask, star_hit,
                   trail_masks)


# --- masks in books ---------------------------------------------------------------

def test_dash_masks_keep_first_and_last_letter():
    assert masks_for("damn", [])[:4] == ["d-n", "d--n", "d---n", "d----n"]


def test_single_hyphen_dropped_after_determiner_only():
    assert "s-l" not in masks_for("scoundrel", [], "the {scoundrel}")
    assert "s--l" in masks_for("scoundrel", [], "the {scoundrel}")
    assert "d-d" in masks_for("damned", [], "be {damned}")


def test_notation_prone_frames():
    assert notation_prone("the {x}") and notation_prone("his {x}")
    assert not notation_prone("you {x}") and not notation_prone("what the {x}")


def test_asterisk_masks_never_sent_as_plain_queries():
    for w in WORDS:
        for q in queries(w):
            if q.kind != "star":
                assert "*" not in q.text


def test_trailing_masks_need_two_dashes():
    assert trail_masks("damn") == ["d--", "d---", "d----"]


def test_trailing_and_star_only_in_unambiguous_frames():
    for q in queries(BY_KEY["bastard"]):
        assert q.kind not in ("trail", "star")  # "you b---" could be four different words
    kinds = {q.kind for q in queries(BY_KEY["fuck"]) if q.frame == "what the {fuck}"}
    assert {"full", "dash", "trail", "star"} <= kinds


def test_capitalised_variant_queried():
    q = next(q for q in queries(BY_KEY["hell"]) if q.kind == "full" and q.frame == "what the {hell}")
    assert q.variants == ["What the hell", "what the hell"]


def test_norm_matches_api_spelling():
    assert norm("be d--d") == "be d -- d"
    assert norm("b-gg-r off") == "b - gg - r off"


def test_star_hit_case_rule():
    assert star_hit("what the f *", "What the f *")
    assert not star_hit("the n *", "the N *")          # notation, not a masked word
    assert not star_hit("what the f *", "what the f is")


def test_every_frame_contains_a_known_form():
    for w in WORDS:
        for f in w.frames:
            assert any("{" + form + "}" in f for form in w.forms), (w.key, f)


# --- smoothing and events -----------------------------------------------------------

def test_spike_capped_but_trend_kept():
    x = np.array([[10.0] * 10 + [5000.0] + [10.0] * 10])
    y = ni.cap_spikes(x)
    assert y[0, 10] == pytest.approx(4 * 10 + 25)
    ramp = np.array([np.linspace(0, 200, 21)])
    assert np.allclose(ni.cap_spikes(ramp), ramp)


def test_window_sum():
    a = np.arange(10.0)[None]
    s = ni.window_sum(a, 1)
    assert s[0, 0] == 0 + 1 and s[0, 5] == 4 + 5 + 6 and s[0, 9] == 8 + 9


def test_rate_needs_support():
    full = np.full((1, 30), 1.0)
    masked = np.zeros((1, 30))
    r, tot = ni.rate(full, masked)
    assert np.all(np.isnan(r))  # 11 per window is under the support floor


def test_events_half_peak_span():
    years = np.arange(1900, 1910)
    r = np.array([0, 1, 3, 6, 10, 7, 4, 2, 6, 0], float)
    e = ni.events(years, r)
    assert (e["peak_year"], e["rise"], e["fall"]) == (1904, 1903, 1905)


# --- Hansard -------------------------------------------------------------------------

@pytest.mark.parametrize("token,word", [
    ("b*****d", "bastard"), ("f***", "fuck"), ("f**king", "fuck"), ("d——d", "damn"),
    ("d--d", "damn"), ("bl——y", "bloody"), ("n*****", "nword"),
])
def test_masks_resolve(token, word):
    assert resolve_mask(token) == word


@pytest.mark.parametrize("token", ["b***", "s***", "it--and", "I—", "d--", "of*"])
def test_ambiguous_or_noise_masks_rejected(token):
    assert resolve_mask(token) is None


def test_full_forms_whole_words_only():
    found = [m.group(1).lower() for m in xh.FULL.finditer("Hello shell, the damned Bastardy Bill, bloody hell")]
    assert found == ["damned", "bloody", "hell"]


@pytest.mark.parametrize("text", [
    "Order. That is an unparliamentary expression.",
    "I must ask the hon. Member to withdraw that word.",
    "The hon. Gentleman must withdraw.",
    "Will the hon. Member withdraw that remark?",
])
def test_challenge_detected(text):
    assert xh.CHALLENGE.search(text)


@pytest.mark.parametrize("text", [
    "I beg to ask leave to withdraw the Amendment.",
    "The Motion was, by leave, withdrawn.",
])
def test_procedural_withdrawals_not_challenges(text):
    assert not xh.CHALLENGE.search(text)


def test_euphemism_pattern():
    assert not xh.EUPH.search("the C-word, cuts")
    m = xh.EUPH.search("he used the N-word in the Chamber")
    assert m and m.group(1).lower() == "n"


def test_era_bins_cover_period():
    assert hi.era_of(1919) == "1919-1939" and hi.era_of(2026) == "2000-2026" and hi.era_of(1918) is None


def test_poisson_ci_contains_count():
    lo, up = hi.poisson_ci(10)
    assert lo < 10 < up and hi.poisson_ci(0)[0] == 0


@pytest.mark.parametrize("text", ["the shame is the nation's—it is ours", "can't—or won't", "N.C.O.s—it is"])
def test_sentence_dashes_are_not_masks(text):
    assert not [m for m in xh.MASK.finditer(text) if resolve_mask(m.group(1))]


@pytest.mark.parametrize("text", [
    "Order. That sort of coarse language is uncharacteristic of the hon. Gentleman.",
    "He must not use words like that.",
    "Order. Policies can be hypocritical, but not individual Members.",
    "Will the hon. Gentleman withdraw?",
    "it would not be legitimate to make such a charge against an individual Member",
])
def test_modern_challenges_detected(text):
    assert xh.CHALLENGE.search(text)


@pytest.mark.parametrize("text", [
    "Does the hon. Member wish to withdraw the amendment?",
    "Is it your pleasure that the amendment be withdrawn?",
])
def test_procedural_chair_withdrawals_not_challenges(text):
    assert not xh.CHALLENGE.search(text)
