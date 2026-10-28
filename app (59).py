import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Longevity Drug Repurposing", page_icon="🧬", layout="wide")

DATA = Path(__file__).parent / "app_data"
HM = {
    "senescence": "Worn-out cells (senescence)",
    "nutrient_sensing": "Growth signals (nutrient sensing)",
    "mitochondria": "Energy production (mitochondria)",
    "autophagy": "Cell recycling (autophagy)",
    "inflammation": "Inflammation",
    "proteostasis": "Protein upkeep (proteostasis)",
}
HALLMARKS = list(HM)
SHORT = {h: HM[h].split(" (")[0] for h in HALLMARKS}


@st.cache_data
def load():
    scores = pd.read_parquet(DATA / "scores.parquet")
    cands = pd.read_csv(DATA / "candidates.csv")
    for col in ["red_flags", "cautions", "key_refs", "targets pushing score up"]:
        if col in cands:
            cands[col] = cands[col].fillna("")
    def jload(name):
        p = DATA / name
        return json.loads(p.read_text()) if p.exists() else {}
    holdout = pd.read_csv(DATA / "holdout_test.csv") if (DATA / "holdout_test.csv").exists() else pd.DataFrame()
    return scores, cands, jload("final_results.json"), jload("benchmarks.json"), jload("hallmarks_summary.json"), holdout


scores, cands, picks, bench, hsum, holdout = load()
bres = bench.get("results", {})

st.title("Hallmark-Aware Longevity Drug Repurposing")
st.caption(
    f"Screening {len(scores):,} compounds for effects on six hallmarks of aging, using gene-activity data from "
    "human cells, machine learning, and AI review of published research. Early-stage computer screening, "
    "not medical advice."
)

tab_overview, tab_explore, tab_drug, tab_method = st.tabs(
    ["Overview", "Explore all scores", "Drug details", "How it works & validation"]
)

# ---------------- Overview ----------------
with tab_overview:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Compounds scored", f"{len(scores):,}")
    c2.metric("Candidates reviewed by AI", f"{cands['drug'].nunique()}")
    if len(holdout):
        c3.metric("Held-out known drugs: avg percentile", f"{holdout['meta'].mean():.0f}",
                  help="Where known helpful drugs, never used for training, ranked among all compounds (50 = random).")
    itp = bres.get("itp_independent_overall")
    if itp:
        c4.metric("Mouse lifespan benchmark (ITP) AUC", f"{itp['auc']:.2f}",
                  help=f"Chance a lifespan-extending compound outscores a failed one (0.5 = random). "
                       f"{itp['n_pos']} vs {itp['n_neg']} compounds, p = {itp['p']:.2f}.")

    st.subheader("Top multi-hallmark candidates")
    top5 = picks.get("top5", [])
    if not top5:
        st.info("No candidates met the bar for the multi-hallmark list.")
    for p in top5:
        with st.container(border=True):
            st.markdown(f"**{p['rank']}. {p['drug']}**  ·  " + ", ".join(SHORT.get(h, h) for h in p["hallmarks"]))
            st.write(p["why"])
            st.caption(f"Main caveat: {p['main_caveat']}")

    st.subheader("Best candidate for each hallmark")
    best = picks.get("best_per_hallmark", [])
    if best:
        st.dataframe(
            pd.DataFrame([{"Hallmark": HM.get(b["hallmark"], b["hallmark"]), "Drug": b["drug"], "Why": b["why"]}
                          for b in best]),
            hide_index=True, width="stretch",
        )
    st.caption("Picks were proposed by an AI reviewer from the evidence below and checked by the project author.")

