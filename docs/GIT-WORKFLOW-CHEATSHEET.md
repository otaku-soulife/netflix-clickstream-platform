# Git & GitHub Workflow Cheat Sheet

The exact commands and flow we use on this project: trunk-based development -
`main` is always deployable, every change goes through a branch, a pull request,
and passing CI before it merges.

## The loop at a glance

```
sync main  ->  branch  ->  edit  ->  local checks  ->  commit  ->  push
   ->  open PR  ->  CI runs (terraform + lint)  ->  merge  ->  sync main
```

---

## 1. Start work - sync and branch

```powershell
git checkout main            # switch to main
git pull                     # get the latest
git checkout -b feat/my-thing   # create + switch to a new branch
```

Branch name prefixes: `feat/`, `fix/`, `infra/`, `pipeline/`, `ml/`, `docs/`, `chore/`.

## 2. See what changed

```powershell
git status                   # what's modified / staged
git diff                     # exact line changes (not yet staged)
```

## 3. Local checks BEFORE pushing (same checks CI runs)

```powershell
# Terraform (run inside infra/)
cd infra
terraform fmt                # auto-format .tf files
terraform validate           # check config is valid
cd ..

# Python
ruff check .                 # lint
ruff format --check .        # format check
```

## 4. Commit

```powershell
git add .                            # stage all changes
git commit -m "feat: short summary"  # commit with a Conventional Commit message
```

Commit message prefixes: `feat:`, `fix:`, `infra:`, `pipeline:`, `ml:`, `docs:`, `chore:`.

## 5. Push the branch

```powershell
git push -u origin feat/my-thing     # first push of a new branch (-u sets upstream)
git push                             # subsequent pushes on the same branch
```

## 6. Open a pull request

```powershell
gh pr create --fill --base main      # create PR, auto-filling title/body from commits
gh pr view --web                     # open the PR in the browser
```

## 7. Watch / validate CI checks

```powershell
gh pr checks --watch                 # live status of the PR's checks
gh run list --branch feat/my-thing --limit 1   # find the latest run
gh run view --log-failed             # show logs of only the failed steps
gh run rerun <run-id> --failed       # re-run only the failed jobs
gh run watch                         # follow the most recent run live
```

A green `terraform` check = plan ran and authenticated to Azure via OIDC.
A green `lint` check = Python passed (or was skipped if no .py files changed).

## 8. Merge (after checks are green)

```powershell
gh pr merge --squash --delete-branch # squash commits into one, delete the branch
```

Merging to `main` triggers the deploy steps (e.g. `terraform apply`).

## 9. Sync local main after merge

```powershell
git checkout main
git pull
```

---

## Handy extras

```powershell
git branch                   # list local branches
git checkout main            # switch back to main
git checkout <branch>        # switch to an existing branch
git log --oneline -10        # recent commit history
git restore <file>           # discard local changes to a file
gh repo view --web           # open the repo in the browser
gh pr list                   # list open PRs
gh secret list               # list repo Actions secrets
```

---

## What the CI workflows do (in `.github/workflows/`)

**terraform.yml** - runs when `infra/**` changes.
- On a PR: `fmt -check`, `init`, `validate`, `plan` (preview only).
- On merge to `main`: also `apply` (builds the infrastructure).
- Authenticates to Azure with OIDC (no stored password).

**lint.yml** - runs when any `*.py` changes.
- `ruff check` (lint) and `ruff format --check` (formatting).

Required status checks + branch protection on `main` mean nothing merges unless
these are green.

---

## Branch protection reminders

- No direct pushes to `main` - always branch + PR.
- Required checks must pass before merge.
- Solo project: approvals set to 0 (you can't approve your own PR); on a team,
  a reviewer approves instead.
