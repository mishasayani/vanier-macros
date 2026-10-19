# Vanier Macros

A personal macro tracker for Gather, the Place Vanier dining hall at UBC. It runs as a website you add to your iPhone Home Screen.

- **The menu updates itself.** Every morning a GitHub Action pulls the Gather menu from UBC Nutrislice (3 days back, 2 weeks ahead) and rebuilds `menu.json`.
- **Macros are estimates.** Nutrislice has no nutrition data for Vanier. New foods get estimates from Claude, which are added to `scripts/estimates.txt`. You can correct any food in the app, and it remembers your numbers.
- **Your log stays on your phone.** Goals, logged food and saved foods live in the phone's browser storage, and nothing is uploaded. Use **Trends → Backup** to save a copy.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole app |
| `menu.json` | Menus and macro estimates (generated) |
| `scripts/build_menu.py` | Builds `menu.json`; `--estimate` asks Claude about new foods |
| `scripts/estimates.txt` | `id\|kcal\|protein\|carbs\|fat\|serving` for every food seen so far |
| `.github/workflows/refresh-menu.yml` | The daily refresh job |
| `sw.js`, `manifest.webmanifest`, icons | Home Screen app and offline support |

## Setup

1. Add a repository secret named `ANTHROPIC_API_KEY` (Settings → Secrets and variables → Actions).
2. Turn on GitHub Pages from the `main` branch, root folder.
3. To refresh by hand: Actions → Refresh Vanier menu → Run workflow.
