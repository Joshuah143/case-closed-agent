"""Multi-session, no-commit reconnaissance for discovering guarded clue chains."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field

import requests
from detective_client import ClueText, GameError

from .solver import CaseSolver


@dataclass
class ReconResult:
    seed_id: str
    briefing: dict = field(default_factory=dict)
    locations: dict[str, dict] = field(default_factory=dict)
    inventory: set[str] = field(default_factory=set)
    sweep_actions_used: int = 0
    clues: dict[str, ClueText] = field(default_factory=dict)
    accepted_pairs: list[tuple[str, str]] = field(default_factory=list)
    attempted_pairs: set[tuple[str, str]] = field(default_factory=set)
    sessions_used: int = 0


class Reconnaissance:
    """Exhaust presentation combinations across disposable, non-committing sessions."""

    def __init__(self, *, verbose: bool = True) -> None:
        self.verbose = verbose

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)

    @staticmethod
    def _present(solver: CaseSolver, character_id: str, ref_id: str) -> bool:
        location = solver.character_locations.get(character_id)
        if not location or not solver._travel_to(location):
            return False
        observation = None
        for attempt in range(3):
            time.sleep(0.4)
            try:
                observation = solver.client.present(character_id, ref_id)
                break
            except GameError:
                return False
            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if status != 429 and status < 500:
                    raise
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        assert observation is not None
        solver._remember_clues(observation.revealed, f"recon:{character_id}:{ref_id}")
        return observation.accepted

    def run(
        self,
        seed_id: str,
        *,
        max_sessions: int = 4,
        reserve_actions: int = 4,
        only_characters: list[str] | None = None,
    ) -> ReconResult:
        result = ReconResult(seed_id=seed_id)
        for session_number in range(1, max_sessions + 1):
            solver = CaseSolver(verbose=False)
            investigation = solver.investigate(seed_id, present_limit=0)
            result.sessions_used = session_number
            result.briefing = solver.briefing.model_dump()
            result.locations = {
                location_id: {
                    "name": memory.name,
                    "exits": sorted(memory.exits),
                    "characters": sorted(memory.characters),
                    "searchable": memory.searchable,
                }
                for location_id, memory in solver.locations.items()
            }
            result.inventory.update(solver.inventory)
            result.sweep_actions_used = solver.action_budget - investigation.actions_remaining
            result.clues.update({clue.clue_id: clue for clue in investigation.clues})
            self._log(
                f"session {session_number}: sweep found {len(solver.clues)} clues; "
                f"{solver.client.actions_remaining} actions remain"
            )

            # Replay previously discovered unlocks so dependent guarded clues are available.
            for character_id, ref_id in result.accepted_pairs:
                if ref_id not in solver.client.inventory and ref_id not in solver.client.clues_seen:
                    continue
                self._present(solver, character_id, ref_id)

            cast_ids = list(
                dict.fromkeys(
                    [member.id for member in solver.briefing.cast]
                    + sorted(solver.character_locations)
                )
            )
            if only_characters:
                cast_ids = [character_id for character_id in cast_ids if character_id in only_characters]
            culprit_id = investigation.culprit.id
            ordered_characters = (
                [culprit_id, *[cid for cid in cast_ids if cid != culprit_id]]
                if culprit_id in cast_ids
                else cast_ids
            )
            made_attempt = False
            while solver.client.actions_remaining > reserve_actions:
                refs = sorted(solver.client.inventory | solver.client.clues_seen)
                pending = [
                    (character_id, ref_id)
                    for character_id in ordered_characters
                    for ref_id in refs
                    if (character_id, ref_id) not in result.attempted_pairs
                    and (character_id, ref_id) not in result.accepted_pairs
                ]
                if not pending:
                    break
                character_id, ref_id = pending[0]
                result.attempted_pairs.add((character_id, ref_id))
                made_attempt = True
                before = set(solver.clues)
                accepted = self._present(solver, character_id, ref_id)
                if accepted:
                    result.accepted_pairs.append((character_id, ref_id))
                    new_ids = sorted(set(solver.clues) - before)
                    self._log(f"  ACCEPT {ref_id} -> {character_id}: {new_ids}")
                    result.clues.update(
                        {clue_id: solver.clues[clue_id] for clue_id in new_ids}
                    )

            result.clues.update(solver.clues)
            self._log(
                f"session {session_number}: {len(result.attempted_pairs)} pairs tested, "
                f"{len(result.accepted_pairs)} accepted, {len(result.clues)} clues total"
            )
            refs = set(solver.client.inventory) | set(result.clues)
            possible_pairs = {(character_id, ref_id) for character_id in cast_ids for ref_id in refs}
            completed = possible_pairs <= (result.attempted_pairs | set(result.accepted_pairs))
            if completed or not made_attempt:
                break
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Exhaust clue unlocks without committing")
    parser.add_argument("seed")
    parser.add_argument("--sessions", type=int, default=4)
    parser.add_argument("--character", action="append", dest="characters")
    args = parser.parse_args()
    result = Reconnaissance().run(
        args.seed.upper(),
        max_sessions=max(1, args.sessions),
        only_characters=args.characters,
    )
    output = {
        "seed_id": result.seed_id,
        "sessions_used": result.sessions_used,
        "briefing": result.briefing,
        "locations": result.locations,
        "inventory": sorted(result.inventory),
        "sweep_actions_used": result.sweep_actions_used,
        "accepted_pairs": [list(pair) for pair in result.accepted_pairs],
        "attempted_pair_count": len(result.attempted_pairs),
        "clues": {clue_id: clue.text for clue_id, clue in result.clues.items()},
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
