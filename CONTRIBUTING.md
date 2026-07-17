# Development Setup

1. Clone the repository.
2. Install dependencies and set up the environment:

    ```console
    $ uv sync
    ```

3. Install the pre-commit hooks:

    ```console
    $ uv run pre-commit install
    ```

## Conventions

- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `build:`, `ci:`, `chore:`, `test:`, etc.) — `python-semantic-release` parses these to determine version bumps and changelog entries. Only `feat:`, `fix:`, `perf:`, or a `BREAKING CHANGE:` footer trigger a release.
- Code is linted and formatted with `ruff`, enforced via pre-commit:

    ```console
    $ uv run ruff check src/ tests/
    $ uv run ruff format src/ tests/
    ```

- Notebook outputs are stripped before commit via `nbstripout` (also enforced via pre-commit).
- Run the test suite with:

    ```console
    $ uv run pytest
    ```
