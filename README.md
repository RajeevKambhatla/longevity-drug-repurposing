# longevity-drug-repurposing

10/28/26: App link: https://longevity-drug-repurposing-dihxymo5lgkbxemkqqxrrh.streamlit.app/
  Built a four-tab Streamlit dashboard: project overview with final picks, a searchable score table for all 15,542 compounds across six hallmarks, per-drug pages with AI evidence dossiers and false-alarm checks, and a validation page with held-out and lifespan-benchmark results.

10/24/26: False-alarm check: SHAP grouped by feature type (gene activity, chemistry, targets) for the top 20 candidates, plus similarity to a toxic-drug signature and signature strength; 76 of 90 candidate pairs red-flagged. Final AI selection over 13 unflagged candidates: best drug named for 6 of 6 hallmarks; top multi-hallmark candidates: kenpaullone, necrostatin-1, as-605240, ku-c103655, tgx-115.

10/20/26: Benchmarked final scores on held-out lifespan data, using the mean of six hallmark scores as the pre-specified primary score. ITP (excluding training drugs): AUC 0.56 (p = 0.45; 3 lifespan-extending vs 6 failed compounds). DrugAge (124 lifespan-extending compounds vs other named compounds): AUC 0.50 (p = 0.556), compared with 0.56 for signature strength alone. Contested ITP compounds excluded and listed.

10/17/26: Built a pooled logistic-regression meta-model combining gene-list and ML percentiles, trained on out-of-fold ML scores (weights: gene list 0.23, ML 0.09). Held-out test on 8 known helpful drugs never used in training or tuning: average percentile 54 (gene list), 58 (ML), 55 (meta-model). Ranked 90 shortlisted drug-hallmark pairs by AI evidence tier, then meta score: 1 High, 2 Medium, 68 stress-flagged.

10/16/26: Ran the RAG review (prompt v1) on 90 drug-hallmark pairs across 73 shortlisted drugs: 4 High, 12 Medium, 74 Low confidence; 68 flagged for possible cellular stress; all citations verified against supplied abstracts. 3 pairs rated Medium or High without a stress flag.

10/16/26: Designed a RAG review prompt (version v1): each review retrieves up to 10 relevant abstracts from the library across mechanism, aging, and safety questions, and returns a schema-validated dossier with a High/Medium/Low confidence rating and a cellular-stress flag. Tested on 5 shortlisted drugs ({'Low': 5}) plus two calibration drugs: metformin rated Medium on nutrient sensing, tunicamycin rated Low (stress flag True) on protein upkeep.

10/15/26: Built a research library for 73 shortlisted candidates (top 15 named, non-control compounds per hallmark): 1,728 PubMed abstracts (median 35 per drug; 13 drugs with none), embedded with a PubMedBERT-based model and indexed with FAISS for semantic search; retrieval tested on mechanism, aging, and safety questions.

10/14/26: Compared logistic regression and random forest, with signature-only and signature+fingerprint+target features, using grouped cross-validation. Best setup: logistic with signatures features (average left-out percentile 59 vs baseline 60). ML beat the baseline by >10 points for: nutrient sensing. Final models trained as 25-model ensembles for uncertainty estimates.

10/13/26: Trained regularized logistic regression per hallmark on signature PCA features (positives: known helpful drugs; negatives: harmful drugs plus 300 random compounds). Grouped cross-validation, average percentile of left-out drugs, ML vs baseline: autophagy 56 vs 50, inflammation 48 vs 59, mitochondria 47 vs 72, nutrient sensing 88 vs 71, proteostasis 76 vs 66, senescence 40 vs 40. Held out 8 known drugs for Week 6; added target features for 1509 compounds.

10/12/26: Built ML features for 15,542 VCAP compounds: ECFP4 chemical fingerprints for 15,503 compounds with structures, and 100 PCA components of the gene-activity signatures (62% of variance); signature neighbors of sirolimus include pi-828, ku-0063794, ly-294002, aminopurvalanol-a, ro-28-1675; UMAP map saved.

10/9/26: Scored all 15,542 VCAP compounds on six hallmarks in seconds with a fast averaging method (agreement with GSEA: 0.73–0.95 across hallmarks); known-drug gaps at full scale higher than Session 9; 128 named compounds rank in the top 5% on three or more hallmarks.

10/9/26: Validated all six hallmarks against 37 known drugs. Gaps: senescence 11, nutrient sensing 20, mitochondria 29, autophagy 3, inflammation 26, proteostasis 32. Using refined gene lists for none (original lists kept for all six).

10/9/26: Built known-drug lists for six hallmarks (37 drugs in total) from LLM suggestions verified against PubMed, plus 139 DrugAge lifespan-extending compounds found in VCAP.

10/6/26: LLM proposed genes for six hallmarks; 23 of 29 new core candidates kept after PubMed and biological review. Effects on control-drug rankings were mixed: proteostasis improved (stress drugs moved toward the bottom), senescence worsened (known senescence drugs dropped 2–18 places), and nutrient sensing was unchanged (sirolimus stayed 3rd). Using the refined list for proteostasis only, and the original lists elsewhere, until more control drugs are available.

10/6/26: Added gene lists for five more hallmarks and scored 100+ pilot drugs on all six; sirolimus ranked 3 of 106 on nutrient sensing; stress drugs ranked 106, 34, 84, 99, 23, 61 of 106 on proteostasis.

10/6/26: App link: https://longevity-drug-repurposing-dihxymo5lgkbxemkqqxrrh.streamlit.app/
Deployed pilot Streamlit app showing senescence scores and AI reviews.

Cell type: VCAP. It has 9 of the known aging drugs found in LINCS and 15542 drugs in total.

9/29/26: Extracted 34753 VCAP drug signatures across 15542 drugs from LINCS Phase 1.

10/3/26: Scored 100 VCAP drugs on senescence using SenMayo and gseapy enrichment; sirolimus ranked 52 of 100.

10/3/26: Added PubMed retrieval and structured LLM reviews for the top 5 senescence candidates; 5 rated Low.
