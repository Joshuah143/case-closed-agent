# Hackathon operating brief

Source: the organizer brief and live Case Closed documentation, checked June 27, 2026.

## Environment

- API: <https://railtracks-case-closed.azurewebsites.net/>
- Practice seeds: `S001`–`S006`
- Scored seeds: `H001`–`H005`
- Deadline shown by the live site: July 3, 2026 at midnight ET
- Team: Himmens
- The private bearer token is intentionally not stored in this repository.

## Score

- Correct culprit: 35%
- Evidence notes: 30%
- Process explanation: 15%
- Correct means: 10%
- Efficiency bonus: up to 10%

Evidence notes are embedding-scored with an x² curve. The narrative is embedding-scored with an x³ curve. Practice experiments established that every discoverable clue must receive a note in practice, despite documentation suggesting non-key clues are ignored.

## Submission rules used

- Practice seeds return component scores and permit unlimited sessions.
- Scored seeds permit unlimited reconnaissance sessions.
- Scored results remain hidden until judging.
- The server currently enforces exactly one commit per team on each hidden seed. A later attempt returns
  `403 Hidden seeds allow only 1 submission per team. Your submission stands.` This supersedes
  the live site's stale five-submission wording.
- The implementation protects every hidden commit behind explicit confirmation flags.
- All five scored seeds must receive a completed run.

## Verified submission state

All five scored seeds returned `accepted=true` on June 27, 2026. The public H001–H002 leaderboard then reported:

1. Himmens — `1.414015`
2. Guan-test — `1.392244`
3. logans-awesome-team — `0.705192`
