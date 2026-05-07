# Publish Checklist

Run these checks before the first GitHub push.

## 1. Confirm `.env` is ignored and not tracked

```bash
git check-ignore -v .env
git ls-files .env
git status --ignored
```

If `.env` ever appears in `git ls-files`, remove it from the index only:

```bash
git rm --cached .env
```

## 2. Scan the repo for secrets

PowerShell:

```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern 'sk-[A-Za-z0-9]{20,}|OPENAI_API_KEY|api[_-]?key|secret|token'
```

Git history check without printing file contents:

```bash
git rev-list --all | ForEach-Object { git grep -I -l "sk-" $_ }
```

If that history command prints anything, stop and clean the local history before pushing.

## 3. Verify the app still works

```bash
pytest -q
cd frontend
npm run build
cd ..
docker compose build
```

Optional route smoke test:

```bash
python -c "from fastapi.testclient import TestClient; from app.main import app; client = TestClient(app); print(client.get('/health').json())"
```

## 4. Review exactly what will be published

```bash
git status
git diff --stat
git ls-files
```

## 5. Safe first commit / push sequence

```bash
git add .
git status
git commit -m "feat(app): initial commit — natural-language real estate price estimator"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

## 6. If a secret was committed locally before any push

Do not push yet. Rewrite the local history first, then force-push only to the brand-new remote if needed.

Typical local-only cleanup flow:

```bash
git log --stat
git rebase -i --root
```

Drop or edit the bad commit, remove the secret, re-run the checks above, then push.
