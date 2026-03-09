"""
Skill CONTAINER — gestion des conteneurs Docker et LXC/LXD.

Usage LLM :
  SKILL:container ARGS:docker ps [all]
  SKILL:container ARGS:docker start <nom>
  SKILL:container ARGS:docker stop <nom>
  SKILL:container ARGS:docker restart <nom>
  SKILL:container ARGS:docker logs <nom> [N]
  SKILL:container ARGS:docker stats
  SKILL:container ARGS:docker images
  SKILL:container ARGS:docker pull <image>
  SKILL:container ARGS:docker rm <nom>
  SKILL:container ARGS:docker rmi <image>
  SKILL:container ARGS:docker exec <nom> <commande>
  SKILL:container ARGS:docker inspect <nom>
  SKILL:container ARGS:lxc list
  SKILL:container ARGS:lxc start <nom>
  SKILL:container ARGS:lxc stop <nom>
  SKILL:container ARGS:lxc exec <nom> <commande>
  SKILL:container ARGS:lxc info <nom>
"""
import subprocess

DESCRIPTION = "Gestion conteneurs Docker et LXC/LXD : start, stop, logs, exec, stats, images"
USAGE = "SKILL:container ARGS:docker ps|start|stop|restart|logs|exec|stats|images|pull | lxc list|start|stop|exec|info"


def _run(cmd: str, timeout: int = 30) -> str:
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


def _docker(action: str, args: list) -> str:
    a = args[0] if args else ""

    if action == "ps":
        flag = "-a" if (a == "all" or a == "-a") else ""
        return _run(f"docker ps {flag} --format 'table {{{{.Names}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Ports}}}}'")

    if action == "start":
        return _run(f"docker start {a}") if a else "Précise le nom du conteneur."

    if action == "stop":
        return _run(f"docker stop {a}") if a else "Précise le nom du conteneur."

    if action == "restart":
        return _run(f"docker restart {a}") if a else "Précise le nom du conteneur."

    if action == "logs":
        if not a:
            return "Précise le nom du conteneur."
        n = args[1] if len(args) > 1 else "50"
        return _run(f"docker logs --tail {n} {a}")

    if action == "stats":
        return _run("docker stats --no-stream --format 'table {{{{.Name}}}}\\t{{{{.CPUPerc}}}}\\t{{{{.MemUsage}}}}'")

    if action == "images":
        return _run("docker images --format 'table {{{{.Repository}}}}\\t{{{{.Tag}}}}\\t{{{{.Size}}}}\\t{{{{.CreatedSince}}}}'")

    if action == "pull":
        return _run(f"docker pull {a}", timeout=120) if a else "Précise l'image."

    if action == "rm":
        return _run(f"docker rm {a}") if a else "Précise le nom du conteneur."

    if action == "rm-stopped":
        return _run("docker container prune -f")

    if action == "rmi":
        return _run(f"docker rmi {a}") if a else "Précise l'image."

    if action == "exec":
        if len(args) < 2:
            return "Format : docker exec <conteneur> <commande>"
        container = args[0]
        cmd = " ".join(args[1:])
        return _run(f"docker exec {container} {cmd}")

    if action == "inspect":
        return _run(f"docker inspect {a}") if a else "Précise le nom du conteneur."

    if action == "network":
        return _run("docker network ls")

    if action == "volumes":
        return _run("docker volume ls")

    if action == "compose-up":
        return _run("docker compose up -d", timeout=120) if not a else _run(f"docker compose -f {a} up -d", timeout=120)

    if action == "compose-down":
        return _run("docker compose down")

    return f"Action docker inconnue : {action}"


def _lxc(action: str, args: list) -> str:
    a = args[0] if args else ""

    if action == "list":
        return _run("lxc list --format table 2>/dev/null || lxc-ls -f 2>/dev/null")

    if action == "start":
        return _run(f"lxc start {a}") if a else "Précise le nom."

    if action == "stop":
        return _run(f"lxc stop {a}") if a else "Précise le nom."

    if action == "restart":
        return _run(f"lxc restart {a}") if a else "Précise le nom."

    if action == "exec":
        if len(args) < 2:
            return "Format : lxc exec <conteneur> <commande>"
        cmd = " ".join(args[1:])
        return _run(f"lxc exec {a} -- {cmd}")

    if action == "info":
        return _run(f"lxc info {a}") if a else _run("lxc info")

    if action == "snapshot":
        return _run(f"lxc snapshot {a}") if a else "Précise le nom."

    if action == "delete":
        return _run(f"lxc delete {a} --force") if a else "Précise le nom."

    return f"Action lxc inconnue : {action}"


def run(args: str, context) -> str:
    parts = args.strip().split()
    if not parts:
        return "Précise : docker ou lxc suivi d'une action."

    runtime = parts[0].lower()
    action  = parts[1].lower() if len(parts) > 1 else "ps"
    rest    = parts[2:] if len(parts) > 2 else []

    if runtime == "docker":
        return _docker(action, rest)

    if runtime in ("lxc", "lxd"):
        return _lxc(action, rest)

    # Tentative de détection auto
    if runtime in ("ps", "stats", "images", "logs", "start", "stop", "restart", "exec"):
        return _docker(runtime, parts[1:])

    return "Précise le runtime : docker ou lxc. Ex: SKILL:container ARGS:docker ps"
