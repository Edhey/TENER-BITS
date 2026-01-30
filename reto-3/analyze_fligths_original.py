import json
import re
import requests
import os
from datetime import datetime
import airportsdata
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
DB_FILE = "flights_db.json"
BASE_URL = "http://hpecds.comnetconsultores.cloud:7373/api/v1"
VISUAL_ANALYSIS = False  # Cambia a True si quieres ver el mapa

# --- CÓDIGOS ANSI PARA COLORES ---
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
RED = "\033[31m"


def color(text, code):
    return f"{code}{text}{RESET}"


def get_datetime(flight):
    """Extrae un objeto datetime para ordenar cronológicamente."""
    try:
        return datetime.strptime(
            f"{flight['departure_date']} {flight['departure_time']}",
            "%Y-%m-%d %H:%M:%S",
        )
    except:
        return datetime.min


def analyze_text(flights):
    print(
        color(f"🔬 Analizando {len(flights)} registros con reglas estrictas...", CYAN)
    )

    # Ordenamos por fecha para intentar leer el mensaje en orden
    flights_sorted = sorted(flights, key=get_datetime)

    full_message_log = []

    for flight in flights_sorted:
        flight_id = flight.get("flight_id", "N/A")
        date = flight.get("departure_date")

        # ---------------------------------------------------------
        # 1. IATA CODES
        # Regla: 3 caracteres exactos y todo mayúsculas [A-Z]
        # ---------------------------------------------------------
        iatas = [flight.get("origin_iata", ""), flight.get("destination_iata", "")]
        for code in iatas:
            if not code:
                continue

            # Chequeo de longitud (si tiene más de 3, lo extra es sospechoso)
            if len(code) > 3:
                extra = code[3:]
                full_message_log.append(
                    (date, extra, f"IATA Length > 3 ({code})", flight_id)
                )

            # Chequeo de caracteres no válidos (minúsculas o números en IATA)
            # Regex: Cualquier cosa que NO sea A-Z
            bad_chars = re.findall(r"[^A-Z]", code)
            for char in bad_chars:
                full_message_log.append(
                    (date, char, f"IATA Format ({code})", flight_id)
                )

        # ---------------------------------------------------------
        # 2. PRECIO (Price)
        # Regla: Solo números y punto decimal. Buscamos letras.
        # ---------------------------------------------------------
        price = str(flight.get("price_usd", ""))
        price_letters = re.findall(r"[a-zA-Z]", price)
        for char in price_letters:
            full_message_log.append(
                (date, char, f"Hidden in Price ({price})", flight_id)
            )

        # ---------------------------------------------------------
        # 3. DURACIÓN (Duration)
        # Regla: Solo números. Buscamos letras.
        # ---------------------------------------------------------
        duration = str(flight.get("duration_hours", ""))
        duration_letters = re.findall(r"[a-zA-Z]", duration)
        for char in duration_letters:
            full_message_log.append(
                (date, char, f"Hidden in Duration ({duration})", flight_id)
            )

        # ---------------------------------------------------------
        # 4. PAÍSES (Origin/Destination Countries)
        # Regla: Mayúsculas después de la 1ª letra o números escondidos
        # ---------------------------------------------------------
        countries = [
            flight.get("origin_country", ""),
            flight.get("destination_country", ""),
        ]
        for text in countries:
            if not text or "LatAm" in text:
                continue  # Filtramos ruido conocido

            # A) CamelCase Anomaly: Mayúscula precedida de minúscula (ej: mexicO)
            hidden_caps = re.findall(r"(?<=[a-z])[A-Z]", text)
            for char in hidden_caps:
                full_message_log.append(
                    (date, char, f"Country Typo ({text})", flight_id)
                )

            # B) Números escondidos en el nombre del país
            hidden_nums = re.findall(r"\d", text)
            for char in hidden_nums:
                full_message_log.append(
                    (date, char, f"Number in Country ({text})", flight_id)
                )

            # C) Anomalía Inicial (Caso especial "Quatemala")
            if text == "Quatemala":
                full_message_log.append(
                    (date, "Q", f"Initial Typo ({text})", flight_id)
                )

        # ---------------------------------------------------------
        # 5. AEROLÍNEAS (Airlines)
        # Regla: Mayúsculas raras o números tras la primera letra
        # ---------------------------------------------------------
        airline = flight.get("airline", "")
        if airline:
            # Mayúscula tras minúscula
            airline_caps = re.findall(r"(?<=[a-z])[A-Z]", airline)
            for char in airline_caps:
                full_message_log.append(
                    (date, char, f"Airline Typo ({airline})", flight_id)
                )

            # Números en aerolínea
            airline_nums = re.findall(r"\d", airline)
            for char in airline_nums:
                full_message_log.append(
                    (date, char, f"Number in Airline ({airline})", flight_id)
                )

        # ---------------------------------------------------------
        # 6. FECHAS (Departure/Arrival)
        # Regla: Formato fecha. Buscamos letras intrusas.
        # ---------------------------------------------------------
        # Concatenamos fecha y hora para buscar en ambas
        raw_date_str = str(flight.get("departure_date", "")) + str(
            flight.get("departure_time", "")
        )
        date_letters = re.findall(r"[a-zA-Z]", raw_date_str)
        # Filtramos caracteres comunes de fecha si los hubiera (ej: T, Z en ISO),
        # pero asumimos formato simple YYYY-MM-DD.
        for char in date_letters:
            # Ignoramos si es parte de un formato estándar ISO que no sea sospechoso
            # Pero en este reto, cualquier letra suele ser pista.
            full_message_log.append(
                (date, char, f"Hidden in Date ({raw_date_str})", flight_id)
            )

    # --- INFORME DE RESULTADOS ---
    print(color("\n📝 REPORTE DE EVIDENCIAS ENCONTRADAS", BOLD + CYAN))
    print(f"{'FECHA':<12} | {'PISTA'} | {'FUENTE DEL HALLAZGO'} {'ID'}")
    print("-" * 60)

    final_word = ""
    for date, char, source, flight_id in full_message_log:
        date_s = color(f"[{date}]", CYAN)
        char_s = color(f"'{char}'", YELLOW + BOLD)
        source_s = color(source, GREEN)
        id_s = color(f"(ID: {flight_id})", BLUE)

        print(f"{date_s} Letra: {char_s} \t| {source_s} {id_s}")
        final_word += char

    if final_word:
        print(color("\n🧩 PALABRA FORMADA: ", BOLD) + color(final_word, YELLOW + BOLD))
    else:
        print(color("\n❌ No se encontraron anomalías con estos criterios.", RED))

    return final_word


