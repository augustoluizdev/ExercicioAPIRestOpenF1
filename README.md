# ExercicioAPIRestOpenF1

Coletor inicial de dados da API OpenF1 para MongoDB.

## Configuracao

1. Instale as dependencias:

	```bash
	pip install -r requirements.txt
	```

2. Inicie um MongoDB local ou informe outra conexao no arquivo `.env`:

As variaveis `SESSION_KEY` e `MEETING_KEY` podem ser alteradas sem modificar o
codigo. O banco utilizado pelo exercicio e `openf1_data`.

## Execucao

Com o MongoDB em funcionamento, execute:

```bash
python f1_data_collector.py
```

Nesta primeira etapa, o script consulta `/sessions` usando a sessao de
demonstracao e salva os resultados na collection `sessions` com `upsert=True`.
Isso permite executar o coletor novamente sem duplicar a sessao.

## Proxima etapa

A base ja possui `connect_to_mongodb`, `fetch_data` e
`save_to_collection`. A Pessoa 2 pode continuar o fluxo adicionando as buscas
de `/drivers` e `/laps` e suas respectivas collections e chaves unicas.