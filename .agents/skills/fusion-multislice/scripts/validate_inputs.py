#!/usr/bin/env python3
"""Validate FUSION AnnData inputs before starting a long experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
from scipy import sparse


def matrix_minimum(matrix: Any) -> float:
    if hasattr(matrix, "to_memory"):
        matrix = matrix.to_memory()
    if sparse.issparse(matrix):
        return float(matrix.data.min()) if matrix.nnz else 0.0
    return float(np.asarray(matrix).min())


def validate_spatial(path: Path) -> tuple[ad.AnnData, dict[str, Any]]:
    adata = ad.read_h5ad(path, backed="r")
    errors: list[str] = []
    warnings: list[str] = []

    if "spatial" not in adata.obsm:
        errors.append('missing .obsm["spatial"]')
    else:
        coordinates = np.asarray(adata.obsm["spatial"])
        if coordinates.ndim != 2 or coordinates.shape[0] != adata.n_obs:
            errors.append("spatial coordinates do not match the number of spots")
        elif coordinates.shape[1] < 2:
            errors.append("spatial coordinates need at least two columns")
        elif not np.isfinite(coordinates[:, :2]).all():
            errors.append("spatial coordinates contain non-finite values")

    if matrix_minimum(adata.X) < 0:
        errors.append(".X contains negative values; raw counts are required")
    if not adata.obs_names.is_unique:
        warnings.append("spot identifiers are not unique")
    if not adata.var_names.is_unique:
        warnings.append("gene identifiers are not unique")

    return adata, {
        "path": str(path),
        "spots": adata.n_obs,
        "genes": adata.n_vars,
        "errors": errors,
        "warnings": warnings,
    }


def validate_reference(path: Path) -> tuple[ad.AnnData, dict[str, Any]]:
    adata = ad.read_h5ad(path, backed="r")
    errors: list[str] = []
    warnings: list[str] = []

    for column in ("cellType", "sampleID"):
        if column not in adata.obs:
            errors.append(f'missing .obs["{column}"]')
        elif adata.obs[column].isna().any():
            errors.append(f'.obs["{column}"] contains missing values')
    if matrix_minimum(adata.X) < 0:
        errors.append(".X contains negative values; raw counts are required")
    if not adata.var_names.is_unique:
        warnings.append("gene identifiers are not unique")

    return adata, {
        "path": str(path),
        "cells": adata.n_obs,
        "genes": adata.n_vars,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spatial", nargs="+", type=Path, help="Spatial .h5ad files")
    parser.add_argument("--reference", required=True, type=Path, help="Reference .h5ad file")
    args = parser.parse_args()

    reference, reference_report = validate_reference(args.reference)
    spatial_results = [validate_spatial(path) for path in args.spatial]
    spatial_reports = [report for _, report in spatial_results]
    reference_genes = set(reference.var_names)

    for spatial, report in spatial_results:
        shared = len(reference_genes.intersection(spatial.var_names))
        report["shared_reference_genes"] = shared
        if shared == 0:
            report["errors"].append("no genes overlap with the reference")
        elif shared < 100:
            report["warnings"].append(
                f"only {shared} genes overlap with the reference"
            )

    report = {"reference": reference_report, "spatial": spatial_reports}
    print(json.dumps(report, indent=2))
    has_errors = bool(reference_report["errors"]) or any(
        item["errors"] for item in spatial_reports
    )
    raise SystemExit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
