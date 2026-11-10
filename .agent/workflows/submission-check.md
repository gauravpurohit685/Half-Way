# /submission-check Workflow

## Purpose
Pre-flight audit for Reactive Omni Buildathon submission via DoraHacks.

## Mandatory Requirements
- [ ] Public Git repository with MIT License.
- [ ] Clean commit history demonstrating continuous development during buildathon window.
- [ ] Zero secrets leaked (`gitleaks detect --source . -v` passes cleanly).
- [ ] Verified contracts deployed to Reactive Lasna (5318007), Base Sepolia (84532), and Unichain Sepolia (1301).
- [ ] At least 3 complete real cross-chain loop transaction sets recorded with explorer links and verified hashes.
- [ ] Accurate latency benchmark tables documented in `docs/LATENCY.md` and `README.md`.
- [ ] Architecture diagram (Mermaid) and 10-minute reproduction guide present in `README.md`.
- [ ] Demo video storyboard prepared (< 3 minutes).
- [ ] DoraHacks submission fields ready.
