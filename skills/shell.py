"""
Skill SHELL — exécution de commandes shell arbitraires.
Skill de dernier recours quand aucun skill spécialisé ne convient.

Usage LLM : SKILL:shell ARGS:<commande bash>
"""
import subprocess

DESCRIPTION = "Exécution de commandes shell arbitraires (fallback général)"
USAGE = "SKILL:shell ARGS:<commande bash complète>"

# Commandes bloquées pour éviter les accidents critiques
BLOCKED = [
    "rm -rf /",
    "dd if=/dev/zero of=/dev/",
    "mkfs",
    "> /dev/sda",
    ":(){ :|:& };:",  # fork bomb
]


def run(args: str, context) -> str:
    cmd = args.strip()
    if not cmd:
        return "Commande vide."

    # Vérification des commandes dangereuses
    for blocked in BLOCKED:
        if blocked in cmd:
            return f"Commande bloquée pour sécurité : {blocked}"

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=60,
            executable="/bin/bash",
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        returncode = result.returncode

        output = ""
        if stdout:
            output += stdout
        if stderr:
            output += ("\n" if output else "") + f"[stderr] {stderr}"
        if not output:
            output = f"(Commande exécutée, code retour : {returncode})"

        # Tronqué à 4000 caractères
        if len(output) > 4000:
            output = output[:4000] + f"\n... [tronqué, {len(output)} caractères total]"

        return output

    except subprocess.TimeoutExpired:
        return "Timeout (60s) — commande trop longue."
    except Exception as e:
        return f"Erreur : {e}"
