import os

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

OPENF1_BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
DB_NAME = os.getenv("DB_NAME", "openf1_data")
MONGO_URI = os.getenv("MONGO_URI")
SESSION_KEY = int(os.getenv("SESSION_KEY", "9159"))
MEETING_KEY = int(os.getenv("MEETING_KEY", "1219"))


def connect_to_mongodb():
    """Lê a URI do MongoDB do arquivo .env, conecta e retorna a base de dados."""
    if not MONGO_URI:
        raise ValueError("MONGO_URI não configurada. Verifique o arquivo .env.")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        raise RuntimeError(f"Não foi possível conectar ao MongoDB: {exc}") from exc

    db = client[DB_NAME]
    print(f"Conexão com MongoDB estabelecida no banco '{DB_NAME}'.")
    return db


def fetch_data(endpoint: str, params: dict | None = None) -> list:
    """Faz uma requisição GET na API OpenF1 e retorna uma lista de resultados."""
    if not endpoint:
        raise ValueError("O endpoint deve ser informado.")

    url = f"{OPENF1_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    try:
        response = requests.get(url, params=params or {}, timeout=30)
        response.raise_for_status()
        payload = response.json()

        if payload is None:
            return []
        if isinstance(payload, list):
            return payload
        return [payload]
    except requests.RequestException as exc:
        print(f"Erro na requisição HTTP para {url}: {exc}")
        return []
    except ValueError as exc:
        print(f"Resposta inválida da API OpenF1 em {url}: {exc}")
        return []


def save_to_collection(data: list, collection_name: str, unique_keys: list, db=None) -> None:
    """Insere ou atualiza os registros usando update_one(..., upsert=True) para garantir idempotência."""
    if db is None:
        db = connect_to_mongodb()

    if not data:
        print(f"Nenhum dado para salvar na collection '{collection_name}'.")
        return

    if not collection_name:
        raise ValueError("O nome da collection deve ser informado.")

    collection = db[collection_name]
    registros_processados = 0

    for record in data:
        if not isinstance(record, dict):
            continue

        filter_doc = {key: record.get(key) for key in unique_keys if key in record}
        if len(filter_doc) != len(unique_keys):
            print(f"Registro ignorado em '{collection_name}': chaves únicas ausentes.")
            continue

        collection.update_one(filter_doc, {"$set": record}, upsert=True)
        registros_processados += 1

    print(f"Collection '{collection_name}' atualizada com {registros_processados} registros.")


def main():
    """Fluxo principal: conecta ao banco, busca sessão, pilotos e voltas e salva cada conjunto na collection correta."""
    print(f"Executando coleta para session_key={SESSION_KEY} e meeting_key={MEETING_KEY}.")

    db = connect_to_mongodb()

    print(f"Buscando sessão para session_key={SESSION_KEY}...")
    sessions = fetch_data("/sessions", {"session_key": SESSION_KEY, "meeting_key": MEETING_KEY})
    if sessions:
        save_to_collection(sessions, "sessions", ["session_key"], db=db)
    else:
        print("Nenhuma sessão foi retornada pela API OpenF1.")

    print(f"Buscando pilotos para session_key={SESSION_KEY}...")
    drivers = fetch_data("/drivers", {"session_key": SESSION_KEY})
    if drivers:
        save_to_collection(drivers, "drivers", ["session_key", "driver_number"], db=db)
    else:
        print("Nenhum piloto foi retornado pela API OpenF1.")

    print(f"Buscando voltas para session_key={SESSION_KEY}...")
    laps = fetch_data("/laps", {"session_key": SESSION_KEY})
    if laps:
        save_to_collection(laps, "laps", ["session_key", "driver_number", "lap_number"], db=db)
    else:
        print("Nenhuma volta foi retornada pela API OpenF1.")

    print("Coleta concluída com sucesso.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Erro na execução principal: {exc}")

