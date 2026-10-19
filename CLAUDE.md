# Vanier Macros — notes for Claude

Personal macro tracker for Gather (Place Vanier, UBC), served from GitHub Pages at https://mishasayani.github.io/vanier-macros/. The owner logs food on their phone; the log lives only in the phone's browser storage, so Claude never sees or edits it.

Nutrislice has no nutrition data for Vanier. Every dish's macros are estimates in `scripts/estimates.txt` (`id|kcal|protein|carbs|fat|serving`), merged into `menu.json` by `scripts/build_menu.py`. A GitHub Action rebuilds `menu.json` every morning; it only adds dishes, never changes existing estimate lines.

## Photo estimates (the main way estimates get improved)

The owner sends photos of a Vanier meal, with a common object for scale, and names the dish. For each one:

1. Find the dish in `menu.json` by name (and date, if given) to get its Nutrislice id and ingredients. If the name matches more than one dish or none, ask.
2. Judge the portion from the photo against the scale object, then estimate kcal, protein, carbs and fat for that serving using the ingredient list.
3. Replace that id's line in `scripts/estimates.txt`. Make the serving text describe what was in the photo, e.g. `plate (~1 cup rice, ~120 g chicken)`.
4. Rebuild with `python3 scripts/build_menu.py <3 days ago> 17`, then commit and push. Pages redeploys in a minute or two.
5. Reply with the old and new numbers and the portion you assumed.

**Always say when a photo isn't good enough, before estimating.** Name the problem and what would fix it. Problems include: no scale object, or one too far from the plate to compare; food hidden under other food, sauce or a lid; only a side view of a bowl or other deep dish, so the depth can't be judged; blurry or dark images; the meal already partly eaten; more than one dish on the plate with no say which is which. If you can still give a rough estimate, label it as low confidence and ask for a better photo next time that dish is served.

Skip dishes the owner has already sent photos for unless they ask for a redo. In-app overrides the owner made on their phone take priority over `estimates.txt`; mention that if they say a dish still shows old numbers.

## Other

- No in-app Claude calls and no API keys: the owner removed them on purpose.
- Keep the page a single `index.html` with no build step. Test at phone width in light and dark mode before pushing.
