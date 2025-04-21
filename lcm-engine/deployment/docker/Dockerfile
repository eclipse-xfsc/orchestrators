FROM    python:3.11

COPY    . /app

WORKDIR /app

RUN     pip3 install --no-cache-dir -r requirements.txt

ENV     PYTHONPATH="/app" \
        FLASK_DEBUG=0 \
        FLASK_APP=main.py \
        RUNTIME_ENVIRONMENT=local \
        LCM_ENGINE_KUBE_CONFIG_CONTEXT=default

ENTRYPOINT      ["python3"]
CMD             ["lcm_engine/main.py"]

EXPOSE          8080
