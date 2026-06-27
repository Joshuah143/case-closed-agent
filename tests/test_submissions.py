from case_closed.submissions import NOTE_GLOSSES, PLANS


def test_every_plan_has_exactly_one_note_per_expected_clue() -> None:
    assert set(NOTE_GLOSSES) == set(PLANS)
    for seed_id, plan in PLANS.items():
        assert frozenset(NOTE_GLOSSES[seed_id]) == plan.expected_clues


def test_scoring_artifacts_stay_below_verbosity_targets() -> None:
    for seed_id, plan in PLANS.items():
        assert len(plan.explanation.split()) <= 140, seed_id
        for clue_id, note in NOTE_GLOSSES[seed_id].items():
            assert len(note.split()) <= 120, (seed_id, clue_id)


def test_plans_use_one_budget_unit_per_action() -> None:
    budgets = {"H001": 60, "H002": 60, "H003": 65, "H004": 65, "H005": 70}
    for seed_id, plan in PLANS.items():
        assert budgets[seed_id] - len(plan.actions) == plan.expected_actions_remaining
