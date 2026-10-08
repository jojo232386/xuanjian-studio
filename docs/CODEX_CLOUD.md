# Codex Cloud development setup

Use a private, reusable Codex Cloud environment for `jojo232386/xuanjian-studio`.
The source base prepared on 2026-10-08 is `6ce92d3e83cc5db3c402791b6fe432e474570ae8`.

Ask environment setup to install **Python 3.14** and **Node.js 22**, select the
package-manager network preset, and run:

```bash
bash scripts/codex_cloud_setup.sh
bash scripts/codex_cloud_check.sh
```

If Python 3.14 is installed outside PATH, set `XUANJIAN_CLOUD_PYTHON` to that
interpreter when running setup. The scripts refuse a different Python or Node
major/minor version rather than silently changing the supported toolchain.
They reuse a matching `.venv`; an incompatible existing environment must be
handled separately, without deleting it automatically.

Record setup as the environment's Install script. The Start skill should run
`bash scripts/codex_cloud_check.sh` for acceptance and, only when a task needs
the application, run `.venv/bin/python backend/server.py` on
`127.0.0.1:8788` with a disposable `XUANJIAN_DATA_DIR`. Do not start a public
service or copy personal journals, backups, WebDAV tokens or AI provider keys.

Publish after the frontend build and all Linux source tests pass. Start a new
task from the published environment and repeat the check to verify the saved
setup. A prepared script, GitHub branch or successful check in another workspace
is not proof that an account environment has been published.

## Acceptance scope

The local Linux preparation result is recorded in `CODEX_CLOUD_VALIDATION.json`:
frontend build passed and 128 source tests passed. Account environment publishing
and verification from a fresh Cloud task are still pending authentication.

The check runs the complete source suite, including HTTP and sync contracts,
and excludes only `tests/test_macos_client_app_e2e.py`. Record the exclusion as
**NOTRUN**. Apple Silicon packaging, signing and a clean real Mac's Gatekeeper
first launch remain separate acceptance gates. Do not mark them passed from
Linux results.

## Tradeoffs and recovery

The cloud environment allows development while the original Mac is unavailable.
Its prepared filesystem must be republished when setup changes. Preserve
important changes in Git; saved task state does not replace a repository or a
backup. Reusing the setup avoids dependency installation in each task, but uses
the account's existing Codex allowance.

This addition does not replace the local-first desktop app with a hosted app.
To stop using the setup, select the original main branch; local user data and
the existing runtime were not moved.
