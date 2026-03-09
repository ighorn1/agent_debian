"""
Skill CRON — gestion des tâches cron.

Usage LLM :
  SKILL:cron ARGS:list [utilisateur]
  SKILL:cron ARGS:add <expression_cron> <commande>
  SKILL:cron ARGS:remove <pattern>
  SKILL:cron ARGS:system-list
"""
import subprocess
import tempfile
import os

DESCRIPTION = "Gestion des tâches cron (crontab)"
USAGE = "SKILL:cron ARGS:list | add <* * * * *> <commande> | remove <pattern> | system-list"


def _run(cmd: str, timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, text=True,
            capture_output=True, timeout=timeout
        )
        return (result.stdout + result.stderr).strip() or "(aucune sortie)"
    except Exception as e:
        return str(e)


def run(args: str, context) -> str:
    parts = args.strip().split(None, 1)
    action = parts[0].lower() if parts else "list"
    rest   = parts[1] if len(parts) > 1 else ""

    if action == "list":
        user = rest.strip() or ""
        flag = f"-u {user}" if user else ""
        result = _run(f"crontab {flag} -l 2>/dev/null")
        return result if result else "Crontab vide."

    if action == "add":
        # Format attendu : "* * * * * commande"
        # On split les 5 premiers champs (expression cron) + le reste (commande)
        words = rest.split()
        if len(words) < 6:
            return "Format : add <min> <heure> <jour> <mois> <jourSem> <commande>\nEx: add 0 3 * * * /usr/bin/apt-get update"
        cron_expr = " ".join(words[:5])
        command   = " ".join(words[5:])
        entry     = f"{cron_expr} {command}"

        # Récupère le crontab actuel, ajoute la ligne
        current = _run("crontab -l 2>/dev/null")
        if entry in current:
            return f"Cette entrée existe déjà : {entry}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as f:
            if current and "no crontab" not in current.lower():
                f.write(current + "\n")
            f.write(entry + "\n")
            tmpfile = f.name

        out = _run(f"crontab {tmpfile}")
        os.unlink(tmpfile)
        return f"Entrée ajoutée : {entry}\n{out}"

    if action == "remove":
        if not rest:
            return "Précise le pattern à supprimer."
        current = _run("crontab -l 2>/dev/null")
        lines = [l for l in current.splitlines() if rest not in l]
        new_cron = "\n".join(lines)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as f:
            f.write(new_cron + "\n")
            tmpfile = f.name

        out = _run(f"crontab {tmpfile}")
        os.unlink(tmpfile)
        removed = len(current.splitlines()) - len(lines)
        return f"{removed} entrée(s) supprimée(s) contenant '{rest}'.\n{out}"

    if action == "clear":
        return _run("crontab -r 2>/dev/null && echo 'Crontab effacé'")

    if action == "system-list":
        # Crons système dans /etc/cron.*
        out = []
        for d in ["/etc/cron.d", "/etc/cron.daily", "/etc/cron.weekly", "/etc/cron.monthly"]:
            files = _run(f"ls {d} 2>/dev/null")
            if files:
                out.append(f"{d}:\n{files}")
        return "\n\n".join(out) or "Aucun cron système trouvé."

    return "Action inconnue. Disponible : list, add, remove, clear, system-list"
