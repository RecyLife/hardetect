import psutil
import platform
import socket
import subprocess
from tabulate import tabulate

def processor_info():
    try:
        output = subprocess.check_output(["lscpu"], universal_newlines=True)
        processor_info = {}
        for line in output.splitlines():
            if "Architecture" in line:
                processor_info["Architecture"] = line.split(":")[1].strip()
            elif "CPU op-mode(s)" in line:
                processor_info["Mode(s) d'opération du CPU"] = line.split(":")[1].strip()
            elif "Model name" in line:
                processor_info["Famille de processeur"] = line.split(":")[1].strip()
            elif "Core(s) per socket" in line:
                processor_info["Nombre de cœurs physiques"] = line.split(":")[1].strip()
            elif "Thread(s) per core" in line:
                processor_info["Threads par cœur"] = line.split(":")[1].strip()
            elif "Socket(s)" in line:
                processor_info["Nombre de sockets"] = line.split(":")[1].strip()
            elif "Max MHz" in line:
                processor_info["Fréquence Turbo maxi (MHz)"] = line.split(":")[1].strip()

        if "Nombre de cœurs physiques" in processor_info and "Threads par cœur" in processor_info:
            total_cores = int(processor_info["Nombre de cœurs physiques"])
            threads_per_core = int(processor_info["Threads par cœur"])
            processor_info["Nombre de threads"] = total_cores * threads_per_core
        
        if "Fréquence Turbo maxi (MHz)" in processor_info:
            processor_info["Fréquence Turbo maxi (GHz)"] = f"{float(processor_info['Fréquence Turbo maxi (MHz)']) / 1000:.2f}"
        
        return processor_info

    except subprocess.CalledProcessError:
        return {
            "Famille de processeur": "Erreur lors de la récupération des informations processeur"
        }

def memory_info():
    memory = psutil.virtual_memory()
    return {
        "Mémoire totale (Go)": f"{memory.total / (1024 ** 3):.2f}"
    }

def storage_info():
    try:
        output = subprocess.check_output(["lsblk", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,ROTA"], universal_newlines=True)
        storage_info = []
        root_partition = psutil.disk_partitions(all=False)[0].device

        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 5:
                name = parts[0]
                size = parts[1]
                type_ = parts[2]
                mountpoint = parts[3] if len(parts) > 3 else ""
                rota = parts[4]

                storage_type = "SSD" if rota == "0" else "HDD"
                
                if root_partition not in name:
                    storage_info.append(f"{name}: {size} ({storage_type})")

        return {
            "Stockage (non système)": "\n".join(storage_info) if storage_info else "Aucun périphérique de stockage non système détecté"
        }
    except subprocess.CalledProcessError:
        return {
            "Stockage": "Erreur lors de la récupération des informations de stockage."
        }

def graphics_info():
    graphics_info = []

    try:
        output = subprocess.check_output(["lspci"], universal_newlines=True)
        for line in output.splitlines():
            if "VGA" in line or "3D" in line:
                graphics_info.append(line.strip())
    except subprocess.CalledProcessError:
        graphics_info.append("Erreur lors de la récupération des informations graphiques.")

    return {
        "Cartes graphiques": "\n".join(graphics_info) if graphics_info else "Aucune carte graphique détectée"
    }

def linux_pc_model():
    model_file = "/sys/class/dmi/id/product_name"
    vendor_file = "/sys/class/dmi/id/product_vendor"
    board_vendor_file = "/sys/class/dmi/id/board_vendor"

    try:
        with open(model_file, "r") as f:
            model = f.read().strip()
    except FileNotFoundError:
        model = "Modèle inconnu"

    try:
        with open(vendor_file, "r") as f:
            vendor = f.read().strip()
        if vendor == "":
            raise FileNotFoundError
    except (FileNotFoundError, ValueError):
        try:
            with open(board_vendor_file, "r") as f:
                vendor = f.read().strip()
        except FileNotFoundError:
            vendor = "Fabricant inconnu"

    return f"{vendor} {model}"

def system_info():
    return {
        "Nom du PC": linux_pc_model(),
        "Nom de la machine (hostname)": socket.gethostname(),
        "Système d'exploitation": platform.system(),
        "Version de l'OS": platform.version(),
        "Architecture": platform.architecture()[0]
    }

def create_table(data_dict):
    """Transforme un dictionnaire en tableau."""
    table = []
    for key, value in data_dict.items():
        table.append([key, value])
    return table

if __name__ == "__main__":
    processor_info = processor_info()
    memory_info = memory_info()
    storage_info = storage_info()
    graphics_info = graphics_info()
    system_info = system_info()

    full_info = {**processor_info, **memory_info, **storage_info, **graphics_info, **system_info}

    table = create_table(full_info)
    print(tabulate(table, headers=["Propriété", "Valeur"], tablefmt="pretty"))
