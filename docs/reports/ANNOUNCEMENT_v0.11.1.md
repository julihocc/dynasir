# DynaSIR v0.11.1 Released

We’ve published dynasir v0.11.1. This release delivers comprehensive, publication-ready reporting tools while preserving full backward compatibility with v0.9.1 and v0.10.0.

Highlights:
- ModelReport class for one-line exports to Markdown, LaTeX tables, and high-DPI figures
- Multi-panel forecast visualization with confidence intervals
- Automated summary statistics and forecast accuracy evaluation
- Model comparison utilities (create_comparison_report)

Quality and validation:
- CI matrix (3.9, 3.10, 3.11, 3.12) fully passing
- Integration tests validate wheel installation
- All 7 example notebooks verified

Install:
```
pip install dynasir==0.11.1
python -c "import dynasir; print(dynasir.__version__)"  # should print 0.11.1
```

Links:
- GitHub Release: https://github.com/julihocc/dynasir/releases/tag/v0.11.1
- PyPI: https://pypi.org/project/dynasir/0.11.1/
- Reporting demo: examples/notebooks/07_reporting_and_publication.ipynb

Thanks to everyone who contributed to testing, docs, and CI improvements.