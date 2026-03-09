"""
Skill PROCESS — gestion des processus.

Usage LLM :
  SKILL:process ARGS:list [filtre]
  SKILL:process ARGS:top [N]
  SKILL:process ARGS:kill <pid> [signal]
  SKILL:process ARGS:killall <nom>
  SKILL:process ARGS:nice <pid> <priorité>
  SKILL:process ARGS:info <pid>
  SKILL:process ARGS:tree
  SKILL:process ARGS:find <nom>
"""
import subprocess

DESCRIPTION = "Gestion des processus : list, top, kill, killall, nice, find"
USAGE = "SKILL:process ARGS:list [filtre] | top [N] | kill <pid> [signal] | killall <nom> | info <pid> | tree | find <nom>"


def _run(cmd: str, timeout: int = 10) -> str:
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
    parts = args.strip().split(None, 1)
    action = parts[0].lower() if parts else "list"
    rest   = parts[1] if len(parts) > 1 else ""

    if action == "list":
        cmd = "ps aux --sort=-%cpu | head -30"
        if rest:
            cmd = f"ps aux | grep -i {rest} | grep -v grep"
        return _run(cmd)

    if action == "top":
        n = rest.strip() or "15"
        return _run(
            f"ps aux --sort=-%cpu | head -{n} | "
            "awk 'NR==1{print} NR>1{printf \"%-10s %-6s %-5s %-5s %s\\n\",$1,$2,$3,$4,$11}'"
        )

    if action == "kill":
        parts2 = rest.split()
        if not parts2:
            return "Précise le PID."
        pid    = parts2[0]
        signal = parts2[1] if len(parts2) > 1 else "15"
        return _run(f"kill -{signal} {pid}")

    if action == "kill9":
        if not rest:
            return "Précise le PID."
        return _run(f"kill -9 {rest.strip()}")

    if action == "killall":
        if not rest:
            return "Précise le nom du processus."
        return _run(f"killall {rest.strip()}")

    if action == "nice":
        parts2 = rest.split()
        if len(parts2) < 2:
            return "Format : nice <pid> <priorité (-20 à 19)>"
        pid, prio = parts2[0], parts2[1]
        return _run(f"renice {prio} -p {pid}")

    if action == "info":
        if not rest:
            return "Précise le PID."
        pid = rest.strip()
        out = _run(f"ps -p {pid} -o pid,ppid,user,%cpu,%mem,vsz,rss,stat,start,time,comm --no-headers")
        cmdline = _run(f"cat /proc/{pid}/cmdline 2>/dev/null | tr '\\0' ' '")
        return f"Process {pid}:\n{out}\nCmdline: {cmdline}"

    if action == "tree":
        return _run("pstree -p | head -50")

    if action == "find":
        if not rest:
            return "Précise le nom du processus."
        return _run(f"pgrep -a -i {rest.strip()}")

    if action == "lsof":
        # Fichiers ouverts par un processus
        if rest:
            return _run(f"lsof -p {rest.strip()} | head -30")
        return _run("lsof | wc -l && echo fichiers ouverts au total")

    return "Action inconnue. Disponible : list, top, kill, kill9, killall, nice, info, tree, find, lsof"
