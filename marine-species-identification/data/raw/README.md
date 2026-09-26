# Fish4Knowledge (F4K) Marine Species Ground-Truth Dataset

## Overview & Scientific Source
- **Official Source**: University of Edinburgh, School of Informatics
- **Project**: European Commission FP7 Fish4Knowledge Project (Grant Agreement No. 257245)
- **Official Portal**: `https://homepages.inf.ed.ac.uk/rbf/Fish4Knowledge/GROUNDTRUTH/RECOG/`
- **Acquisition Date**: September 26, 2026
- **License / Permitted Use**: Open Academic Research & Scientific Evaluation Benchmark
- **Habitat**: Live underwater video streams from Kenting National Park coral reef cameras (Taiwan)
- **Ground-Truth Labeling**: Verified by professional marine biologists from the National Museum of Marine Biology and Aquarium (NMMBA)

## Taxonomic Class Catalog
The dataset contains live underwater marine fish imagery spanning 10 representative species across 7 distinct families:
1. `species_02`: *Plectroglyphidodon dickii* (Blackbar damselfish, Family: Pomacentridae)
2. `species_04`: *Amphiprion clarkii* (Yellowtail clownfish, Family: Pomacentridae)
3. `species_05`: *Chaetodon lunulatus* (Oval butterflyfish, Family: Chaetodontidae)
4. `species_06`: *Chaetodon trifascialis* (Chevron butterflyfish, Family: Chaetodontidae)
5. `species_07`: *Myripristis kuntee* (Shoulderspot soldierfish, Family: Holocentridae)
6. `species_08`: *Acanthurus nigrofuscus* (Brown surgeonfish, Family: Acanthuridae)
7. `species_09`: *Hemigymnus fasciatus* (Barred thicklip wrasse, Family: Labridae)
8. `species_10`: *Neoniphon sammara* (Sammara squirrelfish, Family: Holocentridae)
9. `species_12`: *Canthigaster valentini* (Valentin's sharpnose puffer, Family: Tetraodontidae)
10. `species_16`: *Lutjanus fulvus* (Blacktail snapper, Family: Lutjanidae)

## File Naming Convention & Trajectory Tracking
Each image is named according to:
`fish_<tracking_id>_<fish_id>.png`
- `tracking_id`: Unique identifier of the underwater video tracking trajectory sequence.
- `fish_id`: Global unique detection index.

All images sharing the same `tracking_id` originate from the same fish trajectory instance in video.
**Critical for Data Leakage Prevention**: Train/Validation/Test splits are grouped by `tracking_id` so no video trajectory is split across sets.
