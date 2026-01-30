import json
import re
import requests
import os
from datetime import datetime
import airportsdata
import matplotlib.pyplot as plt

# Configuration
DB_FILE = "flights_db.json"
BASE_URL = "http://hpecds.comnetconsultores.cloud:7373/api/v1"
VISUAL_ANALYSIS = False

# ANSI codes
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
    """Extract a datetime object from the flight for sorting."""
    try:
        return datetime.strptime(
            f"{flight['departure_date']} {flight['departure_time']}",
            "%Y-%m-%d %H:%M:%S",
        )
    except:
        return datetime.min


def analyze_text(flights):
    print(color(f"Analyzing {len(flights)} records for anomalies...", CYAN))

    flights_sorted = sorted(flights, key=lambda x: int(x.get("flight_id", 0)))
    message_part_1 = ""
    full_message_log = []

    for flight in flights_sorted:
        flight_id = flight.get("flight_id", "N/A")
        date = flight.get("departure_date")

        # Check 1: IATA codes (Should be 3 letters)
        iatas = [flight.get("origin_iata", ""), flight.get("destination_iata", "")]
        for code in iatas:
            if code and len(code) > 3:
                # Assume it's the extra letter at the end
                extra_char = code[3:]
                message_part_1 += extra_char
                full_message_log.append(
                    (date, extra_char, f"IATA Length ({code})", flight_id)
                )

        # Check 2: Prices (Should not contain letters)
        price = str(flight.get("price_usd", ""))
        price_letters = re.findall(r"[a-zA-Z]", price)
        if price_letters:
            for char in price_letters:
                message_part_1 += char
                full_message_log.append(
                    (date, char, f"Price Anomalous ({price})", flight_id)
                )

        # Check 3: Countries/Cities (Typos and anomalies)
        text_fields = [
            flight.get("origin_country", ""),
            flight.get("destination_country", ""),
        ]
        for text in text_fields:
            if text and "LatAm" not in text:  # Filter out LatAm to avoid noise

                anomalies = []

                # A) Uppercase in the middle/at end anomaly (e.g., mexicO -> O)
                camel_case = re.findall(r"(?<=[a-z])[A-Z]", text)
                anomalies.extend(camel_case)

                # B) Specific initial anomaly (e.g., Quatemala -> Q)
                # The previous regex doesn't catch the Q because it has no lowercase before it
                if text == "Quatemala":
                    anomalies.append("Q")

                for char in anomalies:
                    full_message_log.append((date, char, f"Typo ({text})", flight_id))

    print(color("\nCHRONOLOGICAL CLUES REPORT", BOLD + CYAN))
    final_word = ""
    for date, char, source, flight_id in full_message_log:
        date_s = color(f"[{date}]", CYAN)
        id_s = color(f"(ID: {flight_id})", BLUE)
        char_s = color(f"'{char}'", YELLOW + BOLD)
        source_s = color(source, GREEN)
        print(f"{date_s} Letter: {char_s} \t| Source: {source_s} {id_s}")
        final_word += char

    if final_word:
        print(color("\nWord found: ", BOLD) + color(final_word, YELLOW + BOLD))
    else:
        print(color("\nNo text clues detected.", YELLOW))

    return final_word


def analyze_visual(flights):
    print(color("\nVISUAL TRAJECTORY RADAR", BOLD + CYAN))

    try:
        airports = airportsdata.load("IATA")
    except:
        print(
            color(
                "Error: You need to install airportsdata: pip install airportsdata",
                YELLOW,
            )
        )
        return

    plt.figure(figsize=(12, 6), facecolor="black")
    ax = plt.axes()
    ax.set_facecolor("#0f0f0f")
    plt.title(
        f"Trail of The Shadow ({len(flights)} flights)", color="#00ff00", fontsize=14
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

    print(color(f"   Drawn {count} traces. Opening window...", CYAN))
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    if not os.path.exists(DB_FILE):
        print(color(f"{DB_FILE} not found.", RED))
        exit(1)

    with open(DB_FILE, "r", encoding="utf-8") as f:
        flights = json.load(f)

    # Run the updated text analysis
    magic_word = analyze_text(flights)

    if magic_word:
        # Try the endpoint exactly as it appears
        endpoint = f"{BASE_URL}/{magic_word}"
        print(
            color("\nTesting Direct Endpoint: ", BOLD + CYAN)
            + color(endpoint, YELLOW + BOLD)
        )

        try:
            r = requests.get(endpoint)
            if r.status_code == 200:
                print(color("\nACCESS GRANTED! Response:", GREEN + BOLD))
                print(r.text[:500] + "...")
            else:
                print(color(f"Status: {r.status_code}", YELLOW))
                if VISUAL_ANALYSIS:
                    analyze_visual(flights)
        except:
            print(color("Error connecting to the endpoint.", RED))
            if VISUAL_ANALYSIS:
                analyze_visual(flights)
    else:
        print(
            color("No magic word formed. Check the records.", YELLOW)
        )
