"""Commands for the currently implemented, explicitly incomplete port."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from .catalog import data
from .item import parse_label
from .scraper import parse_botls
from .terminal import Terminal, read_ttyrec
from .benchmark import parse_xlog, legitimate_ascension


def main():
    parser = argparse.ArgumentParser(description="BotHack Python — portage en cours, aucune ascension Python validée")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="État du portage et taille des tables originales")
    item = commands.add_parser("item", help="Analyser un libellé d’inventaire")
    item.add_argument("label")
    replay = commands.add_parser("replay", help="Relire un ttyrec ; cela ne joue pas une partie")
    replay.add_argument("file", type=Path)
    replay.add_argument("--records", type=int, default=0, help="Arrêter après N enregistrements, 0 = tous")
    replay.add_argument("--json", action="store_true")
    benchmark = commands.add_parser("report", help="Lire les résultats authentiques d’un xlogfile")
    benchmark.add_argument("xlogfile", type=Path)
    args = parser.parse_args()
    if args.command == "status":
        result = {"status": "incomplete", "python_ascensions": 0,
                  "items": len(data()["items"]), "monsters": len(data()["monsters"]),
                  "sokoban_layouts": len(data()["sokoban"]),
                  "missing": ["complete mainbot strategy", "game event integration", "full action/prompt handlers", "dungeon navigation", "identification event integration"]}
    elif args.command == "item":
        result = parse_label(args.label)
    elif args.command == "report":
        records = [parse_xlog(line) for line in args.xlogfile.read_text().splitlines() if line.strip()]
        result = {"recorded_games": len(records), "ascensions": sum(legitimate_ascension(r) for r in records), "records": records}
    else:
        terminal = Terminal()
        count = 0
        with args.file.open("rb") as stream:
            for record in read_ttyrec(stream):
                frame = terminal.feed(record.payload)
                count += 1
                if args.records and count >= args.records:
                    break
        frame = terminal.snapshot()
        if not args.json:
            print("\n".join(frame.lines))
            print(f"\n{count} enregistrements ; curseur ({frame.cursor.x}, {frame.cursor.y})")
            return
        result = {"records": count, "frame": asdict(frame), "status": parse_botls(frame.botls)}
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
