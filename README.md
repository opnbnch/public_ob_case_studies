# opnbnch

OpenBench strives to be the home for open, high quality ADME-Tox datasets and the gathering place for _in silico_ ADME-Tox discussion online. This repository is meant to host tools, datasets, and research, including supporting materials for the [OpenBench Weekly](https://opnbnch.substack.com/welcome) newsletter.

To understand why OpenBench exists, read [the manifesto.](https://opnbnch.substack.com/p/a-paradise-deferred)

For more insight into **case studies**, check out the [`case_studies`](./case_studies) directory. 

Tooling for data aggregation and cleaning is a work-in-progress.

## Getting started

The easiest way to get started with `opnbnchmark` is to install all the necessary dependencies with conda. If you have already installed miniconda, you can skip step 1. 

1. Install Miniconda from [https://conda.io/miniconda.html](https://conda.io/miniconda.html)
2. At the command line, `cd` into your opnbnchmark home directory. Once there: 
3. `conda env create -f environment.yml`
4. `conda activate opnbnchmark` (or `source activate opnbnchmark` for older versions of conda. After creating the envrionment, your console should instruct you on which to use.)
