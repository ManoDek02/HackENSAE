import asyncio
import httpx
import uuid
import time
from colorama import init, Fore

init(autoreset=True)

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api"  # Modifiez si vous testez en production
HACKATHON_ID = 1  # ID du hackathon à tester (doit avoir statut = inscriptions ou en_cours)
NB_USERS = 50     # Nombre de connexions/inscriptions simultanées

async def worker(client: httpx.AsyncClient, i: int):
    uid = uuid.uuid4().hex[:8]
    email = f"loadtest_{uid}@ensae.sn"
    password = "password123"
    
    # 1. Register
    reg_res = await client.post(f"{API_BASE_URL}/auth/register", json={
        "email": email,
        "prenom": f"Test{i}",
        "nom": f"Load",
        "password": password
    })
    
    if reg_res.status_code not in (200, 201):
        print(Fore.RED + f"[-] Erreur Register User {i}: {reg_res.text}")
        return False

    # 2. Login
    login_res = await client.post(f"{API_BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if login_res.status_code != 200:
        print(Fore.RED + f"[-] Erreur Login User {i}: {login_res.text}")
        return False
        
    token = login_res.json()["access_token"]
    
    # 3. Inscription au hackathon
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "hackathon_id": HACKATHON_ID,
        "nom_equipe": f"Equipe Load Test {uid}",
        "email_contact": email,
        "membres": [{"nom": f"Membre {uid}", "filiere": "IT"}],
        "domaine": "Performance"
    }
    
    start_time = time.time()
    insc_res = await client.post(f"{API_BASE_URL}/inscriptions", json=payload, headers=headers)
    elapsed = time.time() - start_time
    
    if insc_res.status_code in (200, 201):
        print(Fore.GREEN + f"[+] Inscription OK | Equipe {uid} | Temps: {elapsed:.2f}s")
        return True
    else:
        print(Fore.YELLOW + f"[-] Inscription FAIL | Equipe {uid} | Status: {insc_res.status_code} | Msg: {insc_res.text}")
        return False

async def main():
    print(f"=== Début du test de charge : {NB_USERS} inscriptions simultanées ===")
    print(f"URL: {API_BASE_URL}")
    print("Vérifiez que le backend FastAPI est démarré !\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [worker(client, i) for i in range(NB_USERS)]
        start = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start
        
    successes = sum(1 for r in results if r)
    
    print("\n=== Bilan du test de charge ===")
    print(f"Succès : {successes} / {NB_USERS}")
    print(f"Temps total : {total_time:.2f}s")
    print(f"Inscriptions par seconde : {successes/total_time:.2f} req/s")

if __name__ == "__main__":
    asyncio.run(main())
