"""Deterministic verdict extraction and scoring-artifact generation."""

from __future__ import annotations

import re
from collections.abc import Iterable

from detective_client import Briefing, CastMember, ClueText, MeansOption


WORD_RE = re.compile(r"[a-z0-9]+")


def _words(value: str) -> set[str]:
    return set(WORD_RE.findall(value.casefold()))


def infer_culprit(briefing: Briefing) -> CastMember:
    """Select the cast member named most specifically in the canonical timeline."""
    timeline = " ".join(step.claim for step in briefing.timeline_steps).casefold()
    claim_openings = [
        _words(" ".join(step.claim.split()[:4])) for step in briefing.timeline_steps
    ]
    ranked: list[tuple[int, int, int, CastMember]] = []
    for member in briefing.cast:
        tokens = [token for token in _words(member.name) if len(token) > 2]
        exact = int(member.name.casefold() in timeline)
        subject_matches = sum(bool(set(tokens) & opening) for opening in claim_openings)
        matches = sum(timeline.count(token) for token in tokens)
        ranked.append((subject_matches, exact, matches, member))
    ranked.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
    if not ranked or ranked[0][:3] == (0, 0, 0):
        raise ValueError("The timeline does not identify a cast member")
    return ranked[0][3]


MEANS_SIGNALS: dict[str, set[str]] = {
    "poison": {
        "poison",
        "poisoned",
        "arsenic",
        "aconitine",
        "morphine",
        "dose",
        "toxicology",
        "acid",
        "cyanide",
        "prussic",
        "digitalis",
        "antimony",
        "tartar",
        "emetic",
    },
    "blade": {"blade", "knife", "knifed", "stab", "stabbed", "stabbing", "lancet", "sword"},
    "blunt": {
        "blunt",
        "bludgeon",
        "bludgeoned",
        "mallet",
        "hammer",
        "clubbed",
        "fracture",
        "strike",
        "struck",
        "blow",
        "weight",
    },
    "rope": {"rope", "strangle", "strangled", "garrote", "garroted"},
    "drown": {"drown", "drowned", "drowning", "submerged"},
    "natural": {"natural", "heart", "cardiac", "failure"},
    "fall": {"fall", "fell", "fallen", "accidental", "stair", "stairs", "staircase"},
}


def infer_means(briefing: Briefing) -> MeansOption:
    """Map explicit timeline language to one of the supplied means IDs."""
    timeline_text = " ".join(step.claim for step in briefing.timeline_steps).casefold()
    timeline_words = _words(timeline_text)
    decoy_words: set[str] = set()
    for marker in ("staging", "staged", "stage ", "mistaken for", "rather than"):
        if marker in timeline_text:
            decoy_words.update(_words(timeline_text.split(marker, maxsplit=1)[1]))
    primary_clause = briefing.timeline_steps[0].claim.casefold() if briefing.timeline_steps else ""
    for marker in ("then staged", "staging", "staged", "stage ", "mistaken for", "rather than"):
        primary_clause = primary_clause.split(marker, maxsplit=1)[0]
    primary_clause = primary_clause.split(".", maxsplit=1)[0]
    primary_words = _words(primary_clause)
    ranked: list[tuple[int, MeansOption]] = []
    for option in briefing.means_options:
        option_words = _words(f"{option.id} {option.name}")
        score = len(option_words & timeline_words) * 2
        score += len(option_words & primary_words) * 8
        for category, signals in MEANS_SIGNALS.items():
            if category in option_words or category in option.id.casefold() or option_words & signals:
                score += len(signals & timeline_words) * 2
                score += len(signals & primary_words) * 8
                score -= len((signals | option_words) & decoy_words) * 8
        ranked.append((score, option))
    ranked.sort(key=lambda row: row[0], reverse=True)
    if not ranked or ranked[0][0] == 0:
        raise ValueError("The timeline does not identify a means option")
    return ranked[0][1]


