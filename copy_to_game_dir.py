import argparse
from pathlib import Path
import shutil
import sys
import fnmatch

parser = argparse.ArgumentParser(description="Copy Mod Organizer mod files to game dir")
parser.add_argument("target_dir", type=Path, help="target (game) directory")
parser.add_argument(
    "modlist",
    nargs="?",
    type=Path,
    help="modlist.txt from MO, with +enabled and -disabled mods",
    default=Path("profiles/Weedheim/modlist.txt"),
)
parser.add_argument(
    "-m",
    "--modsdir",
    type=Path,
    default=Path("mods"),
    help="dir to (MOs) mods directory",
)
parser.add_argument(
    "-l", "--hardlink", action="store_true", help="use hardlinks instead of copies"
)
parser.add_argument(
    "-e", "--exclude", nargs="+", default=["meta.ini"], help="exclude mod file patterns"
)


def copy_tree(
    source: Path,
    destination: Path,
    dirs_exist_ok: bool = False,
    ignore_patterns: list[str] | None = None,
    use_hardlinks: bool = False,
):
    """similar to `shutil.copytree` with hardlink option"""
    for root, dirs, files in source.walk():
        rel_root = root.relative_to(source)
        for dir in dirs:
            rel_dir = rel_root / dir
            if ignore_patterns and any(
                fnmatch.fnmatch(str(rel_dir), pat) for pat in ignore_patterns
            ):
                continue
            (destination / rel_dir).mkdir(exist_ok=dirs_exist_ok)
        for file in files:
            rel_file = rel_root / file
            if ignore_patterns and any(
                fnmatch.fnmatch(str(rel_file), pat) for pat in ignore_patterns
            ):
                continue
            target = destination / rel_file
            if use_hardlinks:
                if dirs_exist_ok and target.exists():
                    target.unlink()
                target.hardlink_to(root / file)
            else:
                shutil.copy2(root / file, target)


if __name__ == "__main__":
    args = parser.parse_args()
    modsdir: Path = args.modsdir
    target_dir: Path = args.target_dir
    if (
        args.hardlink
        and (abs_modsdir := modsdir.resolve()).drive
        != (abs_target_dir := target_dir.resolve()).drive
    ):
        print(
            f"Hardlinks can only be created on the same drive! {abs_modsdir} -> {abs_target_dir}",
            file=sys.stderr,
        )
        exit(1)
    target_dir.mkdir(exist_ok=True, parents=True)
    with open(args.modlist) as modlist:
        for line in modlist:
            if not line.startswith("+"):
                continue
            mod = line.lstrip("+").rstrip("\n")
            mod_dir = modsdir / mod
            copy_tree(
                mod_dir,
                target_dir,
                dirs_exist_ok=True,
                ignore_patterns=args.exclude,
                use_hardlinks=args.hardlink,
            )
