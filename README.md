# longevity-drug-repurposing

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
