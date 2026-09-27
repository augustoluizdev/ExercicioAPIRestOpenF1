# ExercicioAPIRestOpenF1

Coletor Python para consumir a API OpenF1 e armazenar os dados em MongoDB de forma modular, configurável e idempotente.

## Requisitos

- Python 3
- requests
- pymongo
- python-dotenv

## Configuração

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Crie ou ajuste o arquivo `.env` com as variáveis necessárias:


3. Verifique se o MongoDB está em execução localmente ou ajuste a `MONGO_URI` conforme seu ambiente.

## Execução

```bash
python f1_data_collector.py
```

O script executa a coleta da sessão de demonstração, salva os dados em `sessions`, `drivers` e `laps`, e usa `update_one(..., upsert=True)` para evitar duplicações.

## Coleções e chaves únicas

- `sessions`: `session_key`
- `drivers`: `session_key` + `driver_number`
- `laps`: `session_key` + `driver_number` + `lap_number`

## Funcionalidades

- Conexão com MongoDB via `connect_to_mongodb()`
- Consulta à API OpenF1 via `fetch_data()`
- Persistência idempotente via `save_to_collection()`
- Fluxo principal em `main()` para sessão, pilotos e voltas
