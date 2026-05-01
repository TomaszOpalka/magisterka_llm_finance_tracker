#  LLM Efficiency Benchmark: Premium vs. Free in Financial API Engineering

### 🎓 Praca Magisterska: Porównawcza Analiza Efektywności i Jakości Odpowiedzi Modeli LLM

**Autor:** Tomasz Opałka  
**Kierunek:** Informatyka, Wydział Finansów i Zarządzania  
**Promotor:** Dr inż. Natalia Piórkowska  
**Rok:** 2026

---

##  O Projekcie
Niniejsze repozytorium zawiera dokumentację oraz wyniki eksperymentu badawczego realizowanego w ramach pracy magisterskiej. Celem projektu jest obiektywne zestawienie możliwości modelu klasy Premium (**Gemini 3.1 PRO**) z wiodącymi modelami bezpłatnymi w zadaniach z zakresu inżynierii oprogramowania oraz argumentacji logicznej.

Głównym zadaniem postawionym przed modelami jest budowa systemu **FinanceTrack** – mikroserwisu REST API do monitorowania indeksu **S&P 500**, zasilanego danymi z biblioteki `yfinance`.

##  Badane Jednostki (LLMs)
Eksperyment obejmuje łącznie 1000 interakcji (500 w j. polskim, 500 w j. angielskim) z następującymi modelami:
*    **Gemini 3.1 PRO** (Model Referencyjny / Premium)
*    **Gemini Flash**
*    **ChatGPT (GPT-4o)**
*    **DeepSeek-V3**
*    **Grok 4.1 Flash**

##  Scenariusz Badawczy: PR #67
Kluczowym elementem weryfikacji jest **Pull Request #67**, który narzuca rygorystyczne mapowanie konwencji nazewnictwa:
- **Database Layer:** `snake_case` (SQLAlchemy 2.0+)
- **API/Frontend Layer:** `camelCase` (Pydantic v2)

Badanie sprawdza zdolność modeli do utrzymania długiego okna kontekstowego oraz precyzji technicznej w warunkach narastającej złożoności projektu.

##  Stack Technologiczny
*   **Język:** Python 3.12
*   **Framework:** FastAPI
*   **ORM:** SQLAlchemy 2.0+ (Asynchronous)
*   **Dane:** yfinance API (S&P 500 Index)
*   **Walidacja:** Pydantic v2
*   **Testy:** Pytest + Manual Static Analysis

##  Struktura Repozytorium
*   `/experiments` – Pełna historia ewolucji kodu dla każdego modelu (śledzona przez Git commits).
*   `/prompts` – Zestaw 100 ujednoliconych instrukcji badawczych (PL/EN).
*   `/results` – Macierz KPI, statystyki błędów i analiza porównawcza.
*   `/validator` – Skrypty automatyzujące sprawdzanie poprawności kontraktu API.

---
*Projekt ma charakter empiryczno-analityczny i stanowi próbę odpowiedzi na pytanie o ekonomiczną oraz techniczną zasadność stosowania modeli Premium w profesjonalnej inżynierii danych finansowych.*