# Imaging AI — X-ray, OPG, CBCT & MRI (v2)

Implemented in `backend/app/routes/imaging.py`, wired to the frontend at
**Dental Imaging** in the app sidebar.

## Study types supported
| Type | What the AI screens for |
|---|---|
| Intraoral X-ray (IOPA) / Bitewing | Interproximal caries risk, periapical radiolucency, bone-loss estimate |
| OPG (Panoramic) | Same as above, full-arch |
| CBCT (3D cone-beam) | Bone-density index for implant planning, mandibular-canal proximity, impacted teeth |
| **MRI (new)** | TMJ disc position (normal / anterior displacement with or without reduction), joint effusion, condylar morphology, sinus mucosal thickening, soft-tissue asymmetry flags |
| Intraoral 3D scan / Clinical photo | Stored for the chart; visual review only (no automated model yet) |

## How it works
1. `POST /imaging/upload` — multipart upload (patient_id, study_type, file). Stored under `uploads/imaging/`, row created in `imaging_studies`.
2. `POST /imaging/studies/{id}/analyze` — runs the analyzer:
   - If `PROVIDER_VISION_API_KEY` + `PROVIDER_VISION_URL` are set, calls the external vision model first (`provider_vision_analysis`).
   - Otherwise runs the built-in deterministic heuristic analyzer (`analyze_xray_or_opg`, `analyze_cbct`, `analyze_mri`) so the module works with zero external dependencies for demos/dev.
3. `POST /imaging/studies/{id}/review` — clinician sign-off (`CONFIRMED` / `REVISED` / `REJECTED`). Required before findings are considered part of the permanent chart.
4. `GET /imaging/mri/tmj-report/{id}` — patient-friendly one-paragraph MRI summary for printing/sharing.

## Governance (unchanged pattern from ai.py)
- Every analysis call is written to `ai_audit_logs` with `reviewed=false`.
- Every response includes `"disclaimer"` text and the UI always shows a "requires clinician review" state until reviewed.
- Swap in a real radiology/vision model by implementing `provider_vision_analysis()` — the local heuristic is a placeholder for demos, **not** a validated clinical model.

## Next steps for production
- Replace the heuristic analyzer with a validated DICOM-aware model (proper CBCT/MRI slice handling, not single-file JPG/PNG heuristics).
- Add a DICOM viewer (e.g. Cornerstone.js) instead of a plain `<img>` for CBCT/MRI series.
- Add consent capture before AI-assisted analysis of medical imaging, per local regulation.
