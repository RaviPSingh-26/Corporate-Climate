"""
CDP Corporate Climate Disclosure Dashboard
-------------------------------------------
Compares climate-risk, mitigation, target, and supplier disclosures
across 5 companies (Adobe, Cognizant, Accenture, Alphabet, Microsoft)
using their CDP Climate Change questionnaire responses.

Run with:  streamlit run app.py
(Make sure Companies_CDP_MERGED.xlsx is in the same folder as this file.)
"""

import re
import pandas as pd
import streamlit as st
import plotly.express as px

# ----------------------------------------------------------------------
# PAGE CONFIG  (must be the first Streamlit command)
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="CDP Corporate Climate Dashboard",
    layout="wide",
)

DATA_FILE = "Companies_CDP_MERGED.xlsx"
COMPANY_ORDER = ["Adobe", "Accenture", "Alphabet", "Cognizant", "Microsoft"]


# ----------------------------------------------------------------------
# 1. LOAD + PREP DATA
# ----------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE, sheet_name="All Matches")
    df["Answer Text"] = df["Answer Text"].fillna("")
    return df


def add_keyword_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Tag each row with keyword-based indicators used across the dashboard."""
    target_kw = re.compile(
        r"science.based target|SBTi|net-zero|net zero|1\.5.?C aligned"
        r"|target achieved|% of target",
        re.I,
    )
    supplier_kw = re.compile(
        r"supplier.{0,40}(requirement|compliance|code of conduct|contract)", re.I
    )
    money_pat = re.compile(r"\b\d{5,}(?:\.\d+)?\b")  # 5+ digit numbers = $ figures

    df = df.copy()
    df["has_target_kw"] = df["Answer Text"].str.contains(target_kw)
    df["has_supplier_kw"] = df["Answer Text"].str.contains(supplier_kw)
    df["money_figures"] = df["Answer Text"].apply(lambda t: money_pat.findall(t))
    df["n_money_figures"] = df["money_figures"].apply(len)
    return df


# ----------------------------------------------------------------------
# 2. LOAD DATA
# ----------------------------------------------------------------------
raw_df = load_data()
df = add_keyword_flags(raw_df)

companies_present = [c for c in COMPANY_ORDER if c in df["Company"].unique()]

st.title("🌍 CDP Corporate Climate Disclosure Dashboard")
st.caption(
    "Comparing climate risk, mitigation, target, and supplier disclosures "
    "across Adobe, Accenture, Alphabet, Cognizant, and Microsoft — based on "
    "their CDP Climate Change questionnaire responses (matched excerpts)."
)

with st.expander("ℹ️ About this data & methodology", expanded=False):
    st.markdown(
        """
This dashboard uses **matched excerpts** from each company's CDP Climate
Change questionnaire response — not the full filing. Each row is a
questionnaire section (identified by a *Question Code*) tagged with a
*Matched Category* (Hazard / Risk / Mitigation / Vulnerability) and an
*Answer Type* (Qualitative / Quantitative / Not Applicable).

