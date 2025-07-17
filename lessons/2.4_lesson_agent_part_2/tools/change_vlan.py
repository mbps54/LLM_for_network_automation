import ipaddress

SWITCHES = {
    "192.168.1.10": {
        "name": "asw1",
        "ports": ["Gi0/" + str(i) for i in range(1, 25)],
        "vlans": [10, 20, 30, 40, 50]
    },
    "192.168.1.11": {
        "name": "asw2",
        "ports": ["Gi0/" + str(i) for i in range(1, 25)],
        "vlans": [10, 20, 30, 40, 50]
    },
    "192.168.1.12": {
        "name": "asw3",
        "ports": ["Gi0/" + str(i) for i in range(1, 25)],
        "vlans": [10, 20, 30, 40, 50]
    },
    "192.168.2.1": {
        "name": "dsw1",
        "ports": ["Gi1/0/" + str(i) for i in range(1, 25)],
        "vlans": [10, 20, 30, 100, 200]
    },
    "192.168.2.2": {
        "name": "dsw2",
        "ports": ["Gi1/0/" + str(i) for i in range(1, 25)],
        "vlans": [10, 20, 30, 100, 200]
    },
    "192.168.3.1": {
        "name": "core1",
        "ports": ["Ten0/" + str(i) for i in range(1, 9)],
        "vlans": [10, 20, 30, 100, 200, 300]
    }
}


# Эмуляция настройки VLAN на порту устройства
def change_vlan(ip: str, port: str, vlan: int) -> str:
    """
    Эмулирует изменение VLAN на указанном порту сетевого коммутатора.

    Проверяет корректность IP-адреса, существование устройства в базе,
    наличие порта и поддерживаемость указанного VLAN. Возвращает
    результат в виде текстового сообщения.

    Аргументы:
        ip (str): IPv4-адрес коммутатора.
        port (str): Имя порта (например, "Gi0/1").
        vlan (int): VLAN, который необходимо назначить.

    Возвращает:
        str: Статус выполнения операции или сообщение об ошибке.

    Исключения:
        ValueError: Если IP-адрес имеет неверный формат.
    """
    try:
        ipaddress.IPv4Address(ip)
    except ValueError:
        raise ValueError("change_vlan() принимает только корректный IPv4-адрес.")

    if ip not in SWITCHES:
        return f"Устройство с IP {ip} не найдено."

    switch = SWITCHES[ip]

    if port not in switch["ports"]:
        return f"Порт {port} не найден на устройстве {switch['name']} ({ip})."

    if vlan not in switch["vlans"]:
        return f"VLAN {vlan} не настроен на устройстве {switch['name']} ({ip})."

    return f"VLAN на порту {port} устройства {switch['name']} ({ip}) успешно изменён на VLAN {vlan}."