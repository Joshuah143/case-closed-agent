"""Controlled S001 scorer probe using the public documentation's reference-style answer."""

from __future__ import annotations

import argparse
import json

from detective_client import DetectiveClient


REFERENCE_NOTES = [
    {
        "clue_id": "clue_04",
        "note": (
            "Establishes Silas placed himself at the warehouse at midnight by creating an "
            "official cargo appointment — providing both a pretext to lure the victim there "
            "and documentary proof of his own presence."
        ),
    },
    {
        "clue_id": "clue_05",
        "note": (
            "Confirms Silas authored the ledger entry personally, ruling out forgery and "
            "placing the midnight appointment squarely on his own initiative rather than a "
            "clerical error."
        ),
    },
    {
        "clue_id": "clue_M1",
        "note": (
            "Places a distinctively limping figure moving toward the warehouse at the exact "
            "time of the murder, corroborating the ledger's midnight appointment with "
            "independent testimony before any name is attached."
        ),
    },
    {
        "clue_id": "clue_M2",
        "note": (
            "Closes the chain — the same witness identifies the ledger as Silas's private "
            "cargo book and names him as the limping figure she saw, linking the documentary "
            "evidence to a specific suspect."
        ),
    },
    {
        "clue_id": "clue_02",
        "note": (
            "Establishes cause of death and narrows the murder weapon to a fixed-blade knife — "
            "the same category as the monogrammed knife later found at the warehouse — ruling "
            "out all other means."
        ),
    },
    {
        "clue_id": "clue_06",
        "note": (
            "Physically connects the knife found at the warehouse to the fatal wound via "
            "matching blade width and serration, confirming it as the specific murder weapon "
            "rather than merely an associated object."
        ),
    },
    {
        "clue_id": "clue_07",
        "note": (
            "Directly attributes ownership of the murder weapon to Silas Vane through his own "
            "monogram on the pommel, placing the instrument of death in his possession."
        ),
    },
    {
        "clue_id": "clue_S2",
        "note": (
            "Silas's own confession confirms his presence at the warehouse, the confrontation "
            "over the illegal cargo run, and the killing — completing the chain from motive "
            "and opportunity to act."
        ),
    },
]

REFERENCE_EXPLANATION = (
    "Silas Vane arranged a secret midnight cargo run to lure Aldric Marsh to the warehouse, "
    "then stabbed him when Marsh threatened to report the illegal operation to the magistrate. "
    "A witness confirmed Silas was at the warehouse at midnight and his monogrammed knife "
    "matches the wound. When confronted with the physical evidence, he confessed."
)

SUPPORTING_NOTES = [
    {
        "clue_id": "clue_01",
        "note": (
            "Identifies the victim as Aldric Marsh, a harbor merchant whose shipping business "
            "connects him directly to Silas Vane's off-book cargo operation and explains why "
            "the illegal warehouse run could be used as a credible lure."
        ),
    },
    {
        "clue_id": "clue_03",
        "note": (
            "Fixes the death between midnight and two in the morning, aligning the murder with "
            "Silas's midnight warehouse delivery, Mara's sighting, and the time the victim was "
            "drawn away from the public docks."
        ),
    },
    {
        "clue_id": "clue_F1",
        "note": (
            "Deputy Finn's dawn discovery and observation that the blood had already darkened "
            "independently corroborate that Marsh died several hours earlier, consistent with "
            "the medical midnight-to-two estimate rather than a dawn attack."
        ),
    },
    {
        "clue_id": "clue_F2",
        "note": (
            "Establishes that Marsh was generally considered an honest merchant and narrows the "
            "credible conflict to specific business dealings, supporting the disclosed illegal "
            "cargo motive over an unidentified enemy or random dockside grievance."
        ),
    },
    {
        "clue_id": "clue_R1",
        "note": (
            "Rex states that his debt dispute with Marsh ended three months earlier, weakening "
            "the apparent financial motive against him; the signed receipt independently "
            "corroborates this claim and helps exclude Rex as the killer."
        ),
    },
    {
        "clue_id": "clue_R2",
        "note": (
            "Shows Silas had recently become secretive about nighttime warehouse traffic, "
            "corroborating the hidden off-book cargo operation that supplied his motive and the "
            "pretext for bringing Marsh to the warehouse."
        ),
    },
    {
        "clue_id": "clue_W1",
        "note": (
            "Authorises lawful entry to the bonded warehouse and enables recovery of the "
            "matching monogrammed knife; it preserves the investigative chain connecting the "
            "warehouse search to the physical murder weapon."
        ),
    },
    {
        "clue_id": "clue_S1",
        "note": (
            "Records Silas's false alibi that he left the office at ten and knew nothing of a "
            "midnight delivery; his signed ledger, Mara's identification, and later admission "
            "directly contradict this denial and demonstrate consciousness of guilt."
        ),
    },
    {
        "clue_id": "clue_08",
        "note": (
            "The signed receipt objectively confirms Rex paid his debt to Marsh in full three "
            "months before the murder, removing the principal suspected motive and corroborating "
            "Rex's account rather than merely relying on his denial."
        ),
    },
    {
        "clue_id": "clue_09",
        "note": (
            "Places Rex drinking at the tavern until closing on the murder night; although he "
            "appeared agitated, the bartender's independent account supports an alibi away from "
            "the warehouse during the critical midnight sequence."
        ),
    },
]