# ---------------- Explore ----------------
with tab_explore:
    st.write("Final scores for every compound: percentiles from 100 (most helpful) to 0. Use the filters to explore.")
    f1, f2, f3 = st.columns([2, 2, 1])
    sort_by = f1.selectbox("Sort by", HALLMARKS, format_func=lambda h: HM[h])
    query = f2.text_input("Search by name")
    named_only = f3.toggle("Named compounds only", value=True)

    meta = scores[[f"{h}_meta" for h in HALLMARKS]].copy()
    meta.columns = [SHORT[h] for h in HALLMARKS]
    meta["Top-5% hallmarks"] = (meta >= 95).sum(axis=1)
    if named_only and "is_named" in scores:
        meta = meta[scores["is_named"].astype(bool)]
    if query:
        meta = meta[meta.index.str.contains(query.strip().lower(), regex=False)]
    meta = meta.sort_values(SHORT[sort_by], ascending=False)
    meta.index.name = "Compound"

    st.caption(f"{len(meta):,} compounds match; showing the top 500.")
    st.dataframe(
        meta.head(500).round(0),
        width="stretch", height=560,
        column_config={SHORT[h]: st.column_config.ProgressColumn(SHORT[h], min_value=0, max_value=100, format="%d")
                       for h in HALLMARKS},
    )

# ---------------- Drug details ----------------
with tab_drug:
    cand_drugs = sorted(cands["drug"].unique())
    others = sorted(set(scores.index[scores["is_named"].astype(bool)]) - set(cand_drugs)) if "is_named" in scores else []
    drug = st.selectbox("Choose a compound (AI-reviewed candidates are listed first)", cand_drugs + others)

    row = scores.loc[drug]
    st.subheader(drug)
    chart = pd.DataFrame({"Final score (percentile)": [row[f"{h}_meta"] for h in HALLMARKS]},
                         index=[SHORT[h] for h in HALLMARKS])
    st.bar_chart(chart, horizontal=True, height=280)

    detail = pd.DataFrame({
        "Hallmark": [HM[h] for h in HALLMARKS],
        "Gene-list score": [row[f"{h}_baseline"] for h in HALLMARKS],
        "ML score": [row[f"{h}_ml"] for h in HALLMARKS],
        "ML uncertainty (±)": [row[f"{h}_ml_sd"] for h in HALLMARKS],
        "Final score": [row[f"{h}_meta"] for h in HALLMARKS],
    }).round(0)
    st.dataframe(detail, hide_index=True, width="stretch")
    st.caption("Final score combines the gene-list and ML scores. Small ML uncertainty means the score was stable "
               "across 25 retrained models.")

    rows = cands[cands["drug"] == drug]
    if rows.empty:
        st.info("This compound wasn't in the top 15 for any hallmark, so it has no AI evidence review.")
    for _, r in rows.iterrows():
        r = r.to_dict()
        label = f"{HM.get(r['hallmark'], r['hallmark'])} · evidence: {r['confidence']}"
        if r.get("red_flags"):
            label += " · ⚠ possible false alarm"
        with st.expander(label, expanded=len(rows) == 1):
            if r.get("red_flags"):
                st.warning("Red flags: " + r["red_flags"])
            if r.get("cautions"):
                st.info("Cautions: " + r["cautions"])
            st.markdown(f"**How it might work:** {r['mechanism']}")
            st.markdown(f"**Evidence in cells:** {r['evidence_cell']}")
            st.markdown(f"**Evidence in animals:** {r['evidence_animal']}")
            st.markdown(f"**Evidence in people:** {r['evidence_human']}")
            st.markdown(f"**Safety:** {r['safety']}")
            st.markdown(f"**Why this rating:** {r['rationale']}")
            refs = [p.strip() for p in str(r.get("key_refs", "")).split(",") if p.strip()]
            if refs:
                st.markdown("**Key papers:** " + ", ".join(f"[{p}](https://pubmed.ncbi.nlm.nih.gov/{p}/)" for p in refs))
            checks = []
            for key, name in [("toxic_likeness", "Resemblance to toxic drugs"), ("signal_strength", "Signature strength")]:
                if pd.notna(r.get(key)):
                    checks.append(f"{name}: {r[key]:.0f}th percentile")
            shares = [f"{g} {r[g]:.0f}%" for g in ["gene activity %", "chemistry %", "targets %"] if pd.notna(r.get(g))]
            if shares:
                checks.append("What drove the ML score: " + ", ".join(s.replace(" %", "") for s in shares))
            if r.get("targets pushing score up") and r["targets pushing score up"] != "-":
                checks.append("Targets pushing the score up: " + r["targets pushing score up"])
            if checks:
                st.caption(" · ".join(checks))

