# agent_debian

Agent d'administration système. Gère les paquets, services, processus, fichiers, réseau, utilisateurs et conteneurs sur le serveur local. Répond aux délégations de Nexus via MQTT.

## Rôle

Toutes les tâches système sur **ce serveur** passent par cet agent : `apt install`, `systemctl restart`, surveillance disque/RAM, consultation des logs, gestion des crons, etc.

## Installation

```bash
cd /opt/agent_debian
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
systemctl enable --now agent_debian
```

## Skills disponibles

| Skill | Description |
|-------|-------------|
| `apt` | Gestion des paquets (install, remove, update, upgrade, search) |
| `systemd` | Contrôle des services (start, stop, restart, status, enable) |
| `shell` | Exécution de commandes shell arbitraires |
| `script` | Exécution de scripts multi-lignes |
| `sysinfo` | CPU, RAM, disque, uptime |
| `process` | Liste, kill, surveillance des processus |
| `filesystem` | Lecture, écriture, liste, recherche de fichiers |
| `network` | Interfaces, connexions, ping, traceroute |
| `journal` | Consultation des logs systemd (journalctl) |
| `cron` | Gestion des tâches cron |
| `container` | Gestion Docker/LXC (ps, start, stop, logs) |
| `user` | Gestion des utilisateurs et groupes |
| `agents_status` | Statut des agents du système |
| `mqtt_send` | Publication sur un topic MQTT |
| `mqtt_subscribe` | Souscription dynamique à un topic MQTT |
| `muc_send` | Message dans le groupe XMPP |

## Surveillance proactive

L'agent monitore en arrière-plan (toutes les 5 minutes) :
- **Disque** : alerte si un volume dépasse 85% d'utilisation
- **RAM** : alerte si la mémoire utilisée dépasse 90%

Les alertes sont envoyées automatiquement à Nexus via MQTT.

## Configuration

`config/config.json` :
```json
{
  "agent_id": "debian.local",
  "xmpp": {
    "jid": "debian.local@xmpp.ovh",
    "password": "...",
    "admin_jid": "sylvain@xmpp.ovh",
    "muc_room": "agents@muc.xmpp.ovh"
  },
  "mqtt": { "host": "localhost", "port": 1883 },
  "llm": {
    "base_url": "http://192.168.7.119:11434",
    "model": "ministral-3:latest",
    "temperature": 0.3
  },
  "llm_profiles": {
    "local": "ministral-3:latest",
    "cloud": "gpt-oss:120b-cloud"
  }
}
```

## Commandes

```
/report   — Rapport système (uptime, RAM, disque, stats tâches)
/update   — Git pull + redémarrage du service
/status   — État de la queue de tâches
/pause    — Pause du traitement des tâches
/resume   — Reprise
```

## Fichiers

```
agent_debian.py       — Point d'entrée
skills/               — 16 skills système
config/               — Configuration et system prompt
agent_debian.service  — Unit systemd
```
