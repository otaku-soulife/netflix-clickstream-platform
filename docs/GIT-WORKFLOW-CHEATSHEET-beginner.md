# Git & GitHub Workflow Cheat Sheet (Beginner Friendly)

A step-by-step guide for making a change and getting it into the project safely.
Written for someone brand new to Git/GitHub. Every command says **what it does**,
**when to run it**, and **when you can skip it**.

---

## First, the mental model (read once)

- **Repository ("repo")** = the project folder, tracked by Git.
- **`main` branch** = the official, always-working version. You never edit it directly.
- **Branch** = a private copy where you make changes safely, then propose merging back.
- **Commit** = a saved snapshot of your changes, with a short message.
- **Push** = upload your branch/commits to GitHub (the cloud copy, called `origin`).
- **Pull Request ("PR")** = a request to merge your branch into `main`. Checks run here.
- **CI checks** = robots that automatically test your change before it can merge.

**The loop:**
```
sync main -> make a branch -> edit files -> (local checks) -> commit ->
push -> open PR -> checks pass -> merge -> sync main again
```

---

## Step 1 - Get the latest `main`

**What:** Start from the newest version so you don't work on stale files.

```powershell
git checkout main
git pull
```

**When to run:** Every time you start a new piece of work.
**Skip if:** You *just* pulled and nothing has merged since.

---

## Step 2 - Create a branch

**What:** Make your safe workspace for this change.

```powershell
git checkout -b docs/skills-log
```

Name it `type/short-description`. Types: `feat/`, `fix/`, `infra/`, `pipeline/`,
`ml/`, `docs/`, `chore/`.

**When to run:** Once, at the start of each change.
**Skip if:** You already created and are on the branch (check with `git branch`;
the `*` shows where you are).

---

## Step 3 - Make your changes

**What:** Edit, add, or delete files in VS Code (or copy files into the folder).

**When to run:** Always - this is the actual work.
**Skip if:** Never.

---

## Step 4 - See what changed

**What:** Check which files Git noticed.

```powershell
git status          # list changed/new files
git status -s       # short form (?? = new, M = modified)
git diff            # line-by-line changes (press q to exit the viewer)
```

**When to run:** Any time you want to confirm what you're about to commit.
**Skip if:** You already know what changed (running it is free, though).

Note: if `git diff` fills the screen with a `:` at the bottom, press **q** to
quit - that's just the scrolling viewer, not an error.

---

## Step 5 - Local checks (ONLY for the file types you changed)

**What:** Run the same checks CI will run, so your PR passes the first time.
**You only run the check that matches what you edited.**

**If you edited Terraform (`.tf` in `infra/`):**
```powershell
cd infra
terraform fmt
terraform validate
cd ..
```

**If you edited Python (`.py`):**
```powershell
ruff format .
ruff check .
```

**DECISION TABLE - which checks do I run?**

| What you changed           | terraform fmt/validate | ruff |
|----------------------------|:----------------------:|:----:|
| Only docs / Markdown (.md) | skip                   | skip |
| Python files (.py)         | skip                   | RUN  |
| Terraform files (.tf)      | RUN                    | skip |
| Both .py and .tf           | RUN                    | RUN  |

**When to run:** Only when you changed the matching file type.
**Skip if:** Docs-only (Markdown) or anything that isn't Terraform/Python -
skip both and go to Step 6.

---

## Step 6 - Stage your changes

**What:** Tell Git which changes to include in the next commit.

```powershell
git add .            # stage everything you changed
git add docs/        # or a specific folder/file
```

`git add` works the same for brand-new files and edited files.

**When to run:** Always, right before committing.
**Skip if:** Never (Git won't commit anything that isn't staged).

---

## Step 7 - Commit

**What:** Save a snapshot with a message describing the change.

```powershell
git commit -m "docs: add skills log"
```

Start the message with the type: `feat:`, `fix:`, `infra:`, `pipeline:`,
`ml:`, `docs:`, `chore:`.

**When to run:** After staging, when you've finished a logical chunk.
**Skip if:** Never - this is how work is saved.

---

## Step 8 - Push to GitHub

**What:** Upload your branch so GitHub can see it.

```powershell
git push -u origin docs/skills-log   # first push of a new branch
git push                             # later pushes on the same branch
```

**When to run:** After committing, when ready to open/update a PR.
**Skip if:** You want to keep committing locally a bit longer first.

---

## Step 9 - Open a Pull Request

**What:** Propose merging into `main`; this starts the CI checks.

```powershell
gh pr create --fill --base main
gh pr view --web
```

**When to run:** Once per branch, after your first push.
**Skip if:** A PR for this branch already exists (new pushes update it automatically).

---

## Step 10 - Watch the checks

**What:** Wait for the robots (lint, terraform) to pass.

```powershell
gh pr checks --watch
```

Green = good. If red: `gh run view --log-failed` shows why.

**When to run:** After opening/updating a PR.
**Skip if:** Never - checks must be green to merge.

---

## Step 11 - Merge

**What:** Fold your change into `main`.

```powershell
gh pr merge --squash --delete-branch
```

**When to run:** After all checks are green (and, on a team, approved).
**Skip if:** Checks are still failing - fix them first.

---

## Step 12 - Sync your local `main`

**What:** Bring your computer's `main` up to date with the merge.

```powershell
git checkout main
git pull
```

**When to run:** Right after merging, before the next change.
**Skip if:** You're immediately branching again and will pull then.

---

## Quick reference - the happy path (docs-only change)

```powershell
git checkout main; git pull
git checkout -b docs/my-change
# ...edit files...
git add .
git commit -m "docs: describe the change"
git push -u origin docs/my-change
gh pr create --fill --base main
gh pr checks --watch
gh pr merge --squash --delete-branch
git checkout main; git pull
```

---

## Common beginner snags

- **Stuck on a screen with `:` at the bottom** (after `git diff`/`git log`):
  press **q** to quit the viewer.
- **"not a git repository"**: wrong folder - `cd` into the repo folder first.
- **`git checkout -b` says "invalid"**: you forgot the branch name after `-b`.
- **`git status` shows only a folder name** (e.g. `producer/`): normal - Git
  collapses a new folder; the files inside are there.
- **PR says "Review required" and you're solo**: set required approvals to 0 in
  branch protection (you can't approve your own PR).

---

## Glossary

- **origin** = the GitHub (cloud) copy of your repo.
- **staged** = marked to be included in the next commit (via `git add`).
- **squash merge** = combine your branch's commits into one clean commit on `main`.
- **CI** = Continuous Integration; the automated checks that run on your PR.
