# Macro Tracker

A personal macro tracker for Gather, the Place Vanier dining hall at UBC. It runs as a website you add to your iPhone Home Screen.

- **The menu updates itself.** Every morning a GitHub Action pulls the Gather menu from UBC Nutrislice (3 days back, 2 weeks ahead) and rebuilds `menu.json`.
- **Macros are estimates.** Nutrislice has no nutrition data for Vanier. Estimates live in `scripts/estimates.txt` and get refined from meal photos in a Claude chat (see `CLAUDE.md`). You can also correct any dish in the app, and it remembers your numbers.
- **Your log stays on your phone.** Goals, logged food and saved foods live in the phone's browser storage, and nothing is uploaded. Use **Trends → Backup** to save a copy.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole app |
| `menu.json` | Menus and macro estimates (generated) |
| `scripts/build_menu.py` | Builds `menu.json` (`--estimate` would ask the Claude API about new dishes, but only if a key is set; none is) |
| `scripts/estimates.txt` | `id\|kcal\|protein\|carbs\|fat\|serving` for every food seen so far |
| `.github/workflows/refresh-menu.yml` | The daily refresh job |
| `sw.js`, `manifest.webmanifest`, icons | Home Screen app and offline support |

## Refreshing by hand

Actions → Refresh Vanier menu → Run workflow. New dishes show "No estimate yet" until someone adds a line for them in `scripts/estimates.txt`.
