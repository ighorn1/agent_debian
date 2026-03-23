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


def _confirm_or_execute(context, description: str, action_fn) -> str:
    """Demande confirmation si requête XMPP directe, sinon exécute immédiatement."""
    sender = getattr(context.agent, '_last_xmpp_sender', '')
    if not sender:
        return action_fn()
    context.agent._pending_confirmations[sender] = {"description": description, "fn": action_fn}
    return f"⚠️ Confirmation requise :\n{description}\n\nRéponds **oui** pour confirmer ou **non** pour annuler."


def _run(cmd: str, timeout: int = 10) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, text=True,
            capture_output=True, timeout=timeout
        )
        return (result.stdout + result.stderr).strip() or "(aucune sortie)"
    except Exception as e:
        return str(e)


def _get_current_crontab() -> str:
    """Retourne le crontab actuel, ou chaîne vide si inexistant."""
    result = subprocess.run(
        "crontab -l", shell=True, text=True, capture_output=True
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


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
        words = rest.split()
        if len(words) < 6:
            return "Format : add <min> <heure> <jour> <mois> <jourSem> <commande>\nEx: add 0 3 * * * /usr/bin/apt-get update"
        cron_expr = " ".join(words[:5])
        command   = " ".join(words[5:])
        entry     = f"{cron_expr} {command}"

        current = _get_current_crontab()
        if entry in current:
            return f"Cette entrée existe déjà : {entry}"

        def _do_add():
            with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as f:
                if current:
                    f.write(current + "\n")
                f.write(entry + "\n")
                tmpfile = f.name
            result = subprocess.run(f"crontab {tmpfile}", shell=True, text=True, capture_output=True)
            os.unlink(tmpfile)
            if result.returncode != 0:
                return f"❌ Erreur crontab : {(result.stdout + result.stderr).strip()}"
            return f"✅ Entrée ajoutée : {entry}"

        return _confirm_or_execute(context, f"Ajouter cron : {entry}", _do_add)

    if action == "remove":
        if not rest:
            return "Précise le pattern à supprimer."
        current = _get_current_crontab()
        lines = [l for l in current.splitlines() if rest not in l]
        removed_count = len(current.splitlines()) - len(lines)
        if removed_count == 0:
            return f"Aucune entrée contenant '{rest}' trouvée."

        def _do_remove():
            new_cron = "\n".join(lines)
            with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as f:
                f.write(new_cron + "\n")
                tmpfile = f.name
            result = subprocess.run(f"crontab {tmpfile}", shell=True, text=True, capture_output=True)
            os.unlink(tmpfile)
            if result.returncode != 0:
                return f"❌ Erreur crontab : {(result.stdout + result.stderr).strip()}"
            return f"✅ {removed_count} entrée(s) supprimée(s) contenant '{rest}'."

        return _confirm_or_execute(context, f"Supprimer {removed_count} cron contenant '{rest}'", _do_remove)

    if action == "clear":
        return _confirm_or_execute(
            context,
            "Effacer TOUT le crontab root (action irréversible)",
            lambda: _run("crontab -r 2>/dev/null && echo 'Crontab effacé'")
        )

    if action == "system-list":
        # Crons système dans /etc/cron.*
        out = []
        for d in ["/etc/cron.d", "/etc/cron.daily", "/etc/cron.weekly", "/etc/cron.monthly"]:
            files = _run(f"ls {d} 2>/dev/null")
            if files:
                out.append(f"{d}:\n{files}")
        return "\n\n".join(out) or "Aucun cron système trouvé."

    return "Action inconnue. Disponible : list, add, remove, clear, system-list"
