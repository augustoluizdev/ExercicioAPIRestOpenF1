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


def save_to_collection(data: list, collection_name: str, unique_keys: list):
    """Insere ou atualiza os registros usando upsert para manter idempotência."""
    if not data:
        print(f"Nenhum dado para salvar na collection '{collection_name}'.")
        return

    db = connect_to_mongodb()
    collection = db[collection_name]

    for record in data:
        if not isinstance(record, dict):
            continue

        filter_doc = {key: record.get(key) for key in unique_keys if key in record}
        if not filter_doc:
            print(f"Registro ignorado em '{collection_name}': chaves únicas ausentes.")
            continue

        collection.update_one(filter_doc, {"$set": record}, upsert=True)

    print(f"Collection '{collection_name}' atualizada com {len(data)} registros.")


def main():
    """Fluxo principal: busca dados da sessão no OpenF1 e salva no MongoDB."""
    session_key = int(os.getenv("SESSION_KEY", "9159"))
    meeting_key = int(os.getenv("MEETING_KEY", "1219"))

    print(f"Buscando sessões para session_key={session_key} e meeting_key={meeting_key}...")
    sessions = fetch_data("/sessions", {"session_key": session_key, "meeting_key": meeting_key})

    if sessions:
        save_to_collection(sessions, "sessions", ["session_key"])
    else:
        print("Nenhuma sessão foi retornada pela API OpenF1.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Erro na execução principal: {exc}")
