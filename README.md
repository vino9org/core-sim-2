
# Welcome to your Python project

This project is set up Python project with dev tooling pre-configured

* ruff
* mypy
* VS Code support

## Setup

The easiest way to get started is use [Visual Studio Code with devcontainer](https://code.visualstudio.com/docs/devcontainers/containers)

[rye](https://github.com/astral-sh/rye) is the blazing fast python project manager tool. Install it first before proceeding.


```shell

# create virtualenv and install dependencies
rye sync

```

## Develop the code for the stack

```shell

# update your DATABASE_URL is used
# create database and assign proper privileges to the user
# e.g.
# create database mydb;
# grant all privileges on database mydb to me;

nano .env

# run alembic migration
alembic upgrade head

# run unit tests
pytest

```

## generate code using config file without interactive input

Create a [config file](sample_prog.json) with options to use, then

```shell

cat <<EOF > config.json
{
    "default_context": {
        "project_name": "Some Program",
        "project_slug": "some_prog",
        "pkg_name": "some_prog",
        "project_short_description": "Some python program",
        "dockerfile_option": "Dockerfile with Github workflow",
        "extra_packages": "None",
        "version": "0.1.0"
    }
}
EOF


cookiecutter gh:vino9org/cookiecutter-python --config-file config.json --no-input

```
