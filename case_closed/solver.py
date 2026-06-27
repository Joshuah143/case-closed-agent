"""Action-efficient deterministic investigation engine."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import re
import time
from typing import Any

import requests
from detective_client import (
    Briefing,
    CastMember,
    ClueText,
    DetectiveClient,
    GameError,
    LocationObservation,
    MeansOption,
    MoveObservation,
    PresentObservation,
)

from .reasoning import (
    build_evidence_notes,
    build_process_explanation,
    infer_culprit,
    infer_means,
)


@dataclass
class LocationMemory:
    location_id: str
    name: str = ""
    exits: set[str] = field(default_factory=set)
    characters: set[str] = field(default_factory=set)
    searchable: bool = False
    visited: bool = False
    searched: bool = False


@dataclass
class InvestigationResult:
    seed_id: str
    culprit: CastMember
    means: MeansOption
    clues: list[ClueText]
    inventory: set[str]
    actions_remaining: int
    evidence_notes: list[dict[str, str]]
    process_explanation: str
    commit_result: dict[str, Any] | None = None


class CaseSolver:
    """Explore the map, collect grounded evidence, and submit the disclosed verdict."""

    def __init__(self, client: DetectiveClient | None = None, *, verbose: bool = True) -> None:
        self.client = client or DetectiveClient()
        self.verbose = verbose
        self.briefing: Briefing | None = None
        self.action_budget = 0
        self.locations: dict[str, LocationMemory] = {}
        self.current_location = ""
        self.clues: dict[str, ClueText] = {}
        self.inventory: set[str] = set()
        self.interviewed: set[str] = set()
        self.character_locations: dict[str, str] = {}
        self.clue_sources: dict[str, str] = {}
        self.item_names: dict[str, str] = {}
        self.failed_edges: set[tuple[str, str, tuple[str, ...]]] = set()
        self.action_log: list[str] = []

    def _log(self, message: str) -> None:
        self.action_log.append(message)
        if self.verbose:
            print(message)

    def _retry(self, operation: Any, *args: Any, **kwargs: Any) -> Any:
        """Retry transient throttling and server errors with bounded backoff."""
        for attempt, delay in enumerate((0.5, 1.0, 2.0, 4.0), start=1):
            try:
                return operation(*args, **kwargs)
            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status != 429 and (status is None or status < 500):
                    raise
                self._log(f"RETRY HTTP {status} attempt {attempt}")
                time.sleep(delay)
        return operation(*args, **kwargs)

    def _remember_clues(self, clues: list[ClueText], source: str) -> None:
        for clue in clues:
            if clue.clue_id not in self.clues:
                self._log(f"  + {clue.clue_id} from {source}: {clue.text}")
            self.clues[clue.clue_id] = clue
            self.clue_sources[clue.clue_id] = source

    def _observe(self, obs: LocationObservation | MoveObservation) -> None:
        memory = self.locations.setdefault(obs.location_id, LocationMemory(obs.location_id))
        memory.name = obs.name
        memory.exits.update(obs.exits)
        memory.characters = set(obs.characters_present)
        memory.searchable = obs.searchable
        memory.visited = True
        self.current_location = obs.location_id
        for character_id in obs.characters_present:
            self.character_locations[character_id] = obs.location_id

    def _process_current_location(self) -> None:
        memory = self.locations[self.current_location]
        if memory.searchable and not memory.searched:
            obs = self._retry(self.client.search)
            memory.searched = True
            self._log(f"SEARCH {memory.location_id} ({obs.actions_remaining} left)")
            for evidence in obs.found:
                if evidence.item_id:
                    self.inventory.add(evidence.item_id)
                    self.item_names[evidence.item_id] = evidence.name
                    self._log(f"  + item {evidence.item_id}: {evidence.name}")
                self._remember_clues(evidence.yields, evidence.name)
        for character_id in sorted(memory.characters - self.interviewed):
            obs = self._retry(self.client.interview, character_id)
            self.interviewed.add(character_id)
            self._log(f"INTERVIEW {character_id} ({obs.actions_remaining} left)")
            self._remember_clues(obs.said, f"interview:{character_id}")

    def _edge_blocked(self, left: str, right: str) -> bool:
        signature = tuple(sorted(self.inventory | set(self.clues)))
        return (left, right, signature) in self.failed_edges

    def _shortest_path(self, goals: set[str]) -> list[str] | None:
        queue: deque[tuple[str, list[str]]] = deque([(self.current_location, [])])
        seen = {self.current_location}
        while queue:
            node, path = queue.popleft()
            if node in goals:
                return path
            for neighbor in sorted(self.locations.get(node, LocationMemory(node)).exits):
                if neighbor in seen or self._edge_blocked(node, neighbor):
                    continue
                seen.add(neighbor)
                queue.append((neighbor, [*path, neighbor]))
        return None

    def _move_one(self, destination: str) -> bool:
        origin = self.current_location
        try:
            obs = self._retry(self.client.move, destination)
        except GameError as exc:
            signature = tuple(sorted(self.inventory | set(self.clues)))
            self.failed_edges.add((origin, destination, signature))
            self._log(f"BLOCKED {origin} -> {destination}: {exc}")
            return False
        self._observe(obs)
        self._log(f"MOVE {origin} -> {destination} ({obs.actions_remaining} left)")
        return True

    def _travel_to(self, destination: str) -> bool:
        while self.current_location != destination:
            path = self._shortest_path({destination})
            if not path or not self._move_one(path[0]):
                return False
        return True

    def _present_with_chase(
        self, character_id: str, ref_id: str, *, max_chases: int = 3
    ) -> PresentObservation | None:
        """Present evidence, following a scheduled character when the API locates them."""
        for _ in range(max_chases + 1):
            try:
                return self._retry(self.client.present, character_id, ref_id)
            except GameError as exc:
                match = re.search(r"currently at '([^']+)'", str(exc))
                if not match:
                    self._log(f"PRESENT ERROR {ref_id} -> {character_id}: {exc}")
                    return None
                destination = match.group(1)
                self.character_locations[character_id] = destination
                self._log(f"CHASE {character_id} -> {destination}")
                if not self._travel_to(destination):
                    return None
        return None

    def sweep(self) -> None:
        """Visit every reachable location with nearest-neighbor graph routing."""
        assert self.briefing is not None
        all_locations = {location.id for location in self.briefing.locations}
        while True:
            self._process_current_location()
            unvisited = {loc for loc in all_locations if not self.locations[loc].visited}
            if not unvisited:
                return
            path = self._shortest_path(unvisited)
            if not path:
                self._log(f"UNREACHABLE: {', '.join(sorted(unvisited))}")
                return
            self._move_one(path[0])

    def unlock(self, culprit: CastMember, *, present_limit: int = 16) -> None:
        """Follow the common witness-identification then culprit-confrontation chain."""
        attempts = 0
        attempted: set[tuple[str, str]] = set()
        cast_ids = [member.id for member in self.briefing.cast] if self.briefing else []
        witness_signals = {
            "saw",
            "seen",
            "noticed",
            "watched",
            "witness",
            "around",
            "delivered",
            "served",
            "returning",
        }
        witness_scores: list[tuple[int, str]] = []
        for character_id in cast_ids:
            if character_id == culprit.id:
                continue
            character_clues = [
                clue
                for clue_id, clue in self.clues.items()
                if self.clue_sources.get(clue_id) == f"interview:{character_id}"
            ]
            score = sum(
                len(set(clue.text.casefold().split()) & witness_signals)
                for clue in character_clues
            )
            witness_scores.append((score, character_id))
        witness_scores.sort(reverse=True)

        def item_score(item_id: str) -> int:
            text = f"{item_id} {self.item_names.get(item_id, '')}".casefold()
            positive = sum(
                token in text
                for token in ("ledger", "report", "bottle", "will", "receipt", "record", "mallet")
            )
            negative = sum(token in text for token in ("warrant", "key", "permit"))
            return positive * 4 - negative * 3

        ordered_items = sorted(self.inventory, key=item_score, reverse=True)

        # A partial eyewitness usually identifies the culprit when shown a document/item.
        for witness_score, character_id in witness_scores:
            if witness_score <= 0:
                continue
            location = self.character_locations.get(character_id)
            if not location or not self._travel_to(location):
                continue
            for ref_id in ordered_items[:2]:
                if attempts >= present_limit or self.client.actions_remaining <= 8:
                    return
                attempts += 1
                attempted.add((character_id, ref_id))
                obs = self._present_with_chase(character_id, ref_id)
                if obs is None:
                    continue
                self._log(
                    f"PRESENT {ref_id} -> {character_id}: {'accepted' if obs.accepted else 'no'} "
                    f"({obs.actions_remaining} left)"
                )
                self._remember_clues(obs.revealed, f"present to {character_id}")
                if obs.accepted:
                    break

        # Some forensic clues explicitly require a named expert to identify a residue/sample.
        expert_characters: list[str] = []
        for character_id in cast_ids:
            testimony = " ".join(
                clue.text.casefold()
                for clue_id, clue in self.clues.items()
                if self.clue_sources.get(clue_id) == f"interview:{character_id}"
            )
            if any(
                phrase in testimony
                for phrase in ("assist with", "happy to examine", "expert", "analyse", "analyze")
            ):
                expert_characters.append(character_id)
        expert_refs = sorted(
            self.clues.values(),
            key=lambda clue: sum(
                phrase in clue.text.casefold()
                for phrase in (
                    "expert identification",
                    "preliminary",
                    "residue",
                    "sample",
                    "compound",
                )
            ),
            reverse=True,
        )
        for character_id in expert_characters:
            location = self.character_locations.get(character_id)
            if not location or not self._travel_to(location):
                continue
            for evidence in expert_refs[:3]:
                if attempts >= present_limit or self.client.actions_remaining <= 8:
                    return
                attempts += 1
                obs = self._present_with_chase(character_id, evidence.clue_id)
                if obs is None:
                    continue
                self._log(
                    f"EXPERT {evidence.clue_id} -> {character_id}: "
                    f"{'accepted' if obs.accepted else 'no'} ({obs.actions_remaining} left)"
                )
                self._remember_clues(obs.revealed, f"expert {character_id}")
                if obs.accepted:
                    break

        # A culprit's confession is commonly gated by the strongest physical/documentary clue.
        signal_words = {
            "confess",
            "weapon",
            "knife",
            "poison",
            "morphine",
            "arsenic",
            "mallet",
            "hammer",
            "lancet",
            "match",
            "initial",
            "monogram",
            "signed",
            "witness",
            "identified",
        }
        location = self.character_locations.get(culprit.id)
        if not location or not self._travel_to(location):
            return
        culprit_tokens = {token for token in culprit.name.casefold().split() if len(token) > 2}
        timeline_text = " ".join(
            step.claim for step in (self.briefing.timeline_steps if self.briefing else [])
        ).casefold()
        stopwords = {
            "a",
            "an",
            "and",
            "as",
            "at",
            "before",
            "by",
            "for",
            "from",
            "he",
            "her",
            "his",
            "in",
            "into",
            "it",
            "of",
            "on",
            "the",
            "then",
            "this",
            "to",
            "was",
            "when",
            "with",
        }
        timeline_words = set(re.findall(r"[a-z0-9]+", timeline_text)) - stopwords

        def confrontation_score(clue: ClueText) -> int:
            text = clue.text.casefold()
            words = set(re.findall(r"[a-z0-9]+", text)) - stopwords
            score = len(words & signal_words) * 3
            score += len(words & timeline_words) * 2
            score += sum(token in text for token in culprit_tokens) * 2
            source = self.clue_sources.get(clue.clue_id, "")
            if source.startswith("interview:char_"):
                character_role = source.removeprefix("interview:char_")
                if character_role in timeline_words:
                    score += 10
            if any(token in text for token in ("initial", "monogram", "engraved", "personal")):
                score += 20
            if any(token in text for token in ("matches", "matching", "wound", "toxicology")):
                score += 10
            if any(
                token in text
                for token in ("blood", "hair fibres", "hair fibers", "concealed", "residue")
            ):
                score += 20
            if any(token in text for token in ("signed", "handwriting", "authored")):
                score += 8
            if "purchase" in text and any(
                token in text for token in ("tincture", "aconit", "morphine", "arsenic", "poison")
            ):
                score += 30
            if any(
                token in text
                for token in (
                    "asked me to leave",
                    "not his job",
                    "access to",
                    "secretive",
                    "acting strange",
                    "did not leave",
                )
            ):
                score += 12
            if source.startswith("present to"):
                score += 6
            if clue.clue_id.casefold().endswith(("s2", "m2")):
                score += 4
            return score

        ranked_clues = sorted(self.clues.values(), key=confrontation_score, reverse=True)
        for clue in ranked_clues:
            pair = (culprit.id, clue.clue_id)
            if pair in attempted:
                continue
            if attempts >= present_limit or self.client.actions_remaining <= 8:
                return
            attempts += 1
            obs = self._present_with_chase(culprit.id, clue.clue_id)
            if obs is None:
                continue
            self._log(
                f"PRESENT {clue.clue_id} -> {culprit.id}: "
                f"{'accepted' if obs.accepted else 'no'} ({obs.actions_remaining} left)"
            )
            self._remember_clues(obs.revealed, f"confront {culprit.id}")
            final_id = any(
                re.search(r"(?:2b|3)$", revealed.clue_id, re.IGNORECASE)
                for revealed in obs.revealed
            )
            final_text = any(
                any(
                    phrase in revealed.text.casefold()
                    for phrase in (
                        "confess",
                        "i did it",
                        "i killed",
                        "i stabbed",
                        "i struck",
                        "i poisoned",
                        "it went wrong",
                    )
                )
                for revealed in obs.revealed
            )
            if final_id or final_text:
                return
            partial_clues = list(obs.revealed) if obs.accepted else []
            if partial_clues:
                bridge_characters = [
                    member.id
                    for member in (self.briefing.cast if self.briefing else [])
                    if member.id != culprit.id
                    and (
                        member.id.removeprefix("char_").casefold() in timeline_words
                        or any(
                            token in timeline_words
                            for token in re.findall(r"[a-z0-9]+", member.name.casefold())
                            if len(token) > 3
                        )
                    )
                ]
                for bridge_character in bridge_characters:
                    bridge_location = self.character_locations.get(bridge_character)
                    if not bridge_location or not self._travel_to(bridge_location):
                        continue
                    bridge_refs = [
                        *partial_clues,
                        clue,
                        *[
                            ClueText(clue_id=item_id, text=self.item_names.get(item_id, item_id))
                            for item_id in ordered_items
                        ],
                    ]
                    for partial_clue in bridge_refs:
                        if attempts >= present_limit or self.client.actions_remaining <= 8:
                            return
                        attempts += 1
                        bridge = self._present_with_chase(
                            bridge_character, partial_clue.clue_id
                        )
                        if bridge is None:
                            continue
                        self._log(
                            f"BRIDGE {partial_clue.clue_id} -> {bridge_character}: "
                            f"{'accepted' if bridge.accepted else 'no'} "
                            f"({bridge.actions_remaining} left)"
                        )
                        self._remember_clues(
                            bridge.revealed, f"bridge via {bridge_character}"
                        )
                        if not bridge.accepted:
                            continue
                        culprit_location = self.character_locations.get(culprit.id)
                        if not culprit_location or not self._travel_to(culprit_location):
                            return
                        for bridge_clue in bridge.revealed:
                            if attempts >= present_limit or self.client.actions_remaining <= 8:
                                return
                            attempts += 1
                            conclusion = self._present_with_chase(
                                culprit.id, bridge_clue.clue_id
                            )
                            if conclusion is None:
                                continue
                            self._log(
                                f"CONCLUDE {bridge_clue.clue_id} -> {culprit.id}: "
                                f"{'accepted' if conclusion.accepted else 'no'} "
                                f"({conclusion.actions_remaining} left)"
                            )
                            self._remember_clues(
                                conclusion.revealed, f"confront {culprit.id}"
                            )
                            if conclusion.accepted:
                                return
                culprit_location = self.character_locations.get(culprit.id)
                if culprit_location:
                    self._travel_to(culprit_location)

    def investigate(
        self,
        seed_id: str,
        *,
        commit: bool = False,
        allow_hidden_commit: bool = False,
        present_limit: int = 16,
    ) -> InvestigationResult:
        if seed_id.upper().startswith("H") and commit and not allow_hidden_commit:
            raise ValueError("Hidden-seed commits require allow_hidden_commit=True")
        session = self._retry(self.client.start_session, seed_id)
        self.briefing = session.briefing
        self.action_budget = session.action_budget
        self.locations = {
            location.id: LocationMemory(location_id=location.id, name=location.name)
            for location in session.briefing.locations
        }
        self._observe(session.observation)
        culprit = infer_culprit(session.briefing)
        means = infer_means(session.briefing)
        self._log(f"VERDICT from timeline: {culprit.id} / {means.id}")
        self.sweep()
        if present_limit:
            self.unlock(culprit, present_limit=present_limit)
            if any(not location.visited for location in self.locations.values()):
                self.sweep()

        clues = list(self.clues.values())
        notes = build_evidence_notes(clues, culprit, means)
        explanation = build_process_explanation(session.briefing, culprit, means, clues)
        commit_result = None
        if commit:
            result = self._retry(
                self.client.commit,
                culprit_id=culprit.id,
                means_id=means.id,
                evidence_notes=notes,
                process_explanation=explanation,
            )
            commit_result = result.model_dump()
            self._log(f"COMMIT score={result.score} actions_remaining={result.actions_remaining}")
        return InvestigationResult(
            seed_id=seed_id,
            culprit=culprit,
            means=means,
            clues=clues,
            inventory=set(self.inventory),
            actions_remaining=self.client.actions_remaining,
            evidence_notes=notes,
            process_explanation=explanation,
            commit_result=commit_result,
        )
