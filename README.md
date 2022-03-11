# AWS Tower

Swiss knife for tedious AWS tasks

## Installing

1. Install python3
2. Install `poetry` [following official instructions](https://python-poetry.org/docs/master/#installing-with-the-official-installer)
3. Run `peotry install` in the folder
4. Run `poetry shell`

## Usage

When you have activated the `poetry` virtual environment, you can run:

```shell
python tower.py --help
```

That will give you the commands and options that you can run. For all AWS operations you will need to be authenticated.

## Development

### Libraries

#### Typer

For the CLI functionality, we are using `typer`. It can do a lot of heavy lifting when it comes to a CLI application.

[Official documentation](https://typer.tiangolo.com/)


## TODO
- [ ] new name
- [ ] expand the coverage
- [ ] add tests