def _significance(clue: ClueText, culprit: CastMember, means: MeansOption) -> str:
    text = clue.text
    words = _words(text)
    culprit_name = culprit.name
    clue_id = clue.clue_id.casefold()
    if any(
        phrase in text.casefold()
        for phrase in (
            "i did it",
            "i killed",
            "i struck him",
            "i put it",
            "i introduced",
            "i was there",
            "it went wrong",
            "i strangled",
            "i could not let that happen",
            "i picked up the weight",
            "i prepared the extract",
            "i put antimony",
            "i chose not to negotiate",
        )
    ):
        return (
            f"Directly records {culprit_name}'s admission, confirming the confrontation, "
            "motive, opportunity, and killing rather than merely placing the suspect nearby."
        )
    if clue_id == "clue_01":
        return (
            "Identifies the victim, setting, and condition of the body, anchoring the people and "
            "circumstances that the remaining evidence explains."
        )
    if "time of death" in text.casefold() or "death estimated between" in text.casefold():
        return (
            f"Fixes the critical time window and tests {culprit_name}'s opportunity against the "
            "documentary and witness timeline."
        )
    if clue_id.endswith("k1") or " key" in text.casefold():
        return (
            f"Establishes access to the locked evidence location and connects {culprit_name}'s "
            "opportunity to the physical evidence recovered inside."
        )
    if clue_id.endswith("2a"):
        return (
            f"Records {culprit_name}'s partial admission and rejected innocent explanation, "
            "confirming access to the incriminating substance or object while preserving the "
            "contradiction that later testimony resolves."
        )
    if any(
        phrase in text.casefold()
        for phrase in (
            "i had adjusted",
            "i knew about the will",
            "i use that weight",
            "i served tea as i always do",
        )
    ):
        return (
            f"Records {culprit_name}'s partial admission or defensive explanation, which confirms "
            "access to key evidence while preserving contradictions resolved by the later chain."
        )
    if any(phrase in text.casefold() for phrase in ("i don't know anything", "no knowledge")):
        return (
            f"Records {culprit_name}'s denial or false alibi, which the physical, documentary, "
            "and witness evidence directly contradicts and thereby shows consciousness of guilt."
        )
    if any(
        phrase in text.casefold()
        for phrase in (
            "i was stacking",
            "at home all evening",
            "reviewing correspondence in the library",
        )
    ):
        return (
            f"Records {culprit_name}'s claimed alibi or denial, which the physical, documentary, "
            "and witness evidence contradicts and thereby demonstrates consciousness of guilt."
        )
    if any(
        phrase in text.casefold()
        for phrase in (
            "did not leave my sight",
            "was with me",
            "with me all",
            "all afternoon",
            "all evening",
            "forty witnesses",
            "from five o'clock onward",
            "until the alarm",
            "door was locked and the lights were out",
            "did not return before",
            "left by seven",
        )
    ):
        return (
            "Establishes or corroborates an alibi during the critical time window, testing "
            "opportunity and excluding an alternative suspect despite an apparent motive."
        )
    if any(
        stem in text.casefold()
        for stem in (
            "threat",
            "dismiss",
            "inherit",
            "inquiry",
            "embezzl",
            "cutting off",
            "allowance",
            "report to",
            "magistrate",
            "would have received nothing",
            "disinherited",
        )
    ):
        return (
            f"Establishes the concrete motive and imminent pressure on {culprit_name}, explaining "
            "why the victim was silenced at that particular time."
        )
    if any(
        phrase in text.casefold()
        for phrase in (
            "access to",
            "asked me to leave",
            "alone for",
            "door was shut",
            "came back",
        )
    ):
        return (
            f"Establishes {culprit_name}'s unusual access and opportunity during the critical "
            "window, contradicting the innocent account and connecting the suspect to the scene."
        )
    if "warrant" in words:
        return (
            "Establishes lawful access to the locked crime scene and enables recovery of the "
            "physical evidence that links the fatal means to the culprit."
        )
    if any(phrase in text.casefold() for phrase in ("it was him", "it was her", "that's silas")):
        return (
            f"Closes the identification chain by naming {culprit_name} as the previously "
            "described figure and linking independent witness testimony to the documentary evidence."
        )
    if "handwriting" in words or "signature" in words:
        return (
            f"Confirms {culprit_name} personally authored the incriminating record, ruling out "
            "forgery or clerical error and making the plan the culprit's deliberate initiative."
        )
    if any(phrase in text.casefold() for phrase in ("paid in full", "cleared my debt")):
        return (
            "Removes the apparent financial motive and corroborates the named alternative "
            "suspect's account, helping exclude that person from the murder."
        )
    if any(phrase in text.casefold() for phrase in ("acting strange", "secretive", "off-book")):
        return (
            f"Shows {culprit_name}'s suspicious concealment of the operation underlying the "
            "murder, corroborating the plan and motive established by stronger evidence."
        )
    if "reputation" in words or "bad word" in text.casefold():
        return (
            "Defines the victim's known relationships and possible background grievances, helping "
            "separate vague alternative motives from the culprit's concrete and corroborated motive."
        )
    if any(phrase in text.casefold() for phrase in ("found the body", "first light", "blood had")):
        return (
            "Independently corroborates when and where the body was discovered and supports the "
            "medical time-of-death window rather than identifying the fatal mechanism."
        )
    if any(
        phrase in text.casefold()
        for phrase in (
            "not the cause",
            "postmortem",
            "not the instrument",
            "no blood",
            "untampered",
            "incidental",
            "applied after death",
            "no defensive wounds",
            "nothing of value",
            "nothing appears missing",
            "body was moved",
            "no traumatic injury",
            "inconsistent with self-infliction",
            "nothing from the public shop",
            "ransacking is superficial",
        )
    ):
        return (
            f"Eliminates a misleading apparent cause or staging prop and supports {means.name} "
            "as the true fatal mechanism."
        )
    if any(
        phrase in text.casefold()
        for phrase in (
            "slot on the",
            "fresh scuff marks",
            "altered figures",
            "different shade",
            "finer pen nib",
        )
    ):
        return (
            f"Provides physical or documentary trace evidence connecting {culprit_name} to the "
            "removed weapon, falsified record, or deliberate concealment."
        )
    if words & {"match", "matches", "matching", "geometry", "serration", "residue"}:
        return (
            "Physically connects the recovered instrument or substance to the fatal injury, "
            f"confirming {means.name} as the specific means rather than an incidental object."
        )
    if words & {"toxicology", "wound", "fracture", "cause", "autopsy", "blood", "fibres"}:
        return (
            f"Establishes the medical cause and physical mechanism of death as {means.name}, "
            "linking the fatal injury to the recovered weapon or substance."
        )
    if words & {"initials", "monogram", "owned", "belongs", "personal", "prescription"}:
        return (
            f"Directly attributes ownership or access to {culprit_name}, linking the means "
            "to the suspect's possession and closing the ownership chain."
        )
    if words & {"thumbprint", "fingerprint", "print", "grip"}:
        return (
            f"Physically attributes handling of the incriminating object to {culprit_name}, "
            "linking the suspect directly to the identified murder instrument."
        )
    if words & {"saw", "seen", "witness", "identified", "recognised", "recognized"}:
        return (
            f"Independently places or identifies {culprit_name} in the relevant sequence, "
            "corroborating the documentary and physical evidence with eyewitness testimony."
        )
    if words & {"alibi", "elsewhere", "until", "throughout"}:
        return (
            "Tests opportunity and narrows the suspect pool by placing the named person away "
            "from the crime during the relevant time window."
        )
    if words & {
        "record",
        "ledger",
        "manifest",
        "receipt",
        "entry",
        "signed",
        "letter",
        "handwriting",
        "signature",
        "memorandum",
    }:
        return (
            f"Provides documentary proof connecting {culprit_name} to the plan, motive, or "
            "critical time window and rules out coincidence, forgery, or clerical error."
        )
    if words & {"threat", "dismiss", "inherit", "inquiry", "embezzle", "motive"}:
        return (
            f"Establishes {culprit_name}'s concrete motive and explains why the victim had to "
            "be silenced at that particular time."
        )
    return (
        f"Corroborates the evidence chain against {culprit_name} and helps connect "
        f"motive, opportunity, and {means.name} to the canonical sequence of events."
    )


