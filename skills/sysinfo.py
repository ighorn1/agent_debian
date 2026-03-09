"""
Skill SYSINFO — informations système complètes.

Usage LLM : SKILL:sysinfo ARGS:all | cpu | mem | disk | uptime | load | net
"""
import subprocess

DESCRIPTION = "Informations système : CPU, RAM, disque, uptime, charge, réseau"
USAGE = "SKILL:sysinfo ARGS:all | cpu | mem | disk | uptime | load | net"


def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as e:
        return e.output.strip() or str(e)


def run(args: str, context) -> str:
    what = args.strip().lower() or "all"

    sections = []

    if what in ("all", "uptime"):
        uptime = _run("uptime -p")
        since  = _run("uptime -s")
        sections.append(f"Uptime : {uptime} (depuis {since})")

    if what in ("all", "load"):
        load = _run("cat /proc/loadavg")
        cpus = _run("nproc")
        sections.append(f"Charge système : {load} ({cpus} CPU)")

    if what in ("all", "cpu"):
        cpu_info = _run("lscpu | grep -E 'Model name|CPU\\(s\\)|MHz'")
        cpu_usage = _run(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4\"%\"}'"
        )
        sections.append(f"CPU :\n{cpu_info}\nUtilisation : {cpu_usage}")

    if what in ("all", "mem"):
        mem = _run("free -h")
        sections.append(f"Mémoire :\n{mem}")

    if what in ("all", "disk"):
        disk = _run("df -h --output=source,size,used,avail,pcent,target | column -t")
        sections.append(f"Disques :\n{disk}")

    if what in ("all", "net"):
        ifaces = _run("ip -br addr show")
        sections.append(f"Interfaces réseau :\n{ifaces}")

    if what == "os":
        osinfo = _run("cat /etc/os-release | grep -E '^(NAME|VERSION)='")
        kernel = _run("uname -r")
        sections.append(f"OS :\n{osinfo}\nKernel : {kernel}")

    if not sections:
        return (
            "Option inconnue. Utilise : all, cpu, mem, disk, uptime, load, net, os"
        )

    return "\n\n".join(sections)
