#!/usr/bin/env python3
"""
Agent Debian — Administration système complète.
Contrôle apt, systemd, réseau, filesystem, processus, logs, conteneurs, utilisateurs.
"""
import os
import sys
import threading
import subprocess
import logging


from agents_core import BaseAgent, AgentContext, Message, MessageType

logger = logging.getLogger(__name__)


class AgentDebian(BaseAgent):
    AGENT_TYPE = "debian"
    DESCRIPTION = (
        "Administration système Debian : paquets apt, services systemd, "
        "réseau, filesystem, processus, logs, conteneurs Docker/LXC, utilisateurs"
    )
    DEFAULT_CONFIG_PATH = "/opt/agent_debian/config/config.json"

    def get_skills_dir(self) -> str:
        return os.path.join(os.path.dirname(__file__), "skills")

    def on_start(self):
        """Au démarrage, signale à Nexus que l'agent est prêt."""
        self.mqtt.send_to("nexus", f"Agent Debian ({self.agent_id}) en ligne.")
        # Lance la surveillance proactive
        self._start_monitoring()

    def setup_extra_subscriptions(self):
        """Souscrit aussi aux commandes de contrôle."""
        self.mqtt.subscribe(
            f"agents/{self.agent_id}/control",
            self._on_control_message,
        )

    def _on_control_message(self, msg, topic: str):
        """Messages de contrôle (pause, resume, report...)."""
        from agents_core.message_bus import Message as Msg
        payload = msg.payload if isinstance(msg, Msg) else str(msg)
        result = self._handle_system_command(payload)
        if result and isinstance(msg, Msg):
            self.mqtt.reply(msg, result)

    def handle_custom_command(self, cmd: str, args: str, source_msg=None):
        """Commandes spécifiques à l'agent Debian."""
        if cmd == "report":
            return self._build_report()
        if cmd == "update":
            return self._self_update()
        return f"Commande inconnue : /{cmd}"

    def on_broadcast(self, msg: Message):
        """Réagit aux broadcasts (ex: demande de statut globale)."""
        if "status" in str(msg.payload).lower():
            self.mqtt.reply(msg, self._build_report())

    def _build_report(self) -> str:
        """Génère un rapport quotidien du système."""
        context = AgentContext(self)
        lines = [f"── Rapport {self.agent_id} ──"]
        stats = self.queue.daily_stats()
        lines.append(
            f"Tâches : {stats['total']} total / "
            f"{stats['completed']} OK / {stats['failed']} erreurs / "
            f"durée moy. {stats['avg_duration_s']}s"
        )
        # Infos système rapides
        try:
            uptime = subprocess.check_output("uptime -p", shell=True, text=True).strip()
            disk = subprocess.check_output("df -h / | tail -1 | awk '{print $3\"/\"$2\" (\"$5\" utilisé)\"}'",
                                           shell=True, text=True).strip()
            mem = subprocess.check_output(
                "free -h | awk '/^Mem:/{print $3\"/\"$2}'", shell=True, text=True
            ).strip()
            lines.append(f"Uptime : {uptime} | RAM : {mem} | Disque / : {disk}")
        except Exception:
            pass
        return "\n".join(lines)

    def _self_update(self) -> str:
        """Git pull + redémarrage du service."""
        try:
            out = subprocess.check_output(
                "cd /opt/agent_debian && git pull",
                shell=True, text=True, stderr=subprocess.STDOUT
            )
            subprocess.Popen(["systemctl", "restart", self.agent_id])
            return f"Mise à jour effectuée :\n{out}\nRedémarrage en cours..."
        except subprocess.CalledProcessError as e:
            return f"Erreur mise à jour : {e.output}"

    def _start_monitoring(self):
        """Lance la surveillance proactive en arrière-plan."""
        t = threading.Thread(target=self._monitor_loop, daemon=True)
        t.start()

    def _monitor_loop(self):
        """Vérifie périodiquement les ressources critiques et alerte si nécessaire."""
        import time
        while self._running:
            try:
                self._check_disk_usage()
                self._check_memory()
            except Exception as e:
                logger.debug(f"[Monitor] {e}")
            time.sleep(300)  # Toutes les 5 minutes

    def _check_disk_usage(self):
        """Alerte si un disque dépasse 85%."""
        result = subprocess.run(
            "df -h | awk 'NR>1 && $5+0 > 85 {print $0}'",
            shell=True, capture_output=True, text=True
        )
        if result.stdout.strip():
            self.mqtt.alert(
                f"Espace disque critique :\n{result.stdout.strip()}",
                severity="critical"
            )

    def _check_memory(self):
        """Alerte si la RAM disponible < 10%."""
        result = subprocess.run(
            "free | awk '/^Mem:/{if ($3/$2*100 > 90) print \"RAM utilisée à \"int($3/$2*100)\"%\"}'",
            shell=True, capture_output=True, text=True
        )
        if result.stdout.strip():
            self.mqtt.alert(result.stdout.strip(), severity="warning")


if __name__ == "__main__":
    AgentDebian().run()
