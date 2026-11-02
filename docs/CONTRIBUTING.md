# Contributing to DynaSIR

We welcome contributions from the community! Whether you're a developer, a data scientist, or just someone with a good idea, we encourage you to get involved.

## Getting Started

1.  Fork the repository on GitHub.
2.  Clone your fork locally:

    ```bash
    git clone https://github.com/your-username/dynasir.git
    ```

3.  Create a new branch for your changes:

    ```bash
    git checkout -b my-feature-branch
    ```

4.  Make your changes and commit them with a clear and concise message.

5.  Push your changes to your fork:

    ```bash
    git push origin my-feature-branch
    ```

6.  Open a pull request on the main repository.

## Running Tests

We use `pytest` for testing. To run the tests, first install the development dependencies:

```bash
pip install -e ".[dev,test]"
```

Then, run `pytest` from the root directory of the project:

```bash
pytest
```

This will automatically discover and run all the tests in the `tests` directory.

## Coding Style

We use `black` for code formatting and `flake8` for linting. We also use `mypy` for static type checking. These tools are configured in the `pyproject.toml` file and are enforced by the pre-commit hooks.

Before committing your changes, please make sure to run the pre-commit hooks to ensure your code follows our coding style. You can install the pre-commit hooks by running:

```bash
pre-commit install
```

## Documentation

We use Sphinx for generating documentation. The documentation is located in the `docs` directory. To build the documentation, first install the documentation dependencies:

```bash
pip install -e ".[docs]"
```

Then, navigate to the `docs` directory and run:

```bash
make html
```

The generated HTML files will be in the `docs/_build/html` directory.

## Reporting Bugs

If you find a bug, please open an issue on our GitHub repository. Please include as much detail as possible, including:

*   A clear and concise description of the bug.
*   Steps to reproduce the bug.
*   The expected behavior.
*   The actual behavior.
*   Your operating system and Python version.

## Suggesting Enhancements

If you have an idea for a new feature or an enhancement to an existing feature, please open an issue on our GitHub repository. Please include a clear and concise description of the enhancement, as well as any relevant context or examples.
