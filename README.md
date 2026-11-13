# CDP Corporate Climate Disclosure Dashboard

A Streamlit dashboard comparing climate-risk, mitigation, target and supplier disclosures of five companies — Adobe, Accenture, Alphabet, Cognizant and Microsoft — using excerpts from their CDP Climate Change questionnaire responses.

## Dashboard tabs
1. **Overview** – disclosure volume, mix of Risk / Mitigation / Vulnerability / Hazard, qualitative vs quantitative answers
2. **Financial Risk Quantification** – which companies back risk disclosures with numbers, plus a simple ranking score
3. **Emissions Targets** – target-related disclosures (science-based targets, net-zero, 1.5°C alignment)
4. **Supplier Requirements** – companies that disclose supplier climate requirements
5. **Data Explorer** – filter the raw matched rows and download them as CSV

## Tech stack
Python, Streamlit, pandas, Plotly Express, openpyxl.

## Run locally
```bash
git clone https://github.com/RaviPSingh-26/Corporate-Climate.git
cd Corporate-Climate
pip install -r requirements.txt
streamlit run IT.py
```
Keep `Companies_CDP_MERGED.xlsx` in the same folder as `IT.py`.

## Files
| File | Purpose |
|---|---|
| `IT.py` | The dashboard app |
| `Companies_CDP_MERGED.xlsx` | Matched CDP excerpts (sheet `All Matches`) |
| `requirements.txt` | Python dependencies |

## Method and limitations
Each row is one questionnaire section with a *Question Code*, *Matched Category* and *Answer Type*. The data holds matched excerpts, not the full filings.

Target mentions, supplier requirements and financial figures are detected with **keyword and pattern matching** (for example, any number with five or more digits is treated as a monetary figure). The results are useful for relative comparison between companies but are approximate, so check the original text in the Data Explorer tab before drawing conclusions.
