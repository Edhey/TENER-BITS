# TENER BITS

Repository for the 2025/2026 HPE Tech Challenge Team "Tener Bits".

---

## Challenge 3: Operation "Open Sky"

**[Challenge 3 Description](https://cdstechchallenge.com/retos/enero-reto-3-o8j40fwwboz6ogxa/)**

### Objective

Use the HPE Intelligence API to identify members of "La Sombra" hiding within flight records. We must reconstruct their travel itinerary by finding hidden messages in the data.

### Methodology & Progress

We have developed a Python solution that performs the following:

1. **Scraping (`flights_db.py`):**
   * Fetches the full flight data from the HPE Intelligence API.

2. **Anomaly Detection (`analyze.py`):**
   * **The Pattern:** We detected "CamelCase" anomalies (e.g., `mexic`**O**, `p`**A**`nama`) hidden inside standard text.
   * *Note:* We filtered out the "LatAm" airline to remove false positives.
   * Also we analyzed text fields (Country, City, Airline) for steganography but found no relevant data.

### Key Findings

We successfully isolated **13 specific flights** containing hidden characters.

* **Raw Sequence Found:** `A D S A E R H E M B O U W`
* **Decoded Keywords:** By rearranging the letters, we identified three key terms relevant to the plot:
* **SHADOW**
* **EU** (Europe)
* **AMBER** (Color??)

### ToDo

The endpoint `/api/v1/ADSAERHEMBOUW` returns a **404**. We need to find the correct order of the words.

1. **Rearrange the letters** maybe in a different order it works.
2. **Check for additional clues** in other endpoints?
