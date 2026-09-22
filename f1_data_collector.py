import os

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

OPENF1_BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
DB_NAME = "openf1_data"


def connect_to_mongodb():
    """Lê a URI do MongoDB no .env, conecta e retorna o objeto de banco."""
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("MONGO_URI não configurada. Verifique o arquivo .env.")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception as exc:
        raise RuntimeError(f"Não foi possível conectar ao MongoDB: {exc}") from exc

    db = client[DB_NAME]
    print(f"Conexão com MongoDB estabelecida no banco '{DB_NAME}'.")
    return db


def fetch_data(endpoint: str, params: dict) -> list:
    """Faz requisição GET na API OpenF1 e retorna uma lista de resultados."""
    if not endpoint:
        raise ValueError("O endpoint deve ser informado.")

    url = f"{OPENF1_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    try:
        response = requests.get(url, params=params or {}, timeout=30)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        if data is None:
            return []
        return [data]
    except requests.RequestException as exc:
        print(f"Erro na requisição HTTP para {url}: {exc}")
        return []
    except ValueError as exc:
        print(f"Resposta inválida da API OpenF1 em {url}: {exc}")
        return []


def save_to_collection(*args, **kwargs):
    """Insere ou atualiza os registros no MongoDB usando update_one(..., upsert=True) para manter a idempotência.

    Formatos aceitos:
    - save_to_collection(data, collection_name, unique_keys, db=None)
    - save_to_collection(db, data, collection_name, unique_keys)
    """
    db = kwargs.get("db")
    if len(args) == 4 and not isinstance(args[0], list):
        db, data, collection_name, unique_keys = args
    elif len(args) == 3:
        data, collection_name, unique_keys = args
    elif len(args) == 4:
        data, collection_name, unique_keys, db = args
    else:
        data = kwargs.get("data", [])
        collection_name = kwargs.get("collection_name", "")
        unique_keys = kwargs.get("unique_keys", [])

    if db is None:
        db = connect_to_mongodb()

    if not data:
        print(f"Nenhum dado para salvar na collection '{collection_name}'.")
        return

    collection = db[collection_name]

    for record in data:
        if not isinstance(record, dict):
            continue

        filter_doc = {key: record.get(key) for key in unique_keys if key in record}
        if not filter_doc or len(filter_doc) < len(unique_keys):
            print(f"Registro ignorado em '{collection_name}': chaves únicas ausentes.")
            continue

        collection.update_one(filter_doc, {"$set": record}, upsert=True)

    print(f"Collection '{collection_name}' atualizada com {len(data)} registros.")



def main():
    """Fluxo principal do coletor OpenF1:
    1. Conectar ao MongoDB
    2. Buscar sessão
    3. Salvar sessão
    4. Buscar pilotos
    5. Salvar pilotos
    6. Buscar voltas
    7. Salvar voltas
    """
    session_key = int(os.getenv("SESSION_KEY", "9159"))

    # 1. Conectar ao MongoDB
    db = connect_to_mongodb()

    # 2. Buscar sessão
    print(f"Buscando sessão para session_key={session_key}...")
    sessions = fetch_data("/sessions", {"session_key": session_key})

    # 3. Salvar sessão
    if sessions:
        save_to_collection(sessions, "sessions", ["session_key"], db=db)
    else:
        print("Nenhuma sessão foi retornada pela API OpenF1.")

    # 4. Buscar pilotos
    print(f"Buscando pilotos para session_key={session_key}...")
    drivers = fetch_data("/drivers", {"session_key": session_key})

    # 5. Salvar pilotos
    if drivers:
        save_to_collection(drivers, "drivers", ["session_key", "driver_number"], db=db)
    else:
        print("Nenhum piloto foi retornado pela API OpenF1.")

    # 6. Buscar voltas
    print(f"Buscando voltas para session_key={session_key}...")
    laps = fetch_data("/laps", {"session_key": session_key})

    # 7. Salvar voltas
    if laps:
        save_to_collection(laps, "laps", ["session_key", "driver_number", "lap_number"], db=db)
    else:
        print("Nenhuma volta foi retornada pela API OpenF1.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Erro na execução principal: {exc}")