def analyze_visual(flights):
    print(color("\n🗺️ RADAR VISUAL DE TRAYECTORIAS", BOLD + CYAN))

    try:
        airports = airportsdata.load("IATA")
    except:
        print(color("Error: Instala airportsdata (pip install airportsdata)", YELLOW))
        return

    plt.figure(figsize=(12, 6), facecolor="black")
    ax = plt.axes()
    ax.set_facecolor("#0f0f0f")
    plt.title(f"Rastro de La Sombra ({len(flights)} vuelos)", color="#00ff00")

    count = 0
    for flight in flights:
        orig = flight.get("origin_iata")
        dest = flight.get("destination_iata")
        if orig in airports and dest in airports:
            x1, y1 = airports[orig]["lon"], airports[orig]["lat"]
            x2, y2 = airports[dest]["lon"], airports[dest]["lat"]
            plt.plot([x1, x2], [y1, y2], color="#00ff00", linewidth=0.8, alpha=0.15)
            count += 1

    print(color(f"   Trazados {count} vuelos. Abriendo mapa...", CYAN))
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        print(color(f"{DB_FILE} no encontrado. Asegúrate de tener el JSON.", RED))
        exit(1)

    with open(DB_FILE, "r", encoding="utf-8") as f:
        flights = json.load(f)

    # 1. Ejecutar análisis forense
    magic_word = analyze_text(flights)

    # 2. Probar endpoint automáticamente si hay palabra
    if magic_word:
        endpoint = f"{BASE_URL}/{magic_word}"
        print(
            color("\n🚀 PROBANDO ENDPOINT: ", BOLD + CYAN)
            + color(endpoint, YELLOW + BOLD)
        )

        try:
            r = requests.get(endpoint, timeout=5)
            if r.status_code == 200:
                print(color("\n✅ ¡ACCESO CONCEDIDO!", GREEN + BOLD))
                print("Respuesta del servidor:")
                print(r.text[:600] + "...")
            else:
                print(
                    color(
                        f"⚠️ Status: {r.status_code} (No es la palabra correcta o falta algo)",
                        YELLOW,
                    )
                )

                print(color("\n💡 SUGERENCIA:", CYAN))
                print(f"Prueba variaciones: /api/v1/{magic_word}")
                print(f"O inserta guiones: SHADOW-AMBER-...")

                if VISUAL_ANALYSIS:
                    analyze_visual(flights)
        except Exception as e:
            print(color(f"❌ Error de conexión: {e}", RED))
    else:
        print(color("No se generó ninguna palabra clave para probar.", YELLOW))
