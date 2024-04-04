import re
import sys
from os import path
from typing import Generator

import click

from twitchdl import twitch, utils
from twitchdl.commands.download import get_clip_authenticated_url
from twitchdl.download import download_file
from twitchdl.output import green, print_clip, print_json, print_paged, yellow
from twitchdl.twitch import Clip


def clips(
    channel_name: str,
    *,
    all: bool = False,
    download: bool = False,
    json: bool = False,
    limit: int = 10,
    pager: int | None = None,
    period: twitch.ClipsPeriod = "all_time",
):
    # Ignore --limit if --pager or --all are given
    limit = sys.maxsize if all or pager else limit

    generator = twitch.channel_clips_generator(channel_name, period, limit)

    if json:
        return print_json(list(generator))

    if download:
        return _download_clips(generator)

    if pager:
        return print_paged("Clips", generator, print_clip, pager)

    return _print_all(generator, all)


def _continue():
    enter = click.style("Enter", bold=True, fg="green")
    ctrl_c = click.style("Ctrl+C", bold=True, fg="yellow")
    click.echo(f"Press {enter} to continue, {ctrl_c} to break.")

    try:
        input()
    except KeyboardInterrupt:
        return False

    return True


def _target_filename(clip: Clip):
    url = clip["videoQualities"][0]["sourceURL"]
    _, ext = path.splitext(url)
    ext = ext.lstrip(".")

    match = re.search(r"^(\d{4})-(\d{2})-(\d{2})T", clip["createdAt"])
    if not match:
        raise ValueError(f"Failed parsing date from: {clip['createdAt']}")
    date = "".join(match.groups())

    name = "_".join(
        [
            date,
            clip["id"],
            clip["broadcaster"]["login"],
            utils.slugify(clip["title"]),
        ]
    )

    return f"{name}.{ext}"


def _download_clips(generator: Generator[Clip, None, None]):
    for clip in generator:
        target = _target_filename(clip)

        if path.exists(target):
            click.echo(f"Already downloaded: {green(target)}")
        else:
            url = get_clip_authenticated_url(clip["slug"], "source")
            click.echo(f"Downloading: {yellow(target)}")
            download_file(url, target)


def _print_all(generator: Generator[Clip, None, None], all: bool):
    for clip in generator:
        click.echo()
        print_clip(clip)

    if not all:
        click.secho(
            "\nThere may be more clips. "
            + "Increase the --limit, use --all or --pager to see the rest.",
            dim=True,
        )
