"""
Skill NETWORK — administration réseau.

Usage LLM :
  SKILL:network ARGS:ip [show|route|link]
  SKILL:network ARGS:ping <hôte> [count]
  SKILL:network ARGS:traceroute <hôte>
  SKILL:network ARGS:dns <nom>
  SKILL:network ARGS:ports [tcp|udp]
  SKILL:network ARGS:connections
  SKILL:network ARGS:firewall status
  SKILL:network ARGS:firewall allow <port/service>
  SKILL:network ARGS:firewall deny <port/service>
  SKILL:network ARGS:firewall delete <règle>
  SKILL:network ARGS:firewall list
  SKILL:network ARGS:bandwidth [interface]
  SKILL:network ARGS:hosts [add|remove] <ip> <nom>
  SKILL:network ARGS:wget <url>
  SKILL:network ARGS:curl <url>
"""
import subprocess

DESCRIPTION = "Administration réseau : ip, ping, traceroute, DNS, ports, firewall ufw/iptables"
USAGE = "SKILL:network ARGS:ip | ping <host> | traceroute <host> | dns <host> | ports | connections | firewall status|allow|deny|list | wget <url>"


def _run(cmd: str, timeout: int = 20) -> str:
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
    action = parts[0].lower() if parts else ""
    rest   = parts[1] if len(parts) > 1 else ""

    if action == "ip":
        sub = rest.strip().lower() or "show"
        if sub == "show" or sub == "addr":
            return _run("ip -br addr show")
        if sub == "route":
            return _run("ip route show")
        if sub == "link":
            return _run("ip -br link show")
        if sub == "full":
            return _run("ip addr show")
        return _run(f"ip {rest}")

    if action == "ping":
        parts2 = rest.split()
        host  = parts2[0] if parts2 else ""
        count = parts2[1] if len(parts2) > 1 else "4"
        if not host:
            return "Précise l'hôte."
        return _run(f"ping -c {count} {host}", timeout=int(count) * 3 + 5)

    if action == "traceroute":
        host = rest.strip()
        if not host:
            return "Précise l'hôte."
        return _run(f"traceroute -m 15 {host}", timeout=60)

    if action == "dns":
        host = rest.strip()
        if not host:
            return "Précise le nom à résoudre."
        return _run(f"dig +short {host} && dig +short -x $(dig +short {host} | head -1) 2>/dev/null || nslookup {host}")

    if action == "ports":
        proto = rest.strip().lower()
        if proto == "udp":
            return _run("ss -ulnp")
        return _run("ss -tlnp")

    if action == "connections":
        return _run("ss -tunp | head -50")

    if action == "netstat":
        return _run("ss -s")

    if action == "firewall":
        parts2 = rest.split(None, 1)
        sub    = parts2[0].lower() if parts2 else "status"
        arg    = parts2[1] if len(parts2) > 1 else ""

        # Détecte ufw ou iptables
        ufw_available = _run("which ufw") != ""

        if sub == "status":
            if ufw_available:
                return _run("ufw status verbose")
            return _run("iptables -L -n -v --line-numbers")

        if sub == "allow":
            if not arg:
                return "Précise le port/service."
            if ufw_available:
                return _run(f"ufw allow {arg}")
            return _run(f"iptables -A INPUT -p tcp --dport {arg} -j ACCEPT")

        if sub == "deny":
            if not arg:
                return "Précise le port/service."
            if ufw_available:
                return _run(f"ufw deny {arg}")
            return _run(f"iptables -A INPUT -p tcp --dport {arg} -j DROP")

        if sub == "delete":
            if not arg:
                return "Précise la règle ou le numéro."
            if ufw_available:
                return _run(f"ufw delete {arg}")
            return _run(f"iptables -D INPUT {arg}")

        if sub == "list":
            if ufw_available:
                return _run("ufw status numbered")
            return _run("iptables -L INPUT -n -v --line-numbers")

        if sub == "enable":
            return _run("ufw --force enable") if ufw_available else "ufw non disponible."

        if sub == "disable":
            return _run("ufw disable") if ufw_available else "ufw non disponible."

        return f"Sous-commande firewall inconnue : {sub}"

    if action == "bandwidth":
        iface = rest.strip() or "eth0"
        # ifstat ou /proc/net/dev si pas dispo
        result = _run(f"cat /proc/net/dev | grep {iface}")
        if not result:
            return f"Interface {iface} introuvable."
        return result

    if action == "hosts":
        parts2 = rest.split()
        sub    = parts2[0].lower() if parts2 else "list"
        if sub == "list" or not parts2:
            return _run("cat /etc/hosts")
        if sub == "add" and len(parts2) >= 3:
            ip, name = parts2[1], parts2[2]
            return _run(f"echo '{ip} {name}' >> /etc/hosts && echo 'Ajouté : {ip} {name}'")
        if sub == "remove" and len(parts2) >= 2:
            name = parts2[1]
            return _run(f"sed -i '/{name}/d' /etc/hosts && echo 'Supprimé : {name}'")
        return "Usage : hosts list | add <ip> <nom> | remove <nom>"

    if action == "wget":
        url = rest.strip()
        if not url:
            return "Précise l'URL."
        return _run(f"wget -q --spider {url} && echo 'URL accessible' || echo 'URL inaccessible'")

    if action == "curl":
        url = rest.strip()
        if not url:
            return "Précise l'URL."
        return _run(f"curl -sI {url} | head -10")

    if action == "arp":
        return _run("arp -n")

    if action == "hostname":
        return _run("hostname -f")

    return (
        "Action inconnue. Disponible : ip, ping, traceroute, dns, ports, connections, "
        "firewall, hosts, wget, curl, arp, hostname, netstat"
    )
