from detective_client import (
    Briefing,
    CastMember,
    ClueText,
    LocationInfo,
    MeansOption,
    TimelineStepBrief,
)

from case_closed.reasoning import (
    build_evidence_notes,
    build_process_explanation,
    infer_culprit,
    infer_means,
)


def briefing() -> Briefing:
    return Briefing(
        synopsis="Aldric Marsh was killed at the harbor.",
        locations=[LocationInfo(id="loc_harbor", name="Harbor")],
        cast=[
            CastMember(id="char_finn", name="Deputy Finn"),
            CastMember(id="char_silas", name="Silas Vane"),
        ],
        means_options=[
            MeansOption(id="means_rope", name="Rope"),
            MeansOption(id="means_blade", name="Knife"),
        ],
        timeline_steps=[
            TimelineStepBrief(
                step_id="step_1", claim="Silas Vane brought Marsh to the warehouse at midnight."
            ),
            TimelineStepBrief(
                step_id="step_2", claim="Silas Vane stabbed Marsh with his personal knife."
            ),
        ],
    )


def test_verdict_is_extracted_from_timeline() -> None:
    case = briefing()
    assert infer_culprit(case).id == "char_silas"
    assert infer_means(case).id == "means_blade"


def test_culprit_is_timeline_actor_not_most_frequent_victim_surname() -> None:
    case = Briefing(
        synopsis="Cornelius Fitch was killed.",
        locations=[LocationInfo(id="loc_archive", name="Archive")],
        cast=[
            CastMember(id="char_bram", name="Mr. Bramwell Fitch"),
            CastMember(id="char_aldous", name="Mr. Aldous Crane"),
        ],
        means_options=[MeansOption(id="means_poison", name="Poisoned")],
        timeline_steps=[
            TimelineStepBrief(
                step_id="step_1", claim="Crane delivered poisoned tea to Fitch at three."
            ),
            TimelineStepBrief(
                step_id="step_2", claim="Crane confessed after Fitch's report was found."
            ),
        ],
    )
    assert infer_culprit(case).id == "char_aldous"


def test_means_uses_fatal_mechanism_not_staging_prop() -> None:
    case = Briefing(
        synopsis="The victim was found in a pond with rope on his ankles.",
        locations=[LocationInfo(id="loc_pond", name="Pond")],
        cast=[CastMember(id="char_cray", name="Mr. Jed Cray")],
        means_options=[
            MeansOption(id="means_rope", name="Strangled"),
            MeansOption(id="means_drown", name="Drowned"),
            MeansOption(id="means_blunt", name="Bludgeoned"),
        ],
        timeline_steps=[
            TimelineStepBrief(
                step_id="step_1",
                claim=(
                    "Cray struck Breck with an iron mallet, then staged drowning by tying rope "
                    "around the ankles and rolling the body into the pond."
                ),
            ),
            TimelineStepBrief(
                step_id="step_2", claim="The fracture matches the mill-hammer."
            ),
        ],
    )
    assert infer_means(case).id == "means_blunt"


def test_means_uses_hidden_wound_not_mistaken_natural_cause() -> None:
    case = Briefing(
        synopsis="A weak-hearted victim had no obvious wound.",
        locations=[LocationInfo(id="loc_shop", name="Shop")],
        cast=[CastMember(id="char_connie", name="Constance Lund")],
        means_options=[
            MeansOption(id="means_natural", name="Natural causes / Heart failure"),
            MeansOption(id="means_blade", name="Stabbed"),
        ],
        timeline_steps=[
            TimelineStepBrief(
                step_id="step_1",
                claim=(
                    "Constance confronted Lund and stabbed him with a lancet. The hidden wound "
                    "was initially mistaken for cardiac failure."
                ),
            ),
            TimelineStepBrief(
                step_id="step_2", claim="The will supplied the motive for the stabbing."
            ),
        ],
    )
    assert infer_means(case).id == "means_blade"


def test_means_penalizes_staged_natural_death() -> None:
    case = Briefing(
        synopsis="A man with a weak heart died in a greenhouse.",
        locations=[LocationInfo(id="loc_greenhouse", name="Greenhouse")],
        cast=[CastMember(id="char_crane", name="Mrs. Crane")],
        means_options=[
            MeansOption(id="means_natural", name="Natural Causes / Heart Failure"),
            MeansOption(id="means_poison", name="Poisoned"),
        ],
        timeline_steps=[
            TimelineStepBrief(
                step_id="step_1", claim="Crane faced exposure for a forged codicil."
            ),
            TimelineStepBrief(
                step_id="step_2",
                claim=(
                    "Crane prepared digitalis extract, introduced it into the teacup, and served "
                    "it personally, staging the death as natural heart failure."
                ),
            ),
        ],
    )
    assert infer_means(case).id == "means_poison"


def test_means_penalizes_staged_accidental_fall() -> None:
    case = Briefing(
        synopsis="A clockmaker was found at the foot of stairs.",
        locations=[LocationInfo(id="loc_shop", name="Shop")],
        cast=[CastMember(id="char_lunt", name="Mr. Lunt")],
        means_options=[
            MeansOption(id="means_fall", name="Accidental Fall"),
            MeansOption(id="means_poison", name="Poisoned"),
        ],
        timeline_steps=[
            TimelineStepBrief(
                step_id="step_1",
                claim=(
                    "Lunt introduced antimony into wine; Hartley drank it and died hours later; "
                    "Lunt moved the body to stage an accidental fall."
                ),
            )
        ],
    )
    assert infer_means(case).id == "means_poison"


def test_notes_are_grounded_unique_and_contextual() -> None:
    case = briefing()
    clues = [
        ClueText(clue_id="clue_07", text="The knife bears Silas Vane's monogram."),
        ClueText(clue_id="clue_07", text="duplicate"),
    ]
    notes = build_evidence_notes(clues, infer_culprit(case), infer_means(case))
    assert len(notes) == 1
    assert notes[0]["clue_id"] == "clue_07"
    assert "ownership" in notes[0]["note"]


def test_explanation_uses_timeline_and_respects_word_limit() -> None:
    case = briefing()
    explanation = build_process_explanation(
        case,
        infer_culprit(case),
        infer_means(case),
        [ClueText(clue_id="clue_S2", text="Silas confessed to the stabbing.")],
        max_words=45,
    )
    assert "Silas Vane" in explanation
    assert "midnight" in explanation
    assert "clue_S2" not in explanation
    assert len(explanation.split()) <= 45
