import os
import requests
import json

# Configuración de la API y archivo local
BASE_URL = "http://hpecds.comnetconsultores.cloud:7373/api/v1"
FLIGHTS_ENDPOINT = f"{BASE_URL}/flights"
DB_FILE = "flights_db.json"

# Códigos ANSI
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


def color(text, code):
    return f"{code}{text}{RESET}"


def fetch_all_fligths():
    """Ignora total_pages y descarga hasta que no haya más datos."""
    print(color("Iniciando extracción...", CYAN))

    all_flights = []
    page = 1

    while True:
        try:
            print(color(f"Página {page}...", YELLOW), end="\r")
            url = f"{FLIGHTS_ENDPOINT}?page={page}&page_size=50"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])

                if not items:
                    print(
                        color(f"\nPágina {page} vacía. Fin de la transmisión.", GREEN)
                    )
                    break

                all_flights.extend(items)
                page += 1
            else:
                print(
                    color(
                        f"\nError en página {page}: Status {response.status_code}", RED
                    )
                )
                break

        except Exception as e:
            print(color(f"\nExcepción crítica: {e}", RED))
            break

    print(
        color(
            f"\nDescarga finalizada. Total registros reales: {len(all_flights)}",
            BOLD + CYAN,
        )
    )

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(all_flights, f)

    print(color(f"Datos guardados en {DB_FILE}", GREEN))
    return all_flights


def main():
    if os.path.exists(DB_FILE):
        print(
            color(
                "Estás seguro de que quieres re-descargar los datos? (S/N): ", YELLOW
            ),
            end="",
        )
        choice = input().strip().lower()
        if choice != "s":
            print(color("Usando caché local.", GREEN))
            return
    fetch_all_fligths()


if __name__ == "__main__":
    main()
