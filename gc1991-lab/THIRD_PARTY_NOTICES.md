# Sources, citations, and licensing status

This local teaching candidate combines original project material with Basilisk components. It has not been published and does not assign a new blanket license to the instructor's original work. Select the original-code/documentation license before public distribution, consistently with the applicable upstream terms.

## Basilisk

The complete official source archive is included in `vendor/basilisk-source.tar.gz`, retrieved on 2026-09-08 from [Basilisk](https://basilisk.fr/basilisk/basilisk.tar.gz). SHA-256 and retrieval details are in `vendor/basilisk-source.json`. The official [installation guide](https://basilisk.fr/src/INSTALL) describes the upstream tools.

The archive's `src/COPYING` is the GNU General Public License, version 3; an unchanged copy is included in `LICENSES/Basilisk-COPYING.txt`. Preserve notices and applicable per-file terms in the archive. `core/sv_instrumented.h` derives from Basilisk's `saint-venant.h`; the local changes are provided in `core/sv-boundary.patch`. The build uses complete corresponding source, rather than redistributing a precompiled qcc binary. No additional restrictions on upstream components are intended by this document.

Historical research source paths and hashes appear in `reference/source_provenance.json`. They identify prior studies; those research directories are not runtime dependencies. See `docs/code-guide.md` for the small SV-only adapter and the coherent source snapshot policy.

## Experimental observations

Gharangik, A. M., and Chaudhry, M. H. (1991). “Numerical simulation of hydraulic jump.” *Journal of Hydraulic Engineering*, 117(9), 1195–1211. [DOI: 10.1061/(ASCE)0733-9429(1991)117:9(1195)](https://doi.org/10.1061/%28ASCE%290733-9429%281991%29117%3A9%281195%29).

`data/test4_observations.json` contains the project's manually transcribed Test 4 Table 2 numerical observations, checked against the printed table on 2026-09-04. It records the original PDF hash and extraction note for traceability, without redistributing the paper or including the instructor's private attachment path. Retain the citation and transcription note in derived teaching materials. Do not present these data as newly measured experiments.

The case-specific Manning n and exact numerical outflow station remain uncertain in the source reconstruction; the chosen assumptions are explicitly listed in `docs/methods.md`.

## Python dependencies

Python packages are installed from `requirements.txt`; each retains its own license. Exact locally installed versions are recorded in `.tools/python-packages.txt`. Virtual environments and binary build artifacts are excluded from the source release.