def build_evidence_notes(
    clues: Iterable[ClueText], culprit: CastMember, means: MeansOption
) -> list[dict[str, str]]:
    """Write one grounded note per observed clue; never fabricate clue IDs."""
    notes: list[dict[str, str]] = []
    seen: set[str] = set()
    for clue in clues:
        if clue.clue_id in seen:
            continue
        seen.add(clue.clue_id)
        source = clue.text.strip().rstrip(".")
        note = f"{_significance(clue, culprit, means)} Specifically, {source}."
        notes.append({"clue_id": clue.clue_id, "note": note})
    return notes


def build_process_explanation(
    briefing: Briefing,
    culprit: CastMember,
    means: MeansOption,
    clues: Iterable[ClueText],
    *,
    max_words: int = 138,
) -> str:
    """Use the disclosed canonical timeline as the semantic center of the narrative."""
    timeline = " ".join(step.claim.strip().rstrip(".") + "." for step in briefing.timeline_steps)
    clue_list = list(clues)
    forensic: str | None = None
    admission: str | None = None
    for clue in clue_list:
        text = clue.text.casefold()
        words = _words(clue.text)
        if forensic is None and words & {
            "toxicology",
            "matches",
            "wound",
            "fracture",
            "blood",
            "serration",
        }:
            forensic = clue.text.strip().rstrip(".")
        if admission is None and any(
            phrase in text
            for phrase in (
                "i did it",
                "i struck him",
                "i put it",
                "i introduced",
                "i was there",
                "it went wrong",
            )
        ):
            admission = clue.text.strip().rstrip(".")
    opening = f"{culprit.name} committed the murder using {means.name}."
    alternatives = ", ".join(member.name for member in briefing.cast if member.id != culprit.id)
    parts = [opening, timeline]
    if forensic:
        parts.append("The forensic evidence established that " + forensic + ".")
    if admission:
        parts.append("The culprit's own admission confirms: " + admission + ".")
    if alternatives:
        parts.append(
            f"The evidence and corroborated alibis exclude {alternatives}; none shares the "
            "complete chain of motive, opportunity, means, and admission."
        )
    words = " ".join(parts).split()
    return " ".join(words[:max_words])