SUPPORTING_TEXT = {
    "clue_01": "The victim is Aldric Marsh, harbor merchant, age 47.",
    "clue_03": "Time of death estimated between midnight and 2 a.m., based on body temperature.",
    "clue_F1": (
        "I found the body at first light, near Pier 3. He'd been there a few hours at least — "
        "the blood had already gone dark."
    ),
    "clue_F2": (
        "Aldric Marsh had a reputation for clean dealings. I never heard a bad word against "
        "him except from dock hands who thought he underpaid."
    ),
    "clue_R1": (
        "I cleared my debt with Aldric fair and square, three months back. I've got nothing "
        "against the man."
    ),
    "clue_R2": (
        "Silas Vane's been acting strange for weeks — secretive about who goes in and out of "
        "the warehouse at night."
    ),
    "clue_W1": (
        "An official search warrant, signed by the magistrate, authorising entry to any bonded "
        "warehouse on the dock district."
    ),
    "clue_S1": (
        "I was at the office finishing the month-end accounts all evening. Left around ten, "
        "went straight home. I don't know anything about a midnight delivery."
    ),
    "clue_08": (
        "A signed receipt shows Rex Bowman cleared a substantial debt to Aldric Marsh three "
        "months ago — paid in full."
    ),
    "clue_09": (
        "The bartender says Rex Bowman came in looking agitated the night of the murder and "
        "drank heavily until closing."
    ),
}

FULL_NOTES = [*REFERENCE_NOTES, *SUPPORTING_NOTES]

FULL_EXPLANATION = (
    "Silas Vane, the harbormaster's deputy, killed merchant Aldric Marsh with his personal "
    "fixed-blade knife in the riverside warehouse between midnight and two. Silas scheduled an "
    "illegal midnight cargo delivery to lure Marsh there, then stabbed him when Marsh threatened "
    "to report the off-book run. Silas's signed ledger and matching handwriting prove he arranged "
    "the meeting. Mara Quinn saw a limping man approach the warehouse and identified him as Silas. "
    "The recovered knife matched the wound and bore Silas's initials; confronted with it, he "
    "confessed. Deputy Finn's discovery corroborates the death window. Rex Bowman is excluded "
    "because his debt was paid and he remained drinking at the tavern until closing. Mara and "
    "Finn are witnesses, not suspects."
)


def _collect_all_s001(client: DetectiveClient) -> None:
    client.start_session("S001")
    client.search()
    client.interview("char_finn")
    client.interview("char_mara")
    client.move("loc_office")
    client.search()
    client.interview("char_silas")
    client.move("loc_harbor")
    client.move("loc_tavern")
    client.search()
    client.move("loc_harbor")
    client.move("loc_alley")
    client.interview("char_rex")
    client.move("loc_warehouse")
    client.search()
    client.move("loc_alley")
    client.move("loc_harbor")
    client.present("char_mara", "item_ledger")
    client.move("loc_office")
    client.present("char_silas", "clue_07")


