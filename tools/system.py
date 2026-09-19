import os
import platform

import psutil


def get_system_info():
    """Retorna informações reais e atuais do computador."""

    return {
        "hostname": platform.node(),
        "sistema": platform.system(),
        "distribuicao": _get_distribution(),
        "kernel": platform.release(),
        "arquitetura": platform.machine(),
        "processador": _get_cpu(),
        "gpu": _get_gpu(),
        "memoria_ram": _get_ram_info(),
        "armazenamento": _get_storage(),
    }


def _get_distribution():
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as file:
            data = file.read()

        for line in data.splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip('"')
    except OSError:
        pass

    return "Desconhecida"


def _get_cpu():
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass

    return "Desconhecido"


def _get_gpu():
    drm_path = "/sys/class/drm"

    try:
        for entry in os.listdir(drm_path):
            device_path = os.path.join(drm_path, entry, "device")
            vendor_path = os.path.join(device_path, "vendor")

            if not os.path.exists(vendor_path):
                continue

            try:
                vendor = open(
                    vendor_path,
                    "r",
                    encoding="utf-8"
                ).read().strip()
            except OSError:
                continue

            if vendor == "0x1002":
                product_path = os.path.join(
                    device_path,
                    "product_name"
                )

                if os.path.exists(product_path):
                    try:
                        return open(
                            product_path,
                            "r",
                            encoding="utf-8"
                        ).read().strip()
                    except OSError:
                        pass

                return "AMD GPU"

        return "Não identificada"

    except OSError:
        return "Desconhecida"


def _get_ram_info():
    memory = psutil.virtual_memory()

    return {
        "total_gb": round(memory.total / 1024**3, 2),
        "usada_gb": round(memory.used / 1024**3, 2),
        "disponivel_gb": round(memory.available / 1024**3, 2),
        "uso_percentual": memory.percent,
    }


def _get_storage():
    try:
        disk = psutil.disk_usage("/")

        return {
            "total_gb": round(disk.total / 1024**3, 2),
            "usado_gb": round(disk.used / 1024**3, 2),
            "livre_gb": round(disk.free / 1024**3, 2),
            "uso_percentual": disk.percent,
        }
    except OSError:
        return None
