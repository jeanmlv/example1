# example1

Hi Tiffany, looking at your diagram, I think the overall structure looks good! I would just suggest a few adjustments to better reflect the ARD workflow:

1. **"J&J Derived" box:** I would clarify that the ARDs are generated in Domino using the SDTM/ADaM datasets imported from Med.AI, rather than being created directly by the IDAR or ORBIT teams.

2. **"IDAR" box (Harmonization):** I would change the description to something like "Support the investigation of missing variables by providing additional clinical datasets, study metadata (aCRF/ADaM metadata), and clarification on variable mappings." The variable gap analysis itself is performed on our side in Domino.

3. **Between IDAR and Med.AI/Domino:** I would add a feedback loop showing that, when new or updated datasets become available in Med.AI, they are imported into Domino to update the ARDs and rerun the variable gap analysis. Alternatively, metadata provided by IDARs may help resolve gaps using existing datasets.

4. **ORBIT Team:** If there's room, I would add a small box showing that the ORBIT team supports follow-ups with the IDARs and helps track pending items, while we update the IBD Tracker to keep Vasanth and Pablo informed.

5. **"Thea.View" box:** I would keep this as it is conceptually, since the ARDs are made available there for access and mapping with videos/images.

I think these small adjustments would make the workflow more accurate without changing the overall structure of your slide.
