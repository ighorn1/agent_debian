"""
Skill SCRIPT — créer et exécuter un script bash, avec renvoi du résultat via MQTT.

L'environnement du script expose automatiquement :
  MQTT_BROKER, MQTT_REPLY_TOPIC, AGENT_ID

Ainsi un script peut publier son résultat directement :
  mosquitto_pub -h $MQTT_BROKER -t $MQTT_REPLY_TOPIC -m "mon résultat"

Usage LLM :
  SKILL:script ARGS:run | <contenu du script>
  SKILL:script ARGS:save <nom> | <contenu>
  SKILL:script ARGS:exec <nom> [args]
  SKILL:script ARGS:list
  SKILL:script ARGS:show <nom>
  SKILL:script ARGS:delete <nom>
"""
import os
import subprocess
import stat

DESCRIPTION = "Créer/exécuter des scripts bash avec renvoi du résultat via MQTT"
USAGE = "SKILL:script ARGS:run|<contenu> | save <nom>|<contenu> | exec <nom> | list | show <nom>"

SCRIPTS_DIR = "/opt/agent_debian/scripts"


def _ensure_dir():
    os.makedirs(SCRIPTS_DIR, exist_ok=True)


def _run(cmd: str, env: dict = None, timeout: int = 60) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, text=True,
            capture_output=True, timeout=timeout,
            env=env, executable="/bin/bash"
        )
        out = (result.stdout + result.stderr).strip()
        if len(out) > 4000:
            out = out[:4000] + "\n... [tronqué]"
        return out or f"(code retour : {result.returncode})"
    except subprocess.TimeoutExpired:
        return f"Timeout ({timeout}s)"
    except Exception as e:
        return str(e)


def _build_env(context) -> dict:
    """Environnement injecté dans chaque script."""
    env = os.environ.copy()
    mc = context.config.get("mqtt", {})
    env["MQTT_BROKER"]      = mc.get("host", "localhost")
    env["MQTT_PORT"]        = str(mc.get("port", 1883))
    env["MQTT_REPLY_TOPIC"] = "agents/nexus/inbox"
    env["AGENT_ID"]         = context.agent_id
    return env


def run(args: str, context) -> str:
    _ensure_dir()
    parts = args.strip().split(None, 1)
    action = parts[0].lower() if parts else "run"
    rest   = parts[1] if len(parts) > 1 else ""

    if action == "run":
        # Exécution directe d'un script inline
        if not rest:
            return "Précise le contenu du script."
        content = rest.replace("\\n", "\n")
        # Fichier temporaire
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False, dir="/tmp"
        ) as f:
            f.write("#!/bin/bash\nset -e\n" + content)
            tmpfile = f.name
        os.chmod(tmpfile, stat.S_IRWXU)
        env = _build_env(context)
        out = _run(tmpfile, env=env, timeout=60)
        os.unlink(tmpfile)
        return out

    if action == "save":
        if "|" not in rest:
            return "Format : save <nom> | <contenu du script>"
        name, content = rest.split("|", 1)
        name    = name.strip().replace("/", "_")  # Sécurité
        content = content.strip().replace("\\n", "\n")
        path    = os.path.join(SCRIPTS_DIR, name + ".sh")
        with open(path, "w") as f:
            f.write("#!/bin/bash\n" + content)
        os.chmod(path, stat.S_IRWXU)
        return f"Script sauvegardé : {path}"

    if action == "exec":
        parts2 = rest.split(None, 1)
        name   = parts2[0] if parts2 else ""
        sargs  = parts2[1] if len(parts2) > 1 else ""
        if not name:
            return "Précise le nom du script."
        path = os.path.join(SCRIPTS_DIR, name + ".sh")
        if not os.path.exists(path):
            return f"Script '{name}' introuvable dans {SCRIPTS_DIR}"
        env = _build_env(context)
        return _run(f"{path} {sargs}", env=env, timeout=120)

    if action == "list":
        files = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".sh")]
        return "\n".join(files) if files else "Aucun script sauvegardé."

    if action == "show":
        name = rest.strip()
        if not name:
            return "Précise le nom du script."
        path = os.path.join(SCRIPTS_DIR, name + ".sh")
        if not os.path.exists(path):
            return f"Script '{name}' introuvable."
        with open(path) as f:
            return f.read()

    if action == "delete":
        name = rest.strip()
        if not name:
            return "Précise le nom du script."
        path = os.path.join(SCRIPTS_DIR, name + ".sh")
        if os.path.exists(path):
            os.unlink(path)
            return f"Script '{name}' supprimé."
        return f"Script '{name}' introuvable."

    return "Action inconnue. Disponible : run, save, exec, list, show, delete"