def run_reference_probe() -> dict:
    """Collect only the eight documented key clues, then submit the documented answer style."""
    client = DetectiveClient()
    client.start_session("S001")
    client.search()  # clue_02
    client.interview("char_mara")  # clue_M1
    client.move("loc_office")
    client.search()  # clue_04, clue_05, item_ledger, item_warrant
    client.move("loc_harbor")
    client.move("loc_alley")
    client.move("loc_warehouse")
    client.search()  # clue_06, clue_07
    client.move("loc_alley")
    client.move("loc_harbor")
    client.present("char_mara", "item_ledger")  # clue_M2
    client.move("loc_office")
    client.present("char_silas", "clue_07")  # clue_S2
    result = client.commit(
        culprit_id="char_silas",
        means_id="means_blade",
        evidence_notes=REFERENCE_NOTES,
        process_explanation=REFERENCE_EXPLANATION,
    )
    return result.model_dump()


def run_full_probe() -> dict:
    """Collect all 18 S001 clues in 19 actions and test complete semantic coverage."""
    client = DetectiveClient()
    _collect_all_s001(client)
    result = client.commit(
        culprit_id="char_silas",
        means_id="means_blade",
        evidence_notes=FULL_NOTES,
        process_explanation=FULL_EXPLANATION,
    )
    return result.model_dump()


def run_raw_probe(*, prefix: str = "") -> dict:
    """Compare lexical clue-text overlap with interpretive notes."""
    client = DetectiveClient()
    _collect_all_s001(client)
    raw_notes = [
        {"clue_id": clue_id, "note": f"{prefix}{text}"}
        for clue_id, text in SUPPORTING_TEXT.items()
    ]
    result = client.commit(
        culprit_id="char_silas",
        means_id="means_blade",
        evidence_notes=[*REFERENCE_NOTES, *raw_notes],
        process_explanation=FULL_EXPLANATION,
    )
    return result.model_dump()


def _collect_supporting_clue(client: DetectiveClient, clue_id: str) -> None:
    client.start_session("S001")
    if clue_id in {"clue_01", "clue_03"}:
        client.search()
    elif clue_id in {"clue_F1", "clue_F2"}:
        client.interview("char_finn")
    elif clue_id in {"clue_R1", "clue_R2"}:
        client.move("loc_alley")
        client.interview("char_rex")
    elif clue_id in {"clue_W1"}:
        client.move("loc_office")
        client.search()
    elif clue_id in {"clue_S1"}:
        client.move("loc_office")
        client.interview("char_silas")
    elif clue_id in {"clue_08", "clue_09"}:
        client.move("loc_tavern")
        client.search()
    else:
        raise ValueError(f"No minimal collection route for {clue_id}")


def run_note_ablation() -> list[dict]:
    """Measure each supporting note's isolated contribution to the 18-note pool."""
    results = []
    for entry in SUPPORTING_NOTES:
        client = DetectiveClient()
        _collect_supporting_clue(client, entry["clue_id"])
        result = client.commit(
            culprit_id="char_silas",
            means_id="means_blade",
            evidence_notes=[entry],
            process_explanation=FULL_EXPLANATION,
        )
        results.append(
            {
                "clue_id": entry["clue_id"],
                "notes_score": result.notes_score,
                "isolated_similarity_squared": round((result.notes_score or 0) * 18, 6),
                "notes_correct": result.notes_correct,
                "notes_missing": result.notes_missing,
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ablate-notes", action="store_true")
    parser.add_argument("--raw-notes", action="store_true")
    parser.add_argument("--minimal-notes", action="store_true")
    args = parser.parse_args()
    if args.ablate_notes:
        result = run_note_ablation()
    elif args.raw_notes:
        result = run_raw_probe()
    elif args.minimal_notes:
        result = run_raw_probe(prefix="Establishes that ")
    else:
        result = run_full_probe()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