Because the underlying answer text mixes several sub-questions into one
free-text block, some indicators below (target mentions, supplier
requirement mentions, financial figures) are built with **keyword and
pattern matching** rather than exact field extraction. They're good for
spotting relative differences between companies — always check the
**Data Explorer** tab to read the original text behind any number.
        """
    )

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📊 Overview",
        "💰 Financial Risk Quantification",
        "🎯 Emissions Targets",
        "🔗 Supplier Requirements",
        "🔍 Data Explorer",
    ]
)

# ----------------------------------------------------------------------
# TAB 1 — OVERVIEW
# ----------------------------------------------------------------------
with tab1:
    st.subheader("Disclosure volume by company")
    vol = df["Company"].value_counts().reindex(companies_present)
    fig = px.bar(
        vol,
        x=vol.index,
        y=vol.values,
        labels={"x": "Company", "y": "# matched disclosures"},
        color=vol.index,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Disclosure mix: Risk vs Mitigation vs Vulnerability vs Hazard")
    st.caption(
        "A row can be tagged with more than one category (e.g. 'Risk, Mitigation'), "
        "so this counts every category a row is tagged with."
    )
    cat_counts = (
        df.assign(cat=df["Matched Category"].str.split(", "))
        .explode("cat")
        .groupby(["Company", "cat"])
        .size()
        .reset_index(name="count")
    )
    fig2 = px.bar(
        cat_counts,
        x="Company",
        y="count",
        color="cat",
        barmode="stack",
        category_orders={"Company": companies_present},
    )
    st.plotly_chart(fig2, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Qualitative vs Quantitative answers")
        at = pd.crosstab(df["Company"], df["Answer Type"]).reindex(companies_present)
        fig3 = px.bar(at, barmode="stack")
        st.plotly_chart(fig3, use_container_width=True)
    with c2:
        st.subheader("% of each company's disclosures that are Quantitative")
        pct = (at.get("Quantitative", 0) / at.sum(axis=1) * 100).round(1)
        fig4 = px.bar(pct, labels={"value": "% Quantitative", "index": "Company"})
        st.plotly_chart(fig4, use_container_width=True)

# ----------------------------------------------------------------------
# TAB 2 — FINANCIAL RISK QUANTIFICATION
# ----------------------------------------------------------------------
with tab2:
    st.subheader('Which companies quantify financial risk vs. describe it qualitatively?')

    risk_df = df[df["Matched Category"].str.contains("Risk", na=False)]
    risk_at = pd.crosstab(risk_df["Company"], risk_df["Answer Type"]).reindex(
        companies_present
    )
    st.markdown("**Answer type of Risk-tagged disclosures, by company**")
    fig5 = px.bar(risk_at, barmode="group")
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("**Financial figures mentioned in Risk disclosures**")
    st.caption(
        "Counts 5+ digit numbers appearing in the answer text of Risk-tagged rows "
        "as a proxy for disclosed monetary figures (e.g. cost of risk, revenue impact)."
    )
    money_by_co = (
        risk_df.groupby("Company")["n_money_figures"]
        .sum()
        .reindex(companies_present)
        .fillna(0)
    )
    fig6 = px.bar(
        money_by_co,
        labels={"value": "# of financial figures mentioned", "index": "Company"},
    )
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown("**Ranking: financial-risk quantification score**")
    st.caption(
        "Simple composite = (# Quantitative Risk rows) + (# financial figures mentioned "
        "in Risk rows). Higher = more numbers-backed financial risk disclosure."
    )
    quant_count = risk_at.get("Quantitative", 0)
    score = (quant_count + money_by_co).sort_values(ascending=False)
    st.dataframe(score.rename("score").to_frame(), use_container_width=True)

    with st.expander("See the underlying Risk rows with financial figures"):
        show = risk_df[risk_df["n_money_figures"] > 0][
            ["Company", "Question Code", "Answer Type", "n_money_figures", "money_figures"]
        ].sort_values("n_money_figures", ascending=False)
        st.dataframe(show, use_container_width=True)

# ----------------------------------------------------------------------
# TAB 3 — EMISSIONS TARGETS
# ----------------------------------------------------------------------
with tab3:
    st.subheader("How do emissions-reduction target disclosures compare across companies?")
    st.caption(
        "Rows flagged by keywords: 'science-based target', 'SBTi', 'net-zero', "
        "'1.5°C aligned', 'target achieved', '% of target'."
    )

    target_rows = df[df["has_target_kw"]]
    tcount = target_rows["Company"].value_counts().reindex(companies_present).fillna(0)
    fig7 = px.bar(
        tcount, labels={"value": "# target-related disclosures", "index": "Company"}
    )
    st.plotly_chart(fig7, use_container_width=True)

    st.markdown("**Which Matched Categories carry the target-related content?**")
    fig8 = px.bar(
        target_rows.groupby(["Company", "Matched Category"]).size().reset_index(name="count"),
        x="Company",
        y="count",
        color="Matched Category",
        barmode="stack",
        category_orders={"Company": companies_present},
    )
    st.plotly_chart(fig8, use_container_width=True)

    with st.expander("Read the target-related disclosures"):
        show = target_rows[["Company", "Question Code", "Answer Type", "Answer Text"]]
        pick = st.selectbox("Filter by company", ["All"] + companies_present, key="tgt_co")
        if pick != "All":
            show = show[show["Company"] == pick]
        for _, r in show.iterrows():
            st.markdown(f"**{r['Company']} — {r['Question Code']}** ({r['Answer Type']})")
            st.write(r["Answer Text"][:1500] + ("..." if len(r["Answer Text"]) > 1500 else ""))
            st.divider()

# ----------------------------------------------------------------------
# TAB 4 — SUPPLIER CLIMATE REQUIREMENTS
# ----------------------------------------------------------------------
with tab4:
    st.subheader("Which companies disclose supplier climate requirements?")
    st.caption(
        "Rows flagged where 'supplier' appears near 'requirement', 'compliance', "
        "'code of conduct', or 'contract'."
    )

    sup_rows = df[df["has_supplier_kw"]]
    scount = sup_rows["Company"].value_counts().reindex(companies_present).fillna(0)
    fig9 = px.bar(
        scount, labels={"value": "# supplier-requirement disclosures", "index": "Company"}
    )
    st.plotly_chart(fig9, use_container_width=True)

    st.markdown(f"**Companies with at least one supplier-requirement disclosure:** "
                f"{', '.join(scount[scount > 0].index) if (scount > 0).any() else 'None'}")
    st.markdown(f"**Companies with none found in this matched data:** "
                f"{', '.join(scount[scount == 0].index) if (scount == 0).any() else 'None'}")

    with st.expander("Read the supplier-requirement disclosures"):
        for _, r in sup_rows[["Company", "Question Code", "Answer Type", "Answer Text"]].iterrows():
            st.markdown(f"**{r['Company']} — {r['Question Code']}** ({r['Answer Type']})")
            st.write(r["Answer Text"][:1500] + ("..." if len(r["Answer Text"]) > 1500 else ""))
            st.divider()

# ----------------------------------------------------------------------
# TAB 5 — DATA EXPLORER
# ----------------------------------------------------------------------
with tab5:
    st.subheader("Explore the raw matched data")

    c1, c2, c3 = st.columns(3)
    with c1:
        f_company = st.multiselect("Company", companies_present, default=companies_present)
    with c2:
        f_type = st.multiselect(
            "Answer Type", sorted(df["Answer Type"].dropna().unique()),
            default=sorted(df["Answer Type"].dropna().unique()),
        )
    with c3:
        f_keyword = st.text_input("Search answer text for keyword")

    filtered = df[df["Company"].isin(f_company) & df["Answer Type"].isin(f_type)]
    if f_keyword:
        filtered = filtered[filtered["Answer Text"].str.contains(f_keyword, case=False, na=False)]

    st.write(f"{len(filtered)} rows match your filters")
    st.dataframe(
        filtered[
            ["Company", "Question Code", "Matched Category", "Answer Type", "Start Page", "Answer Text"]
        ],
        use_container_width=True,
        height=500,
    )

    csv = filtered.drop(columns=["money_figures"], errors="ignore").to_csv(index=False)
    st.download_button("⬇️ Download filtered data as CSV", csv, "filtered_cdp_data.csv", "text/csv")
