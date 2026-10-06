import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Longevity Drug Repurposing", page_icon="🧬")
st.title("Hallmark-Aware Longevity Drug Repurposing")
st.caption("Pilot version: one hallmark (cellular senescence), 100 drugs, VCAP cells")

with open("senescence_results.json") as f:
    data = json.load(f)
scores = pd.DataFrame(data["scores"])
reviews = data["reviews"]

st.header("Senescence scores")
st.write(
    "Each drug was scored on how strongly it pushed senescence genes (the SenMayo list) "
    "down in VCAP cells. A higher score means a stronger push in the helpful direction."
)
st.dataframe(scores, hide_index=True)

st.header("AI reviews of top candidates")
st.write("An AI reviewer read published research on each top drug and judged how believable its effect is.")
drug = st.selectbox("Choose a drug", list(reviews))
r = reviews[drug]
st.subheader(f"{drug}: {r['believability']} believability")
st.markdown(f"**Likely mechanism:** {r['likely_mechanism']}")
st.markdown(f"**Evidence:** {r['evidence_summary']}")
st.markdown(f"**Concerns:** {r['concerns']}")
if r["key_pmids"]:
    links = ", ".join(f"[{p}](https://pubmed.ncbi.nlm.nih.gov/{p}/)" for p in r["key_pmids"])
    st.markdown(f"**Key papers:** {links}")

st.divider()
st.caption("Early pilot results from a portfolio project. Not medical advice.")
