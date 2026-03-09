"""
Skill JOURNAL — consultation des logs système via journalctl.

Usage LLM :
  SKILL:journal ARGS:tail [N]
  SKILL:journal ARGS:service <service> [N]
  SKILL:journal ARGS:boot [N]
  SKILL:journal ARGS:errors [N]
  SKILL:journal ARGS:since <durée> (ex: "1h", "30min", "yesterday")
  SKILL:journal ARGS:grep <pattern> [service]
  SKILL:journal ARGS:kernel [N]
  SKILL:journal ARGS:disk-usage
"""
import subprocess

DESCRIPTION = "Consultation des logs système via journalctl et /var/log"
USAGE = "SKILL:journal ARGS:tail [N] | service <service> [N] | errors [N] | since <durée> | grep <pattern> | boot | kernel"


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
    parts = args.strip().split(None, 1)
    action = parts[0].lower() if parts else "tail"
    rest   = parts[1] if len(parts) > 1 else ""

    if action == "tail":
        n = rest.strip() or "50"
        return _run(f"journalctl -n {n} --no-pager -o short-iso")

    if action == "service":
        parts2 = rest.split()
        service = parts2[0] if parts2 else ""
        n       = parts2[1] if len(parts2) > 1 else "50"
        if not service:
            return "Précise le service."
        return _run(f"journalctl -u {service} -n {n} --no-pager -o short-iso")

    if action == "boot":
        n = rest.strip() or "50"
        return _run(f"journalctl -b -n {n} --no-pager -o short-iso")

    if action == "errors":
        n = rest.strip() or "30"
        return _run(f"journalctl -p err..emerg -n {n} --no-pager -o short-iso")

    if action == "warnings":
        n = rest.strip() or "30"
        return _run(f"journalctl -p warning..emerg -n {n} --no-pager -o short-iso")

    if action == "since":
        if not rest:
            return "Précise la durée (ex: '1h', '30min', 'yesterday', '2024-01-01')"
        # Convertit "1h" → "1 hour ago", "30min" → "30 minutes ago"
        since = rest.strip()
        if since.endswith("h") and since[:-1].isdigit():
            since = f"{since[:-1]} hours ago"
        elif since.endswith("min") and since[:-3].isdigit():
            since = f"{since[:-3]} minutes ago"
        return _run(f"journalctl --since='{since}' --no-pager -o short-iso | tail -100")

    if action == "grep":
        parts2 = rest.split(None, 1)
        pattern = parts2[0] if parts2 else ""
        service = parts2[1].strip() if len(parts2) > 1 else ""
        if not pattern:
            return "Précise le pattern."
        cmd = f"journalctl --no-pager -o short-iso"
        if service:
            cmd += f" -u {service}"
        cmd += f" | grep -i '{pattern}' | tail -50"
        return _run(cmd)

    if action == "kernel":
        n = rest.strip() or "30"
        return _run(f"journalctl -k -n {n} --no-pager -o short-iso")

    if action == "disk-usage":
        return _run("journalctl --disk-usage")

    if action == "vacuum":
        # Nettoyage des vieux logs
        size = rest.strip() or "500M"
        return _run(f"journalctl --vacuum-size={size}")

    if action == "file":
        # Lire un fichier de log classique
        filepath = rest.strip()
        if not filepath:
            return "Précise le fichier."
        return _run(f"tail -100 {filepath}")

    return (
        "Action inconnue. Disponible : tail, service, boot, errors, warnings, "
        "since, grep, kernel, disk-usage, vacuum, file"
    )
