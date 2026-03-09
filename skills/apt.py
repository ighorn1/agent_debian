"""
Skill APT — gestion des paquets Debian.

Usage LLM :
  SKILL:apt ARGS:update
  SKILL:apt ARGS:upgrade
  SKILL:apt ARGS:install <paquet1> [paquet2...]
  SKILL:apt ARGS:remove <paquet>
  SKILL:apt ARGS:purge <paquet>
  SKILL:apt ARGS:search <terme>
  SKILL:apt ARGS:show <paquet>
  SKILL:apt ARGS:list-installed [filtre]
  SKILL:apt ARGS:list-upgradable
  SKILL:apt ARGS:autoremove
  SKILL:apt ARGS:check-updates
"""
import subprocess

DESCRIPTION = "Gestion des paquets Debian via apt/dpkg"
USAGE = "SKILL:apt ARGS:install <paquet> | remove <paquet> | update | upgrade | search <terme> | show <paquet> | list-installed | list-upgradable | autoremove"

ENV = {"DEBIAN_FRONTEND": "noninteractive", "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}


def _run(cmd: str, timeout: int = 120) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, text=True,
            capture_output=True, timeout=timeout, env=ENV
        )
        out = (result.stdout + result.stderr).strip()
        return out[:4000] if out else "(aucune sortie)"
    except subprocess.TimeoutExpired:
        return f"Timeout ({timeout}s) — commande trop longue."
    except Exception as e:
        return str(e)


def run(args: str, context) -> str:
    parts = args.strip().split(None, 1)
    action = parts[0].lower() if parts else ""
    extra  = parts[1] if len(parts) > 1 else ""

    if action == "update":
        return _run("apt-get update -q")

    if action == "upgrade":
        return _run("apt-get upgrade -y -q", timeout=300)

    if action == "dist-upgrade":
        return _run("apt-get dist-upgrade -y -q", timeout=300)

    if action == "install":
        if not extra:
            return "Précise le(s) paquet(s) à installer."
        return _run(f"apt-get install -y -q {extra}", timeout=180)

    if action == "remove":
        if not extra:
            return "Précise le paquet à supprimer."
        return _run(f"apt-get remove -y {extra}")

    if action == "purge":
        if not extra:
            return "Précise le paquet à purger."
        return _run(f"apt-get purge -y {extra}")

    if action == "autoremove":
        return _run("apt-get autoremove -y")

    if action == "search":
        if not extra:
            return "Précise le terme de recherche."
        return _run(f"apt-cache search {extra} | head -30")

    if action == "show":
        if not extra:
            return "Précise le paquet."
        return _run(f"apt-cache show {extra}")

    if action in ("list-installed", "list"):
        cmd = f"dpkg -l | grep '^ii' | awk '{{print $2\" \"$3}}'"
        if extra:
            cmd += f" | grep {extra}"
        return _run(cmd)

    if action == "list-upgradable":
        return _run("apt list --upgradable 2>/dev/null")

    if action == "check-updates":
        out = _run("apt-get -s upgrade 2>/dev/null | grep '^[0-9]'")
        return out or "Système à jour."

    if action == "hold":
        if not extra:
            return "Précise le paquet."
        return _run(f"apt-mark hold {extra}")

    if action == "unhold":
        if not extra:
            return "Précise le paquet."
        return _run(f"apt-mark unhold {extra}")

    return (
        "Action inconnue. Disponible : update, upgrade, install, remove, purge, "
        "search, show, list-installed, list-upgradable, autoremove, check-updates, hold, unhold"
    )
