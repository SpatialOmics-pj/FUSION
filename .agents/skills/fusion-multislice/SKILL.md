---
name: fusion-multislice
description: Install and run SpatialOmics-pj/FUSION for multi-slice or multi-section spatial transcriptomics, including dimensionality reduction, spatial-domain clustering, reference-based cell-type deconvolution, cross-slice alignment, and optional batch correction. Use when a coding agent is asked to analyze several spatial transcriptomics slices with FUSION or a matched scRNA-seq reference. Do not use for generic data fusion, media fusion, nuclear fusion, or single-slice analyses that do not need FUSION.
---

# FUSION multi-slice analysis

Use this skill to turn an experiment request into an installed, validated, and
reproducible FUSION run. Read [references/workflow.md](references/workflow.md)
before writing or executing an analysis.

## Required sequence

1. Identify the experiment directory and preserve the user's existing files.
2. Record Python, R, PyTorch, CUDA, and FUSION versions before analysis.
3. Install FUSION with the repository installer when working in a checkout:

   ```bash
   python install_fusion.py
   ```

   Outside a checkout, install IRIS and the complete GitHub package as shown
   in `references/workflow.md`. Do not claim that a Python-only installation
   can run initialization.
4. Validate every spatial slice and the single-cell reference before a long
   run. When file paths are available, run:

   ```bash
   python .agents/skills/fusion-multislice/scripts/validate_inputs.py \
     --reference path/to/reference.h5ad slice1.h5ad slice2.h5ad
   ```

5. Ask for or explicitly record `domain_size`, `topic_size`,
   `spatial_penalty`, `log_fc_cut`, `seed`, and `device`. Do not silently
   invent scientific parameters. A small smoke run may use clearly labeled
   provisional values.
6. Run initialization, preprocessing, model fitting, and alignment in that
   order. Keep a record of slice grouping because the outer `adata_list`
   structure defines subjects or conditions.
7. Save result tables, embeddings, parameters, software versions, and logs in
   a new output directory. Do not overwrite source `.h5ad` files.
8. Report completed stages and exact output paths. If a stage fails, preserve
   `preprocess_ref/` and report the first actionable error.

## Hard constraints

- Spatial inputs need raw spot-by-gene counts in `.X` and two-dimensional
  coordinates in `.obsm["spatial"]`.
- The reference needs raw cell-by-gene counts plus `.obs["cellType"]` and
  `.obs["sampleID"]`.
- Spatial and reference objects need compatible gene identifiers.
- `FUSION_Init` requires R 4.2.2 or newer, `rpy2`, R `Matrix`, and R
  `IRIS`. IRIS compilation needs a C/C++/Fortran toolchain; macOS needs the
  official R development tools including gfortran.
- The current `FUSION_correction` implementation is CUDA-only. Skip it on a
  CPU-only host and explain the limitation; the core model may still use CPU.
- `FUSION_main(remove_tmp_files=True)` removes `preprocess_ref/`. Use `False`
  while diagnosing or when intermediates must be retained.
- Treat the code and notebooks as research software. Never interpret domain
  labels or cell proportions as clinically validated results.

## Compatibility

Prefer the public `fusion` imports documented in the workflow. The historical
top-level imports (`main_ref`, `R_initialization`, `r_batch`, `utils`) remain
available for existing notebooks.
