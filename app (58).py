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


def check_setup():
    """Show a plain-language message instead of a crash if the data files or columns aren't as expected."""
    root = Path(__file__).parent
    required = ["scores.parquet", "candidates.csv"]
    missing = [f for f in required if not (DATA / f).exists()]
    if missing:
        st.error("The app can't find its data files: " + ", ".join(missing))
        if DATA.exists():
            st.write("Files found in the app_data folder:", sorted(p.name for p in DATA.iterdir()))
        else:
            st.write("There's no app_data folder next to app.py in the repository.")
        loose = [f for f in required if (root / f).exists()]
        if loose:
            st.write("These files are at the top level of the repository instead of inside app_data:", loose)
        st.stop()
    try:
        data = load()
    except Exception as e:
        st.error(f"The data files exist but couldn't be read: {type(e).__name__}: {e}")
        st.stop()
    scores_, cands_ = data[0], data[1]
    need_scores = [f"{h}_{k}" for h in HALLMARKS for k in ["baseline", "ml", "ml_sd", "meta"]] + ["is_named"]
    need_cands = ["drug", "hallmark", "confidence", "mechanism", "evidence_cell", "evidence_animal",
                  "evidence_human", "safety", "rationale"]
    gaps = {"scores.parquet": [c for c in need_scores if c not in scores_.columns],
            "candidates.csv": [c for c in need_cands if c not in cands_.columns]}
    gaps = {k: v for k, v in gaps.items() if v}
    if gaps:
        st.error("Some expected columns are missing from the data files.")
        for f, cols in gaps.items():
            st.write(f"**{f}** is missing:", cols)
        st.write("**scores.parquet** has:", list(scores_.columns)[:40])
        st.write("**candidates.csv** has:", list(cands_.columns))
        st.stop()
    return data


scores, cands, picks, bench, hsum, holdout = check_setup()
bres = bench.get("results", {})

st.title("Hallmark-Aware Longevity Drug Repurposing")
st.caption(
    f"Screening {len(scores):,} compounds for effects on six hallmarks of aging, using gene-activity data from "
    "human cells, machine learning, and AI review of published research. Early-stage computer screening, "
    "not medical advice."
)

