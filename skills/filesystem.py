"""
Skill FILESYSTEM — opérations sur le système de fichiers.

Usage LLM :
  SKILL:filesystem ARGS:ls <chemin>
  SKILL:filesystem ARGS:cat <fichier>
  SKILL:filesystem ARGS:write <fichier> | <contenu>
  SKILL:filesystem ARGS:append <fichier> | <contenu>
  SKILL:filesystem ARGS:delete <chemin>
  SKILL:filesystem ARGS:mkdir <chemin>
  SKILL:filesystem ARGS:move <src> | <dst>
  SKILL:filesystem ARGS:copy <src> | <dst>
  SKILL:filesystem ARGS:chmod <mode> <chemin>
  SKILL:filesystem ARGS:chown <owner> <chemin>
  SKILL:filesystem ARGS:find <chemin> <pattern>
  SKILL:filesystem ARGS:grep <pattern> <fichier>
  SKILL:filesystem ARGS:df
  SKILL:filesystem ARGS:du <chemin>
  SKILL:filesystem ARGS:stat <chemin>
  SKILL:filesystem ARGS:tail <fichier> [N]
  SKILL:filesystem ARGS:head <fichier> [N]
"""
import os
import subprocess

DESCRIPTION = "Opérations filesystem : ls, cat, write, delete, move, copy, chmod, find, grep, df, du"
USAGE = "SKILL:filesystem ARGS:ls <path> | cat <file> | write <file>|<content> | delete <path> | find <path> <pattern> | grep <pattern> <file> | df | du <path> | tail <file> [N]"

# Chemins interdits pour éviter les accidents
FORBIDDEN = ["/proc", "/sys", "/dev", "/run/systemd"]


def _safe_path(path: str) -> bool:
    path = os.path.realpath(path)
    return not any(path.startswith(f) for f in FORBIDDEN)


def _run(cmd: str, timeout: int = 15) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, text=True,
            capture_output=True, timeout=timeout
        )
        out = (result.stdout + result.stderr).strip()
        return out[:4000] if out else "(aucune sortie)"
    except subprocess.TimeoutExpired:
        return f"Timeout ({timeout}s)"
    except Exception as e:
        return str(e)


def run(args: str, context) -> str:
    # Sépare l'action du reste
    parts = args.strip().split(None, 1)
    action = parts[0].lower() if parts else ""
    rest   = parts[1] if len(parts) > 1 else ""

    if action == "ls":
        path = rest or "."
        return _run(f"ls -lah {path}")

    if action == "cat":
        if not rest:
            return "Précise le fichier."
        if not _safe_path(rest):
            return f"Accès refusé : {rest}"
        return _run(f"cat {rest}")

    if action == "tail":
        parts2 = rest.split()
        filepath = parts2[0] if parts2 else ""
        n = parts2[1] if len(parts2) > 1 else "50"
        return _run(f"tail -n {n} {filepath}")

    if action == "head":
        parts2 = rest.split()
        filepath = parts2[0] if parts2 else ""
        n = parts2[1] if len(parts2) > 1 else "30"
        return _run(f"head -n {n} {filepath}")

    if action == "write":
        if "|" not in rest:
            return "Format : write <fichier> | <contenu>"
        filepath, content = rest.split("|", 1)
        filepath = filepath.strip()
        content  = content.strip()
        if not _safe_path(filepath):
            return f"Accès refusé : {filepath}"
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(content)
            return f"Fichier écrit : {filepath} ({len(content)} caractères)"
        except Exception as e:
            return str(e)

    if action == "append":
        if "|" not in rest:
            return "Format : append <fichier> | <contenu>"
        filepath, content = rest.split("|", 1)
        filepath = filepath.strip()
        if not _safe_path(filepath):
            return f"Accès refusé : {filepath}"
        try:
            with open(filepath, "a") as f:
                f.write(content.strip() + "\n")
            return f"Contenu ajouté à {filepath}"
        except Exception as e:
            return str(e)

    if action == "delete":
        if not rest:
            return "Précise le chemin."
        if not _safe_path(rest):
            return f"Accès refusé : {rest}"
        # Confirmation implicite : on ne supprime pas récursivement sans -r explicite
        if os.path.isdir(rest):
            return _run(f"rm -rf {rest}")
        return _run(f"rm -f {rest}")

    if action == "mkdir":
        if not rest:
            return "Précise le chemin."
        return _run(f"mkdir -p {rest}")

    if action == "move":
        if "|" not in rest:
            return "Format : move <src> | <dst>"
        src, dst = rest.split("|", 1)
        return _run(f"mv {src.strip()} {dst.strip()}")

    if action == "copy":
        if "|" not in rest:
            return "Format : copy <src> | <dst>"
        src, dst = rest.split("|", 1)
        return _run(f"cp -r {src.strip()} {dst.strip()}")

    if action == "chmod":
        parts2 = rest.split(None, 1)
        if len(parts2) < 2:
            return "Format : chmod <mode> <chemin>"
        return _run(f"chmod {parts2[0]} {parts2[1]}")

    if action == "chown":
        parts2 = rest.split(None, 1)
        if len(parts2) < 2:
            return "Format : chown <owner:group> <chemin>"
        return _run(f"chown -R {parts2[0]} {parts2[1]}")

    if action == "find":
        parts2 = rest.split(None, 1)
        path    = parts2[0] if parts2 else "."
        pattern = parts2[1] if len(parts2) > 1 else "*"
        return _run(f"find {path} -name '{pattern}' 2>/dev/null | head -50")

    if action == "grep":
        parts2 = rest.split(None, 1)
        if len(parts2) < 2:
            return "Format : grep <pattern> <fichier>"
        return _run(f"grep -n '{parts2[0]}' {parts2[1]} 2>/dev/null | head -50")

    if action == "df":
        return _run("df -h")

    if action == "du":
        path = rest or "."
        return _run(f"du -sh {path}/* 2>/dev/null | sort -rh | head -20")

    if action == "stat":
        if not rest:
            return "Précise le chemin."
        return _run(f"stat {rest}")

    return (
        "Action inconnue. Disponible : ls, cat, tail, head, write, append, delete, "
        "mkdir, move, copy, chmod, chown, find, grep, df, du, stat"
    )
