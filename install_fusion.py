#!/usr/bin/env python3
"""Install FUSION and its R initialization dependency from a source checkout."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True, env=env)


def install_r_dependencies() -> dict[str, str]:
    r = shutil.which("R")
    rscript = shutil.which("Rscript")
    if not r or not rscript:
        raise SystemExit(
            "R and Rscript were not found on PATH. Install R first, or rerun "
            "with --skip-r for a Python-only installation."
        )

    expression = """
cran <- "https://cloud.r-project.org"
if (getRversion() < "4.2.2") {
  stop("IRIS requires R 4.2.2 or newer.")
}
if (!requireNamespace("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager", repos = cran)
}
if (!requireNamespace("remotes", quietly = TRUE)) {
  install.packages("remotes", repos = cran)
}
options(repos = BiocManager::repositories())
if (
  Sys.info()[["sysname"]] == "Darwin" &&
  !requireNamespace("rliger", quietly = TRUE) &&
  !nzchar(Sys.which("gfortran"))
) {
  stop(
    "Installing IRIS on macOS requires gfortran. Install the CRAN macOS ",
    "toolchain from https://mac.r-project.org/tools/ and rerun this installer."
  )
}
bioc_dependencies <- c(
  "DelayedArray", "HDF5Array", "S4Vectors",
  "SingleCellExperiment", "SummarizedExperiment"
)
missing_bioc <- bioc_dependencies[
  !vapply(bioc_dependencies, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_bioc)) {
  BiocManager::install(missing_bioc, ask = FALSE, update = FALSE)
}
if (!requireNamespace("rliger", quietly = TRUE)) {
  package_type <- if (.Platform$OS.type == "windows") "binary" else "source"
  install.packages("rliger", repos = cran, type = package_type)
}
if (!requireNamespace("rliger", quietly = TRUE)) {
  stop(
    "The IRIS dependency 'rliger' could not be installed. Check the system ",
    "C/C++/Fortran toolchain, then rerun this installer."
  )
}
if (!requireNamespace("IRIS", quietly = TRUE)) {
  remotes::install_github(
    "YingMa0107/IRIS", dependencies = NA, upgrade = "never"
  )
}
if (!requireNamespace("Matrix", quietly = TRUE)) {
  stop("The required R package 'Matrix' is not installed.")
}
""".strip()
    try:
        run([rscript, "-e", expression])
    except subprocess.CalledProcessError as error:
        raise SystemExit(
            "R dependency installation failed. Read the actionable R error "
            "above, install any missing system compiler, and rerun this command."
        ) from error

    env = os.environ.copy()
    env["R_HOME"] = subprocess.check_output([r, "RHOME"], text=True).strip()
    return env


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install FUSION from this checkout, including IRIS by default."
    )
    parser.add_argument(
        "--skip-r",
        action="store_true",
        help="Install only Python dependencies; FUSION_Init will not be available.",
    )
    parser.add_argument(
        "--editable",
        action="store_true",
        help="Install the checkout in editable development mode.",
    )
    args = parser.parse_args()

    if sys.version_info < (3, 9):
        raise SystemExit("FUSION requires Python 3.9 or newer.")

    checkout = Path(__file__).resolve().parent
    env = os.environ.copy() if args.skip_r else install_r_dependencies()
    target = f"{checkout}[analysis]" if args.skip_r else f"{checkout}[full]"
    command = [sys.executable, "-m", "pip", "install"]
    if args.editable:
        command.append("--editable")
    command.append(target)
    run(command, env=env)

    run(
        [
            sys.executable,
            "-c",
            "import fusion; print(f'FUSION {fusion.__version__} installed')",
        ],
        env=env,
    )


if __name__ == "__main__":
    main()
