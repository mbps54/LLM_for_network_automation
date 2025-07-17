import subprocess


def ping(host: str) -> bool:
    """
    Проверяет доступность хоста по ICMP (ping).

    Аргументы:
        host (str): IP-адрес или доменное имя хоста.

    Возвращает:
        bool: True, если хост отвечает, иначе False.
    """
    try:
        # Пингуем хост 2 раза (для Unix-систем)
        command = ["ping", "-c", "2", host]
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return result.returncode == 0
    except Exception:
        # В случае ошибки — хост считаем недоступным
        return False
