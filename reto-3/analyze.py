import json
import re
import requests
import os
from datetime import datetime
import airportsdata
import matplotlib.pyplot as plt

# Configuración
DB_FILE = "flights_db.json"
BASE_URL = "http://hpecds.comnetconsultores.cloud:7373/api/v1"
VISUAL_ANALYSIS = True

# Códigos ANSI
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


def color(text, code):
    return f"{code}{text}{RESET}"


def get_datetime(flight):
    """Extrae un objeto datetime del vuelo para ordenación."""
    try:
        return datetime.strptime(
            f"{flight['departure_date']} {flight['departure_time']}",
            "%Y-%m-%d %H:%M:%S",
        )
    except:
        return datetime.min


def analyze_text(flights):
    print(color(f"Analizando {len(flights)} registros buscando anomalías...", CYAN))

    flights_sorted = sorted(flights, key=get_datetime)
    message_part_1 = ""
    message_part_2 = ""

    full_message_log = []

    for flight in flights_sorted:
        date = flight.get("departure_date")

        # Comprobación 1: Códigos IATA (Deben ser de 3 letras)
        iatas = [flight.get("origin_iata", ""), flight.get("destination_iata", "")]
        for code in iatas:
            if code and len(code) > 3:
                # Asumimos que es la letra extra al final
                extra_char = code[3:]
                message_part_1 += extra_char
                full_message_log.append((date, extra_char, f"IATA Length ({code})"))

        # Comprobación 2: Precios (No deben tener letras)
        price = str(flight.get("price_usd", ""))
        price_letters = re.findall(r"[a-zA-Z]", price)
        if price_letters:
            for char in price_letters:
                message_part_1 += char
                full_message_log.append((date, char, f"Price Anomalous ({price})"))

        # Comprobación 3: Países/Ciudades
        text_fields = [
            flight.get("origin_country", ""),
            flight.get("destination_country", ""),
        ]
        for text in text_fields:
            if text and "LatAm" not in text:  # Filtramos LatAm para evitar ruido
                # Anomalía: Mayúscula final o camelCase (ej: mexicO)
                anomalies = re.findall(r"(?<=[a-z])[A-Z]", text)
                for char in anomalies:
                    message_part_2 += char
                    full_message_log.append((date, char, f"Typo ({text})"))

    print(color("\nREPORTE CRONOLÓGICO DE PISTAS", BOLD + CYAN))
    final_word = ""
    for date, char, source in full_message_log:
        date_s = color(f"[{date}]", CYAN)
        char_s = color(f"'{char}'", YELLOW + BOLD)
        source_s = color(source, GREEN)
        print(f"{date_s} Letra: {char_s} \t| Fuente: {source_s}")
        final_word += char

    if final_word:
        print(color("\nPalabra encontrada: ", BOLD) + color(final_word, YELLOW + BOLD))
    else:
        print(color("\nNo se detectaron pistas de texto.", YELLOW))

    return final_word


def analyze_visual(flights):
    print(color("\nRADAR VISUAL DE TRAYECTORIAS", BOLD + CYAN))

    try:
        airports = airportsdata.load("IATA")
    except:
        print(
            color(
                "Error: Necesitas instalar airportsdata: pip install airportsdata",
                YELLOW,
            )
        )
        return

    plt.figure(figsize=(12, 6), facecolor="black")
    ax = plt.axes()
    ax.set_facecolor("#0f0f0f")
    plt.title(
        f"Rastro de La Sombra ({len(flights)} vuelos)", color="#00ff00", fontsize=14
    )

    count = 0
    for flight in flights:
        orig = flight.get("origin_iata")
        dest = flight.get("destination_iata")
        if orig in airports and dest in airports:
            x1, y1 = airports[orig]["lon"], airports[orig]["lat"]
            x2, y2 = airports[dest]["lon"], airports[dest]["lat"]
            plt.plot([x1, x2], [y1, y2], color="#00ff00", linewidth=0.8, alpha=0.15)
            count += 1

    print(color(f"   Dibujados {count} trazos. Abriendo ventana...", CYAN))
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        print(color(f"{DB_FILE} no encontrado.", RED))
        exit(1)

    with open(DB_FILE, "r", encoding="utf-8") as f:
        flights = json.load(f)
    magic_word = analyze_text(flights)

    if magic_word:
        endpoint = f"{BASE_URL}/{magic_word}"
        print(color("Endpoint: ", BOLD + CYAN) + color(endpoint, YELLOW + BOLD))
        try:  # Intento automático
            r = requests.get(endpoint)
            if r.status_code == 200:
                print(color("\n¡ACCESO CONCEDIDO! Respuesta:", GREEN + BOLD))
                print(r.text[:500] + "...")
            else:
                print(color(f"Status: {r.status_code}", YELLOW))
                if VISUAL_ANALYSIS:
                    analyze_visual(flights)  # Mostramos mapa para análisis visual
        except:
            print(color("Error al conectar con el endpoint.", RED))
            if VISUAL_ANALYSIS:
                analyze_visual(flights)
    else:
        print(
            color("No se formó ninguna palabra mágica. Revisa los registros.", YELLOW)
        )
