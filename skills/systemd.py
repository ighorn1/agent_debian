"""
Skill SYSTEMD — gestion des services systemd.

Usage LLM :
  SKILL:systemd ARGS:status <service>
  SKILL:systemd ARGS:start <service>
  SKILL:systemd ARGS:stop <service>
  SKILL:systemd ARGS:restart <service>
  SKILL:systemd ARGS:reload <service>
  SKILL:systemd ARGS:enable <service>
  SKILL:systemd ARGS:disable <service>
  SKILL:systemd ARGS:logs <service> [lignes]
  SKILL:systemd ARGS:list [pattern]
  SKILL:systemd ARGS:failed
  SKILL:systemd ARGS:daemon-reload
"""
import subprocess

DESCRIPTION = "Gestion des services systemd (start/stop/restart/status/logs/enable/disable)"
USAGE = "SKILL:systemd ARGS:status <service> | start <service> | stop <service> | restart <service> | enable <service> | disable <service> | logs <service> [N] | list | failed"


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


def run(args: str, context) -> str:
    parts = args.strip().split()
    action = parts[0].lower() if parts else ""
    service = parts[1] if len(parts) > 1 else ""

    if action == "status":
        if not service:
            return "Précise le service."
        return _run(f"systemctl status {service} --no-pager -l")

    if action == "start":
        if not service:
            return "Précise le service."
        out = _run(f"systemctl start {service}")
        status = _run(f"systemctl is-active {service}")
        return f"Démarrage de {service}... Statut : {status}\n{out}"

    if action == "stop":
        if not service:
            return "Précise le service."
        out = _run(f"systemctl stop {service}")
        status = _run(f"systemctl is-active {service}")
        return f"Arrêt de {service}... Statut : {status}\n{out}"

    if action == "restart":
        if not service:
            return "Précise le service."
        out = _run(f"systemctl restart {service}")
        status = _run(f"systemctl is-active {service}")
        return f"Redémarrage de {service}... Statut : {status}\n{out}"

    if action == "reload":
        if not service:
            return "Précise le service."
        return _run(f"systemctl reload {service}")

    if action == "enable":
        if not service:
            return "Précise le service."
        return _run(f"systemctl enable {service}")

    if action == "disable":
        if not service:
            return "Précise le service."
        return _run(f"systemctl disable {service}")

    if action == "mask":
        if not service:
            return "Précise le service."
        return _run(f"systemctl mask {service}")

    if action == "unmask":
        if not service:
            return "Précise le service."
        return _run(f"systemctl unmask {service}")

    if action == "logs":
        if not service:
            return "Précise le service."
        n = parts[2] if len(parts) > 2 else "50"
        try:
            n = int(n)
        except ValueError:
            n = 50
        return _run(f"journalctl -u {service} -n {n} --no-pager -o short-iso")

    if action == "list":
        pattern = parts[1] if len(parts) > 1 else ""
        cmd = "systemctl list-units --type=service --no-pager"
        if pattern:
            cmd += f" | grep {pattern}"
        return _run(cmd)

    if action == "list-all":
        return _run("systemctl list-units --type=service --all --no-pager")

    if action == "failed":
        return _run("systemctl list-units --state=failed --no-pager")

    if action == "daemon-reload":
        return _run("systemctl daemon-reload")

    if action == "is-active":
        if not service:
            return "Précise le service."
        return _run(f"systemctl is-active {service}")

    if action == "is-enabled":
        if not service:
            return "Précise le service."
        return _run(f"systemctl is-enabled {service}")

    return (
        "Action inconnue. Disponible : status, start, stop, restart, reload, "
        "enable, disable, mask, unmask, logs, list, list-all, failed, "
        "daemon-reload, is-active, is-enabled"
    )
