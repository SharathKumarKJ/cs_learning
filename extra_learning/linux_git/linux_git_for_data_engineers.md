# Linux and Git for Data Engineers (Detailed)

## Linux essentials

### 1. File navigation and inspection.
**`ls -lah`**: long listing with human-readable sizes and hidden files. **`tree -L 2`**: visualize directory tree. **`find . -name "*.py" -size +1M`**: locate files by pattern/size — much more powerful than `ls`. **`stat file`**: detailed metadata including inode, permissions, modification times.

### 2. Searching inside files.
**`grep -rn "pattern" path`**: recursive, with line numbers. **`grep -E`** for extended regex, **`grep -F`** for fixed strings (fastest). Prefer **`rg` (ripgrep)** — same syntax, far faster, respects `.gitignore`. For structured search across logs: `rg "ERROR" --json | jq ...`.

### 3. Text processing pipeline.
**`cut -d',' -f2,4`** select CSV columns. **`awk -F',' '{sum+=$3} END {print sum}'`** sum a column. **`sort | uniq -c | sort -rn`** classic frequency-count pipeline. **`sed 's/old/new/g'`** in-place replace (with `-i` for file edit). These compose into surprisingly powerful one-liners for log analysis.

### 4. Compression and archives.
**`tar -czf out.tgz dir/`** create, **`tar -xzf out.tgz`** extract. **`gzip`/`gunzip`** stream compression. **`zstd`** modern, faster and better ratio than gzip — widely supported in Spark/Parquet. **`pigz`** parallel gzip for large files.

### 5. Disk and process inspection.
**`df -h`**: free space per mount. **`du -sh *`**: size per top-level entry, useful for finding bloat. **`top` / `htop` / `glances`**: live process view. **`ps -ef | grep`**: find a process. **`lsof -i :8080`**: which process owns a port. **`netstat -tnlp`** / **`ss -tnlp`**: open ports.

### 6. Permissions and ownership.
**`chmod 644 file`** (rw-r--r--), **`chmod 755 dir`** (rwxr-xr-x). **`chown user:group file`**. Octal = sum of read(4) + write(2) + execute(1) per owner/group/other. Use `umask` to set default permissions for new files.

### 7. SSH and remote work.
**`ssh user@host`**, with `~/.ssh/config` for aliases and per-host keys. **`scp file user@host:/path`**, **`rsync -avzP src/ user@host:/dst/`** (incremental, resumable — preferred over scp for big transfers). **Port forwarding**: `ssh -L 8888:localhost:8888 host` to tunnel a Jupyter/Airflow UI to your laptop.

### 8. Background jobs and schedulers.
**`nohup cmd &`** detach from terminal; **`disown`** to also detach from shell. **`tmux`**/**`screen`** for persistent sessions (essential for long-running CLI jobs). **`cron`** for scheduled jobs (`crontab -e`); for data pipelines, prefer Airflow over cron because of dependency, retry, and observability needs.

### 9. Environment and shell.
**`export VAR=value`** for current shell; persistent in `~/.bashrc`/`~/.zshrc`. **`source .env`** load env vars from a file. **`which python`** vs **`type python`** — `type` also shows aliases and functions. **Always quote variables**: `"$path"` — unquoted, spaces break.

### 10. Cloud CLI tools.
**`aws s3 ls/cp/sync`** (also `aws s3api` for fine-grained), **`gcloud storage cp`** / **`gsutil`**, **`az storage blob upload-batch`**. For piping data: `aws s3 cp s3://b/path - | gunzip | head`. Configure profiles per environment, never share keys via files.

## Git essentials

### 11. Daily workflow.
**`git status`**, **`git add -p`** (stage hunks interactively — review every change before committing), **`git commit -m "msg"`**, **`git push`**. Pull before push: **`git pull --rebase`** keeps history linear vs the merge-commit-spam of plain pull.

### 12. Branching.
**`git checkout -b feature/x`** create + switch; **`git switch feature/x`** modern equivalent. **`git branch -d`** delete merged, **`-D`** force. Convention: short-lived feature branches off `main`, merged via PR after CI green.

### 13. Merging vs rebasing.
**Merge** preserves the actual history with a merge commit — safer for shared branches. **Rebase** replays your commits on top of the target — cleaner history but rewrites your commits, so never rebase a branch others are using. Common pattern: rebase your feature branch onto `main` before opening a PR.

### 14. Resolving conflicts.
Git marks conflicts in files with `<<<<<<<` / `=======` / `>>>>>>>`. Edit, `git add` the resolved file, then `git rebase --continue` or `git commit`. Tools: **`git mergetool`**, VS Code's diff view, **`git diff --conflict=diff3`** for three-way context.

### 15. Inspecting history.
**`git log --oneline --graph --decorate --all`** — the single most useful log command. **`git log -p file`** changes to one file. **`git blame file`** who last changed each line. **`git show <commit>`** full diff of a commit.

### 16. Undoing things safely.
**`git restore file`** discard unstaged changes. **`git restore --staged file`** unstage. **`git reset --soft HEAD~1`** undo last commit but keep changes staged. **`git revert <commit>`** create a new commit that undoes a previous one — preferred on shared branches. **`git reflog`** shows everything HEAD has ever pointed to — life-saver after a botched rebase.

### 17. Stashing.
**`git stash push -m "wip"`** to shelf changes; **`git stash pop`** to bring them back; **`git stash list`** to see all stashes. Use sparingly — long-lived stashes get forgotten; prefer WIP commits on a branch.

### 18. `.gitignore` and large files.
Always commit a `.gitignore` (Python: `.venv`, `__pycache__`, `.env`, notebooks' checkpoints; data: `data/`, `output/`, `*.parquet`). For genuinely large files needed in the repo, use **Git LFS**; for data, store outside git entirely (S3/GCS/ADLS) and reference paths.

### 19. PR-driven workflow.
Branch → push → open PR → CI runs → reviewers comment → push fixes → squash-merge to `main`. **Squash** keeps history clean (one commit per PR). Tag releases (`v1.2.3`) for deployable artifacts. Protect `main`: require reviews, passing CI, signed commits if compliance requires.

### 20. Useful aliases and configs.
`git config --global pull.rebase true`, `git config --global rebase.autosquash true`, `git config --global core.editor "code -w"`. Aliases like `git lg` for the fancy log, `git co` for checkout. Set `user.name` and `user.email` per repo if you contribute personally and professionally on the same machine.
