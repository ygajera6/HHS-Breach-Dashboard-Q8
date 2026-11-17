# Hacking vs. Unauthorized Disclosure | HHS Breach Dashboard (Research Question 8)

Streamlit dashboard comparing Hacking/IT Incident and Unauthorized Access/Disclosure breach reports from the HHS OCR Breach Portal (2020 onward, snapshot November 10, 2026).

## Deploy (no Python install needed)
1. Upload `app.py`, `requirements.txt`, and `hhs_breaches.xlsx` to the root of your GitHub repository.
2. At https://share.streamlit.io/ choose **Create app**, pick the repository and branch, and set `app.py` as the entry point.

## Interactive features
- **Dropdown filters:** breach types (side by side or one), covered entity type, state, business associate present, information location.
- **Date range slider:** breach submission period.

## Visualizations
1. **Bar chart:** information locations, hacking vs. UAD (share of reports, number of reports, or individuals affected).
2. **Pie charts:** each type's share of reports vs. share of individuals affected.
3. **Line chart:** yearly reports, individuals affected, or median individuals per report.

## Caveats
Reported breaches of 500+ individuals only. Sums of individuals affected are not unique people. The dashboard shows reported patterns; it does not establish causes or breach probabilities. See `Data_Preparation_Notes.md` for exclusions.