# ---------------- Method & validation ----------------
with tab_method:
    st.subheader("How it works")
    st.markdown(
        """
1. **Data:** gene-activity measurements for 15,542 compounds in human VCaP cells (LINCS L1000).
2. **Six hallmarks of aging:** each has a gene list from MSigDB, SenMayo, or Gene Ontology, refined with AI suggestions that were checked against published research.
3. **Gene-list score:** how strongly each compound moves each hallmark's genes in the healthy direction.
4. **Machine learning:** a model per hallmark learns from known helpful and harmful drugs, using gene-activity patterns, chemical structure, and drug targets.
5. **Final score:** a meta-model combines the gene-list and ML scores.
6. **AI evidence review:** for top candidates, an AI reads the most relevant PubMed abstracts and writes a skeptical, cited evidence summary.
7. **False-alarm checks:** candidates whose signals look like cell damage or toxicity are flagged.
"""
    )

    st.subheader("Validation")
    if len(holdout):
        st.markdown("**Held-out known drugs.** Helpful drugs set aside before any training, never used for tuning. "
                    "Percentile among all compounds (50 = random):")
        show = holdout.rename(columns={"hallmark": "Hallmark", "drug": "Drug", "baseline": "Gene list",
                                       "ml": "ML", "meta": "Final"})
        show["Hallmark"] = show["Hallmark"].map(lambda h: HM.get(h, h))
        st.dataframe(show[["Hallmark", "Drug", "Gene list", "ML", "Final"]].round(0), hide_index=True,
                     width="stretch")
    lines = []
    if bres.get("itp_independent_overall"):
        x = bres["itp_independent_overall"]
        lines.append(f"- **Mouse lifespan (ITP), excluding training drugs:** AUC {x['auc']:.2f} "
                     f"({x['n_pos']} lifespan-extending vs {x['n_neg']} failed compounds, p = {x['p']:.2f})")
    if bres.get("drugage_overall"):
        x, s = bres["drugage_overall"], bres.get("drugage_signal_strength", {})
        lines.append(f"- **DrugAge lifespan database:** AUC {x['auc']:.2f} (p = {x['p']:.3f}) vs "
                     f"{s.get('auc', float('nan')):.2f} for signature strength alone")
    if lines:
        st.markdown("**Lifespan benchmarks** (AUC: 0.5 = random, 1.0 = perfect):\n" + "\n".join(lines))
    if bench.get("itp_excluded"):
        st.caption("ITP compounds left out because results conflict between studies: " + ", ".join(bench["itp_excluded"]))

    if hsum:
        st.subheader("Hallmarks")
        st.dataframe(pd.DataFrame([{"Hallmark": HM.get(h, h), "Genes in list": v.get("genes"),
                                    "Gene list used": v.get("version"), "Score used": v.get("score_source"),
                                    "Known-drug gap": v.get("gap")} for h, v in hsum.items()]),
                     hide_index=True, width="stretch")

    if (DATA / "umap_signatures.png").exists():
        st.subheader("Map of all compounds by gene-activity signature")
        st.image(str(DATA / "umap_signatures.png"),
                 caption="Compounds with similar effects on gene activity sit close together. Red: known drugs.")

    st.subheader("Limitations")
    st.markdown(
        """
- Results come from one cancer cell line (VCaP), which may not reflect aging tissue.
- Only six of the twelve hallmarks of aging can be measured from gene activity.
- A change in gene activity is an early hint, not proof of a real biological effect.
- Few known drugs exist per hallmark, so the models learn from small examples.
- AI reviews depend on the abstracts retrieved and can contain mistakes; every citation was checked.
- Any promising compound would still need laboratory testing.
"""
    )
