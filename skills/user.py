"""
Skill USER — gestion des utilisateurs et groupes.

Usage LLM :
  SKILL:user ARGS:list
  SKILL:user ARGS:add <nom> [--sudo]
  SKILL:user ARGS:delete <nom>
  SKILL:user ARGS:passwd <nom>
  SKILL:user ARGS:info <nom>
  SKILL:user ARGS:groups <nom>
  SKILL:user ARGS:addgroup <nom> <groupe>
  SKILL:user ARGS:removegroup <nom> <groupe>
  SKILL:user ARGS:lock <nom>
  SKILL:user ARGS:unlock <nom>
  SKILL:user ARGS:whoami
  SKILL:user ARGS:logged
  SKILL:user ARGS:sudoers
"""
import subprocess

DESCRIPTION = "Gestion utilisateurs et groupes : add, delete, passwd, groups, lock/unlock, sudoers"
USAGE = "SKILL:user ARGS:list | add <nom> [--sudo] | delete <nom> | passwd <nom> | info <nom> | groups <nom> | addgroup <nom> <groupe> | lock <nom> | unlock <nom> | logged"


def _run(cmd: str, timeout: int = 15) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, text=True,
            capture_output=True, timeout=timeout
        )
        out = (result.stdout + result.stderr).strip()
        return out[:3000] if out else "(aucune sortie)"
    except subprocess.TimeoutExpired:
        return f"Timeout ({timeout}s)"
    except Exception as e:
        return str(e)


def run(args: str, context) -> str:
    parts = args.strip().split()
    action = parts[0].lower() if parts else "list"
    rest   = parts[1:] if len(parts) > 1 else []

    if action == "list":
        return _run("getent passwd | awk -F: '$3>=1000 || $3==0 {print $1\" (uid=\"$3\", shell=\"$7\")\"}'")

    if action == "add":
        if not rest:
            return "Précise le nom d'utilisateur."
        name  = rest[0]
        sudo  = "--sudo" in rest or "-s" in rest
        cmds = [
            f"adduser --gecos '' --disabled-password {name}",
        ]
        if sudo:
            cmds.append(f"usermod -aG sudo {name}")
        return "\n".join(_run(c) for c in cmds)

    if action == "delete":
        if not rest:
            return "Précise le nom d'utilisateur."
        return _run(f"deluser --remove-home {rest[0]}")

    if action == "passwd":
        if not rest:
            return "Précise le nom d'utilisateur."
        # Génère un mot de passe aléatoire
        pwd = _run("openssl rand -base64 12").strip()
        out = _run(f"echo '{rest[0]}:{pwd}' | chpasswd")
        return f"{out}\nNouveauMDP : {pwd}"

    if action == "info":
        if not rest:
            return "Précise le nom d'utilisateur."
        name = rest[0]
        return _run(f"id {name} && getent passwd {name}")

    if action == "groups":
        if not rest:
            return "Précise le nom d'utilisateur."
        return _run(f"groups {rest[0]}")

    if action == "addgroup":
        if len(rest) < 2:
            return "Format : addgroup <utilisateur> <groupe>"
        return _run(f"usermod -aG {rest[1]} {rest[0]}")

    if action == "removegroup":
        if len(rest) < 2:
            return "Format : removegroup <utilisateur> <groupe>"
        return _run(f"gpasswd -d {rest[0]} {rest[1]}")

    if action == "lock":
        if not rest:
            return "Précise le nom d'utilisateur."
        return _run(f"usermod -L {rest[0]}")

    if action == "unlock":
        if not rest:
            return "Précise le nom d'utilisateur."
        return _run(f"usermod -U {rest[0]}")

    if action == "whoami":
        return _run("whoami && id")

    if action == "logged":
        return _run("who && echo '---' && last -n 10")

    if action == "sudoers":
        return _run("getent group sudo | cut -d: -f4")

    if action == "ssh-key":
        # Ajouter une clé SSH pour un utilisateur
        if len(rest) < 2:
            return "Format : ssh-key <utilisateur> <clé_publique>"
        name = rest[0]
        key  = " ".join(rest[1:])
        return _run(
            f"mkdir -p /home/{name}/.ssh && "
            f"echo '{key}' >> /home/{name}/.ssh/authorized_keys && "
            f"chmod 700 /home/{name}/.ssh && "
            f"chmod 600 /home/{name}/.ssh/authorized_keys && "
            f"chown -R {name}:{name} /home/{name}/.ssh && "
            f"echo 'Clé ajoutée pour {name}'"
        )

    return "Action inconnue. Disponible : list, add, delete, passwd, info, groups, addgroup, removegroup, lock, unlock, whoami, logged, sudoers, ssh-key"
