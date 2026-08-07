# YasinFeed Release Notes - v[VERSION_NUMBER]

**Release Date:** [YYYY-MM-DD]
**Tag:** `v[VERSION_NUMBER]`
**Stability:** [Stable / Release Candidate / Beta]

---

## 1. Release Overview

[Provide a concise, high-level summary of the focus of this release. Describe what major goals were accomplished, which components were upgraded, and the general impact of the changes.]

---

## 2. Key Features & Enhancements

- **[Feature Category / Module]:**
  - **[Feature Name]:** [Describe the feature, why it was introduced, how it works, and how to configure/trigger it.]
  - *Example:* Introduced a modular sequential rewrite AI pipeline engine under `yasinfeed/rewrite/`.
- **[Enhancement Category / Module]:**
  - **[Enhancement Name]:** [Describe the optimization or improvement.]

---

## 3. Bug Fixes & Code Improvements

- **[Fixed Component]:**
  - Fixed [Issue description] (PR #[PR_NUMBER] / Issue #[ISSUE_NUMBER]).
- **[Stability & Reliability]:**
  - Improved exception safety and socket teardown logic in `api/` server modules.

---

## 4. Upgrade & Migration Instructions

### Config Schema Changes
[Specify if any new keys were added or old keys deprecated in `config/config.yaml`.]

- *Example:* The key `storage.type` has been introduced to switch between SQLite and JSON.

### Database Migrations
[Outline any required actions to update existing SQLite databases.]

```sql
-- SQL migrations script (if applicable)
-- ALTER TABLE articles ADD COLUMN classification TEXT;
```

---

## 5. Dependency Updates

List any changes to required libraries and Python version support:

| Package Name | Old Version | New Version | Reason for Update |
|---|---|---|---|
| `PyYAML` | `5.4` | `6.0.1` | Security patches |
| `feedparser` | `6.0.8` | `6.0.10` | Standard Atom feeds support |

---

## 6. Contributors & Acknowledgments

We would like to thank all the developers and community members who contributed to this release!

- @username (Feature implementation & tests)
- @username (Bug hunting & documentation)
