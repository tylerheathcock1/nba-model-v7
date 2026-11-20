# v7 daily run: instructions for the scheduled Claude session

Sheet: **NBA_Model_v7**, spreadsheet ID `1yF6e4uI1_0HjkxcBDCMgmjW2dlzjwMyAZSvUPmQtF3c`.
Repo: `tylerheathcock1/nba-model-v7`, branch `main`.
`RUN` is `morning` or `pretip`; the prompt that started the session says which.

**Rules.**
- This run only logs and writes the v7 sheet. It never places bets, never touches NBA_Model_v5 or v6, and never changes settings in `v7/config.py`.
- If a step fails, finish what you can. If Sheets access works, put a one-line note in `'Read Me'!A30` saying what failed, with the time in Phoenix.

## Steps

1. **Get the code.**
   - The repo should already be checked out, because it is one of the routine's repository sources. Look for `nba-model-v7` in or next to the working directory.
   - If it isn't there, try `add_repo` with owner `tylerheathcock1`, repo `nba-model-v7`, access `push`, then clone it.
   - If neither works, stop and report: "repo not attached to this routine". Without the repo the run can't save its data.
   - Run `pip install -q -r requirements.txt`.

2. **Run the model.** From the repo root:
   ```
   python -m v7.run RUN
   ```
   This pulls new ESPN box scores, grades earlier Pick Log rows, projects today and logs one row per game. It prints:
   - `FIRST_TIP_PHX`: the first tip time today.
   - `PRETIP_RUN_PHX`: the time for the pre-tip run, one hour before first tip.

3. **Update the sheet.** If this session has no Google Sheets tools (`mcp__Google_Sheets__*`), skip this step and say so in the final reply. The data is still saved in step 4, and the next run that does have Sheets access writes the Pick Log, including this run's rows.

   Otherwise, for each tab below:
   - Clear `'<Tab>'!A1:Z2000` with `batch_clear_values`.
   - Write the JSON printed by `python -m v7.sheetrows <key>` to `'<Tab>'!A1` with `update_values`. Pass the values exactly as printed.

   | Tab | key |
   |---|---|
   | Slate | slate |
   | Scorecard | scorecard |
   | Pick Log | picklog |
   | Players | players |

   On the Players tab, leave out the first column (`date`) of every row except the title row.

4. **Save the data.**
   - Commit everything under `data/` with the message `v7 RUN run YYYY-MM-DD`.
   - Push to `main` with `git push origin main`. If the push is rejected, pull with rebase first.

5. **Pre-tip timing.** Nothing to do. The pre-tip run is its own routine and fires daily at 3:28 PM Phoenix. Games that have already tipped are skipped automatically.

6. **Finish.** Reply with three or four lines:
   - games logged;
   - leans (each with the line and the v7 gap);
   - the scorecard's `line_moved_toward_model` and beta for `all`;
   - anything that failed.