tab_overview, tab_explore, tab_drug, tab_method, tab_chat = st.tabs(
    ["Overview", "Explore all scores", "Drug details", "How it works & validation", "Ask a question"]
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

    st.subheader("Top candidates")
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

# ---------------- Chat assistant ----------------
def secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


DAILY_LIMIT = int(secret("DAILY_QUESTION_LIMIT", 100))
SESSION_LIMIT = 15


@st.cache_resource
def usage_counter():
    return {"day": None, "count": 0}


def project_summary():
    lines = [
        "PROJECT: Hallmark-aware longevity drug repurposing. 15,542 compounds were screened using gene-activity data "
        "from one human prostate cancer cell line (VCaP, LINCS L1000). Each compound has a final score (percentile, "
        "100 = most helpful) for six hallmarks of aging: " + "; ".join(HM.values()) + ".",
        "METHOD: gene-list score per hallmark; machine-learning model per hallmark trained on known helpful and harmful "
        "drugs; a meta-model combining both into the final score; AI review of PubMed abstracts for the top 15 named "
        "compounds per hallmark (confidence High/Medium/Low); false-alarm checks for toxicity-like signatures.",
    ]
    if len(holdout):
        lines.append("HELD-OUT TEST (known helpful drugs never used in training; percentile among all compounds): "
                     + "; ".join(f"{r.drug} ({r.hallmark}) {r.meta:.0f}" for r in holdout.itertuples())
                     + f". Average {holdout['meta'].mean():.0f} (50 = random).")
    for key, name in [("itp_independent_overall", "ITP mouse lifespan benchmark"),
                      ("drugage_overall", "DrugAge lifespan benchmark"),
                      ("drugage_signal_strength", "DrugAge, signature strength alone (control)")]:
        if bres.get(key):
            lines.append(f"{name}: AUC {bres[key]['auc']:.2f}, p = {bres[key]['p']:.2f} (0.5 = random).")
    if picks.get("top5"):
        lines.append("FINAL TOP CANDIDATES: " + "; ".join(
            f"{p['rank']}. {p['drug']} ({', '.join(p['hallmarks'])}): {p['why']} Caveat: {p['main_caveat']}"
            for p in picks["top5"]))
    if picks.get("best_per_hallmark"):
        lines.append("BEST PER HALLMARK: " + "; ".join(f"{b['hallmark']}: {b['drug']}" for b in picks["best_per_hallmark"]))
    lines.append("LIMITATIONS: one cancer cell line; only six of twelve hallmarks; gene activity is an early hint, not "
                 "proof; few known drugs per hallmark; AI reviews can contain mistakes; lab testing still needed.")
    lines.append("ALL AI-REVIEWED CANDIDATES (drug | hallmark | final score | evidence | red flags):")
    for r in cands.itertuples(index=False):
        rd = r._asdict()
        lines.append(f"- {rd['drug']} | {rd['hallmark']} | {rd.get('meta_pct', float('nan')):.0f} | "
                     f"{rd['confidence']} | {rd.get('red_flags') or 'none'}")
    return "\n".join(lines)


def drug_details(question):
    q = question.lower()
    words = set(q.replace(",", " ").replace("?", " ").replace(".", " ").split())
    mentioned = [d for d in scores.index if (len(d) > 3 and d in q) or d in words]
    mentioned = sorted(set(mentioned), key=len, reverse=True)[:6]
    out = []
    for d in mentioned:
        row = scores.loc[d]
        out.append(f"SCORES for {d}: " + "; ".join(
            f"{h}: final {row[f'{h}_meta']:.0f}, gene list {row[f'{h}_baseline']:.0f}, ML {row[f'{h}_ml']:.0f}"
            for h in HALLMARKS))
        for _, r in cands[cands["drug"] == d].iterrows():
            out.append(f"DOSSIER {d} / {r['hallmark']} (evidence {r['confidence']}): mechanism: {r['mechanism']} | "
                       f"cells: {r['evidence_cell']} | animals: {r['evidence_animal']} | people: {r['evidence_human']} | "
                       f"safety: {r['safety']} | rating reason: {r['rationale']} | red flags: {r.get('red_flags') or 'none'} | "
                       f"cautions: {r.get('cautions') or 'none'} | PMIDs: {r.get('key_refs') or 'none'}")
    return mentioned, "\n".join(out)


CHAT_SYSTEM = """You answer questions about one longevity drug-repurposing research project, using ONLY the project
data provided. Rules:
- If the data doesn't answer the question, say so plainly; never fill gaps from general knowledge about drugs.
- Use everyday language first, with technical terms in brackets where useful. Keep answers short (under 200 words).
- Scores are percentiles from 0 to 100, where 100 = most helpful among 15,542 compounds.
- Be honest about uncertainty and limitations, including mixed validation results.
- When citing evidence, use only PMIDs that appear in the data, written as PMID numbers.
- This is early computer screening, not medical advice. Never recommend that anyone take a drug."""

with tab_chat:
    st.write("Ask questions about the results, such as *which drugs help both inflammation and protein upkeep?* or "
             "*why was kenpaullone picked?* Answers come only from this project's data.")
    key = secret("ANTHROPIC_API_KEY")
    password = secret("APP_PASSWORD")
    if not key or not password:
        st.info("The chat assistant isn't switched on for this app yet.")
    else:
        if not st.session_state.get("chat_ok"):
            entered = st.text_input("Password", type="password",
                                    help="The chat uses a paid AI service, so it's limited to invited users.")
            if entered:
                if entered == password:
                    st.session_state["chat_ok"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        else:
            st.session_state.setdefault("chat", [])
            for m in st.session_state["chat"]:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

            counter = usage_counter()
            today = pd.Timestamp.now(tz="America/New_York").date()
            if counter["day"] != today:
                counter.update(day=today, count=0)
            asked = sum(m["role"] == "user" for m in st.session_state["chat"])

            question = st.chat_input("Ask about the drugs, hallmarks, or results")
            if question:
                if asked >= SESSION_LIMIT:
                    st.warning(f"You've reached the limit of {SESSION_LIMIT} questions for this visit.")
                elif counter["count"] >= DAILY_LIMIT:
                    st.warning("The daily question limit for this app has been reached. Please try again tomorrow.")
                else:
                    counter["count"] += 1
                    with st.chat_message("user"):
                        st.markdown(question)
                    _, details = drug_details(question)
                    context = project_summary() + ("\n\nDETAILS FOR COMPOUNDS NAMED IN THE QUESTION:\n" + details
                                                   if details else "")
                    history = st.session_state["chat"][-6:]
                    messages = [{"role": m["role"], "content": m["content"]} for m in history]
                    messages.append({"role": "user", "content": f"PROJECT DATA:\n{context}\n\nQUESTION: {question}"})
                    with st.chat_message("assistant"):
                        try:
                            import anthropic
                            client = anthropic.Anthropic(api_key=key)
                            with client.messages.stream(model=secret("CHAT_MODEL", "claude-haiku-5-5"),
                                                        max_tokens=1500, system=CHAT_SYSTEM,
                                                        messages=messages) as stream:
                                answer = st.write_stream(stream.text_stream)
                            st.session_state["chat"] += [{"role": "user", "content": question},
                                                         {"role": "assistant", "content": answer}]
                        except Exception as e:
                            counter["count"] -= 1
                            st.error(f"The assistant couldn't answer just now ({type(e).__name__}). Please try again.")
            st.caption(f"Questions this visit: {asked} of {SESSION_LIMIT}. Answers can contain mistakes; "
                       "check them against the Drug details tab.")
