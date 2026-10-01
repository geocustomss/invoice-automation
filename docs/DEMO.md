# Demo and screenshot plan

## 1. Record a GIF / Loom of the whole flow
```bash
bash demo.sh       # prints each command, pauses, runs it (PAUSE=0 bash demo.sh for an instant run)
```
Record it with any of: Loom (also good for the walkthrough video), [asciinema](https://asciinema.org) + `agg` to make a GIF,
[ScreenToGif](https://www.screentogif.com) (Windows) or [Kap](https://getkap.co) (macOS). Terminal tips: dark theme,
font size 18+, ~100 columns wide, short prompt (`export PS1='$ '`), and no personal paths or API keys on screen.

## 2. Hero screenshot
Capture the decision table (post / review / reject) next to `exceptions.csv` showing the human-readable reasons.

Save as `docs/demo.png` (or `docs/demo.gif`) and add this under the first paragraph of the README:
```markdown
![demo](docs/demo.gif)
```

## 3. Things to point at while narrating
- Eight invoices: four post, two review, two reject, each for a different reason.
- The model extracts; plain code decides. Point at `validate.py`.
- Approved invoices become QuickBooks-style rows with an auto-picked account.

## 4. Before you publish
If you can, add 3-5 realistic (fake) PDF-derived invoices of your own to show it handling messier text.
