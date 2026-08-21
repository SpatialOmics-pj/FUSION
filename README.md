# FUSION

FUSION is a research toolkit for multi-slice spatial transcriptomics. With a
matched single-cell RNA-seq reference, it supports joint dimensionality
reduction, spatial-domain clustering, cell-type deconvolution, cross-slice
alignment, and optional embedding correction.

> **Development status:** this repository currently contains the research
> implementation and example notebooks. Interfaces and output formats may
> change while the package is under active development.

## Installation

FUSION requires Python 3.9 or newer. The initialization step also requires R
4.2.2 or newer on `PATH`; the installer adds the R package
[IRIS](https://github.com/YingMa0107/IRIS) when needed. Because IRIS compiles
native code, a C/C++/Fortran toolchain is required. On macOS, install the
[official R development tools](https://mac.r-project.org/tools/), including
gfortran, before running the complete installer.

### Recommended: repository installer

```bash
git clone https://github.com/SpatialOmics-pj/FUSION.git
cd FUSION
python install_fusion.py
```

For a Python-only installation that omits `rpy2` and IRIS:

```bash
python install_fusion.py --skip-r
```

Python-only mode is useful for inspecting the package, but it cannot run
`FUSION_Init`.

JupyterLab is optional. Add it only when you want to run the bundled
notebooks:

```bash
python -m pip install ".[notebooks]"
```

### Install directly with pip

After R and IRIS are configured, install the complete package directly from
GitHub:

```bash
Rscript -e 'cran <- "https://cloud.r-project.org"; if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager", repos=cran); if (!requireNamespace("remotes", quietly=TRUE)) install.packages("remotes", repos=cran); options(repos=BiocManager::repositories()); BiocManager::install(c("SingleCellExperiment", "SummarizedExperiment", "DelayedArray", "HDF5Array", "S4Vectors"), ask=FALSE, update=FALSE); if (!requireNamespace("rliger", quietly=TRUE)) install.packages("rliger", repos=cran, type=if (.Platform$OS.type == "windows") "binary" else "source"); if (!requireNamespace("IRIS", quietly=TRUE)) remotes::install_github("YingMa0107/IRIS", dependencies=NA, upgrade="never")'
python -m pip install "fusion-srt[full] @ https://github.com/SpatialOmics-pj/FUSION/archive/refs/heads/main.zip"
```

Verify the installation:

```bash
python -c "import fusion; print(fusion.__version__)"
```

## Input data

FUSION expects:

| Input | Required content |
| --- | --- |
| Spatial slices | `AnnData` objects with raw spot-by-gene counts in `.X` and coordinates in `.obsm["spatial"]` |
| Single-cell reference | An `AnnData` object with raw cell-by-gene counts and `.obs["cellType"]` plus `.obs["sampleID"]` |

Gene identifiers must be consistent between the spatial and single-cell data.
Group slices from the same subject or condition in an inner list, then collect
those groups in `adata_list`.

## Minimal workflow

```python
import scanpy as sc
from fusion import FUSION_Init, FUSION_main, FUSION_preprocess, section_alignment

adata_list = [[
    sc.read_h5ad("dataset/SRT_data/151507_adata.h5ad"),
    sc.read_h5ad("dataset/SRT_data/151669_adata.h5ad"),
    sc.read_h5ad("dataset/SRT_data/151673_adata.h5ad"),
]]
sc_adata = sc.read_h5ad("path/to/your_sc_reference.h5ad")

domain_size = 7
seed = 123

# Creates intermediate files in ./preprocess_ref.
FUSION_Init(adata_list, sc_adata, domain_size=domain_size)
FUSION_preprocess(adata_list, log_fc_cut=1.5, seed=seed)

out, embeddings = FUSION_main(
    sp_slice_list=adata_list,
    topic_size=50,
    domain_size=domain_size,
    spatial_penalty=[(1.0, 1.0)],  # one pair for each outer group
    remove_tmp_files=True,
    device="cpu",
    seed=seed,
)

aligned_out = section_alignment(out, method="Distance")
```

`out` is a list of tables containing coordinates, domain assignments,
cell-type proportions, and slide indices. `embeddings` contains the learned
low-dimensional representation for each slice.

### Optional batch correction

```python
from fusion import FUSION_correction

corrected_embeddings = FUSION_correction(adata_list, embeddings, seed=seed)
```

The current `FUSION_correction` implementation requires a CUDA-capable GPU.
The core FUSION model can run with `device="cpu"` or a CUDA device supported by
PyTorch.

## Coding-agent support

This repository includes the
[`fusion-multislice`](.agents/skills/fusion-multislice/SKILL.md) skill. Codex
and compatible coding agents that scan `.agents/skills` can use it to:

- recognize multi-slice spatial transcriptomics requests suited to FUSION;
- validate AnnData structure before a long experiment;
- install Python, R, and IRIS dependencies;
- choose an explicit, reproducible workflow and preserve outputs;
- avoid unsupported assumptions, including CPU batch correction.

To make the skill available in another project, copy
`.agents/skills/fusion-multislice` into that project's `.agents/skills`
directory. In Codex, you can also explicitly request `$fusion-multislice`.

## Examples and repository layout

- `Jupyter notebook/DLPFC_all.ipynb`: end-to-end DLPFC example.
- `Jupyter notebook/DLPFC_batch_remove.ipynb`: embedding-correction example.
- `dataset/`: small example spatial files and a placeholder for your
  single-cell reference.
- `main_ref.py`, `R_initialization.py`, and `r_batch.py`: research
  implementation modules retained for compatibility with the notebooks.

The preprocessing stages write to `preprocess_ref/` in the current working
directory. Use a clean experiment directory, and set `remove_tmp_files=False`
in `FUSION_main` if those intermediate files are needed for debugging.

## Citation and support

Citation details will be added when the accompanying manuscript is public.
For installation problems or reproducible bug reports, open a
[GitHub issue](https://github.com/SpatialOmics-pj/FUSION/issues).
