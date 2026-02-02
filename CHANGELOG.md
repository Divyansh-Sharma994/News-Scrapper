# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-02-02

### Added
- Created `CHANGELOG.md` to track project history.
- Added `.github/coderabbit.yaml` for AI code reviews.
- Added `xlsxwriter` to environment for Excel export support.

### Changed
- **UI Polish**:
  - **Dynamic Progress Bar**: The loader now updates in real-time (e.g., "Reading articles... 45%"), giving feedback on the exact scraping progress.
  - **Animated Loader**: Replaced basic spinners with a **Step-by-Step Status Box**.
  - **Scrollable Results**: Added a dedicated scrollbar area (height=800px) for the results list.
  - **Clean Layout**: Moved summary inside dropdown.
- **Documentation**: Added comprehensive "ELI5" (Explain Like I'm 5) comments to the entire codebase. Now non-technical users can understand what each file (`app2.py`, `article_scraper.py`, `gdelt_fetcher.py`) is doing.
- **Capacity Upgrade**: Removed all hard limits. The app now fetches **all available articles** for the specified duration and keyword. Added concurrency control (Semaphore) to handle mass-fetching safely.
- **Extraction Improvements**:
  - **Redirect Handling**: Integrated `batchexecute` decoder (from `xdpooja/newsscraper`) to properly resolve Google News encrypted URLs. This fixes the "Redirecting..." page issue.
  - **Anti-Blocking**: Added 'Referer' headers and a persistent Cookie Jar to pass checks on sites like MSN.
  - Upgraded `article_scraper.py` to use "Text Density Heuristics" for smarter content locating.
  - Improved "Fallback Extraction" for sites without standard paragraph tags.
  - Removed length restriction in UI, so even short articles are displayed instead of the warning message.
- **Rolled Back**: Reverted HTML & Image display features. Returned to "Text Summary" + "Full Text Dropdown" view.
- **Enhanced Content Display**:
  - Added dropdown "Read Full Article Content" to view the entire article without leaving the app.
  - Added "Paywall Detection": The app now warns if an article requires a subscription ("🔒 Subscription Required").
- **UI Overhaul**: Simplified `app2.py` to focus on a single "Search & Display" workflow.
  - Added dropdown "Read Full Article Content" to view the entire article without leaving the app.
  - Added "Paywall Detection": The app now warns if an article requires a subscription ("🔒 Subscription Required").
- **UI Overhaul**: Simplified `app2.py` to focus on a single "Search & Display" workflow.
  - Removed "Top Agencies" analysis feature.
  - Unified search interface.
  - Improved result display (Headline, Source, 3-4 line Summary).
- **Code Quality**: Rewrote comments in `app2.py`, `article_scraper.py`, and `gdelt_fetcher.py` to be "ELI5" (Explain Like I'm 5) for better readability.
- **Performance**: Increased network timeouts in `gdelt_fetcher.py` and `article_scraper.py` for better reliability on slow connections.
- **Bug Fix**: Fixed Excel download MIME type in `app2.py` to prevent "file corrupted" errors.
