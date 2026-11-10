# Auto-Accept Safety Rules

1. **Testnets Only:**
   - Allowed chain IDs:
     - 11155111 (Ethereum Sepolia)
     - 84532 (Base Sepolia)
     - 1301 (Unichain Sepolia)
     - 5318007 (Reactive Lasna)
   - Every script, test, deployment, and frontend connection must validate chain IDs against this explicit whitelist and reject any other network.
   - Mainnet RPCs and deployments are strictly prohibited.

2. **Spending Limits & Reserves:**
   - Always maintain at least 0.03 ETH balance on Base Sepolia and Unichain Sepolia.
   - Always maintain at least 10 lREACT balance on Reactive Lasna.
   - Single transaction limit: Maximum 0.02 ETH or 5 lREACT. Do not exceed without explicit approval.
   - Never bridge or convert Sepolia ETH to lREACT without asking.

3. **Audit Log:**
   - Every on-chain transaction or state-modifying action must be immediately appended to `docs/AGENT_LOG.md` with: timestamp, chain ID/name, purpose, tx hash, and amount spent.

4. **Secrets & Security:**
   - Never print, echo, commit, or leak `.env` values, keystores, private keys, or the password file `~/.foundry/.halfway-pass`.
   - Run `gitleaks detect --source . -v` before every git commit.
   - Always verify `git status --short` before staging files; `.env` must never be tracked.

5. **No Destructive Operations:**
   - No `sudo`, no `rm -rf` outside this repository, no wildcard root deletions.
   - No `curl | bash`.
   - No `git push --force` or destructive resets on pushed branches.
   - Never modify `~/.bashrc`, `~/.ssh`, global git config, or keystore files.

6. **Supply Chain:**
   - Pin exact dependency versions. Avoid releases newer than 14 days. No unvetted, obscure packages.

7. **Questions & Blockers:**
   - Record open design questions in `docs/QUESTIONS.md`. If blocked, diagnose and stop rather than retrying repetitive failures.

8. **Rate Limiting & RPC Hygiene:**
   - Free tier Alchemy limits must be respected. Use fallback public RPCs, exponential backoff, caching, and reasonable polling intervals.

9. **Process Management:**
   - Run dev servers and daemons in the background with piped logs, never blocking terminal sessions.

10. **Commits:**
    - Small, frequent, Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`). Tag milestones.
