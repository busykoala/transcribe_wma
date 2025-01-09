# Transcribe audio file to text

## Install & develop

```bash
# install
poetry install
# run
poetry run uvicorn main:app --reload
# format
poetry run ruff format
poetry run ruff check --fix
```


## Docker

```bash
docker build -t transcribe .

docker run -p 8000:8000 -e HUGGINGFACEHUB_API_TOKEN=hf_token -e PASSWORD=hunter2 transcribe
```
