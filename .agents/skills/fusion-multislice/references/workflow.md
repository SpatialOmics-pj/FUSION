# Reproducible FUSION workflow

## Installation outside a repository checkout

Confirm that R 4.2.2 or newer and `Rscript` are on `PATH`. IRIS requires a
C/C++/Fortran toolchain; on macOS, install the official R development tools,
including gfortran. Then run:

```bash
Rscript -e 'cran <- "https://cloud.r-project.org"; if (!requireNamespace("BiocManager", quietly=TRUE)) install.packages("BiocManager", repos=cran); if (!requireNamespace("remotes", quietly=TRUE)) install.packages("remotes", repos=cran); options(repos=BiocManager::repositories()); BiocManager::install(c("SingleCellExperiment", "SummarizedExperiment", "DelayedArray", "HDF5Array", "S4Vectors"), ask=FALSE, update=FALSE); if (!requireNamespace("rliger", quietly=TRUE)) install.packages("rliger", repos=cran, type=if (.Platform$OS.type == "windows") "binary" else "source"); if (!requireNamespace("IRIS", quietly=TRUE)) remotes::install_github("YingMa0107/IRIS", dependencies=NA, upgrade="never")'
python -m pip install "fusion-srt[full] @ https://github.com/SpatialOmics-pj/FUSION/archive/refs/heads/main.zip"
python -c "import fusion; print(fusion.__version__)"
```

Use an isolated virtual or Conda environment when possible. If R is not
available, a Python-only inspection install is possible, but initialization
and a complete experiment are not:

```bash
python -m pip install "fusion-srt[analysis] @ https://github.com/SpatialOmics-pj/FUSION/archive/refs/heads/main.zip"
```

## Data contract

Create a nested list where each inner list contains slices from one subject,
condition, or batch:

```python
adata_list = [
    [subject_1_slice_1, subject_1_slice_2],
    [subject_2_slice_1, subject_2_slice_2],
]
```

Each spatial `AnnData` requires:

- `.X`: raw, non-negative spot-by-gene counts;
- `.obsm["spatial"]`: numeric array with one row per spot and at least two
  coordinate columns;
- stable, preferably unique `.obs_names` and `.var_names`.

The reference `AnnData` requires:

- `.X`: raw, non-negative cell-by-gene counts;
- `.obs["cellType"]`: cell-type labels;
- `.obs["sampleID"]`: reference sample labels;
- gene identifiers compatible with every spatial slice.

## Model sequence

```python
from fusion import (
    FUSION_Init,
    FUSION_main,
    FUSION_preprocess,
    section_alignment,
)

domain_size = 7
topic_size = 50
log_fc_cut = 1.5
seed = 123
device = "cpu"

FUSION_Init(adata_list, sc_adata, domain_size=domain_size)
FUSION_preprocess(adata_list, log_fc_cut=log_fc_cut, seed=seed)

# Supply one penalty pair for each outer group in adata_list.
spatial_penalty = [(1.0, 1.0) for _ in adata_list]
out, embeddings = FUSION_main(
    sp_slice_list=adata_list,
    topic_size=topic_size,
    domain_size=domain_size,
    spatial_penalty=spatial_penalty,
    remove_tmp_files=False,
    device=device,
    seed=seed,
)
aligned_out = section_alignment(out, method="Distance")
```

`out` contains one table per outer group. Each table includes `x`, `y`,
`domain`, cell-type proportion columns, and `slide`. `embeddings` contains one
PyTorch tensor per spatial slice.

Only run the optional correction step when CUDA is available:

```python
import torch
from fusion import FUSION_correction

if not torch.cuda.is_available():
    raise RuntimeError("FUSION_correction currently requires CUDA")
corrected_embeddings = FUSION_correction(adata_list, embeddings, seed=seed)
```

## Output record

For every experiment, preserve:

- the ordered input paths and `adata_list` grouping;
- all parameter values and the seed;
- FUSION, Python, R, PyTorch, rpy2, IRIS, and CUDA versions;
- aligned result tables and embeddings;
- stdout/stderr logs and retained `preprocess_ref/` while debugging.

Use a timestamped or user-named output directory. Do not mutate the input
objects on disk unless the user explicitly requests derived `.h5ad` files.
