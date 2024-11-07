"""Console script for sharpener."""

import sys
import click

from sharpener.commands import koji, rpm, gerrit, spec
from sharpener.commands.koji import task, admin, build, check


def show_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Version 1.0.0')
    ctx.exit()


@click.group(invoke_without_command=True)
@click.option(
    '--version',
    is_flag=True,
    callback=show_version,
    expose_value=False,
    is_eager=True,
    help='Show version',
)
def run():
    pass


def main():
    run.add_command(koji.group)
    run.add_command(rpm.group)
    run.add_command(gerrit.group)
    run.add_command(spec.group)
    sys.exit(run())


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
