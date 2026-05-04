import asyncio
import httpx
import time

# Konfiguracja portów
MODELS = {
    "Gemini PRO": 8001,
    "Gemini Flash": 8002,
    "GPT-4o": 8003,
    "DeepSeek": 8004,
    "Grok": 8005
}

async def check_model(client: httpx.AsyncClient, name: str, port: int):
    url = f"http://127.0.0.1:{port}/assets"
    print(f"🔍 Sprawdzam: {name} (Port {port})...")
    
    try:
        # Timeout ustawiony na 5 sekund, żeby dać szansę na inicjalizację bazy
        start_time = time.perf_counter()
        response = await client.get(url, timeout=5.0)
        end_time = time.perf_counter()
        
        latency = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ {name}: DZIAŁA ({latency:.2f}s)")
        else:
            print(f"❌ {name}: BŁĄD {response.status_code}")
            
    except httpx.ConnectError:
        print(f"⚠️ {name}: OFFLINE (Serwer nie odpowiada)")
    except httpx.ReadTimeout:
        print(f"⏰ {name}: TIMEOUT (Baza zablokowana?)")
    except Exception as e:
        print(f"❓ {name}: BŁĄD: {type(e).__name__}")

async def main():
    print("🚀 URUCHAMIAM ASYNCHRONICZNY TEST STAGGERED...\n")
    
    async with httpx.AsyncClient() as client:
        for name, port in MODELS.items():
            # Wykonujemy test dla jednego modelu
            await check_model(client, name, port)
            
            # --- TO JEST KLUCZOWE ---
            # Czekamy 1 sekundę przed odpytaniem kolejnego modelu
            # To zapobiega jednoczesnemu blokowaniu pliku finance.db
            await asyncio.sleep(1.0)
            
    print("\n🏁 Testy zakończone.")

if __name__ == "__main__":
    asyncio.run(main())