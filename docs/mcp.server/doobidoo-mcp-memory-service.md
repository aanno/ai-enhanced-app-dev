# doobidoo/mcp-memory-service

* https://github.com/doobidoo/mcp-memory-service

## use 

```sh
memory launch --host 0.0.0.0 --port 3012
Starting memory server on port 3012...
Waiting for server to start...
Server started (PID 144695)
  Dashboard: http://0.0.0.0:3012
  API docs:   http://0.0.0.0:3012/docs
```

## install sources directly

```sh
uv python install 3.14
uv venv --python 3.14
. .venv/bin/activate
uv pip install pymilvus milvus-lite
uv pip install onnxruntime
uv pip install transformers torch huggingface-hub
uv pip install -e .
du -sk .venv/
6052264 .venv/
```
