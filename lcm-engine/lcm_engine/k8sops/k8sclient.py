import logging
import os
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pythonping import ping

runtime_env = os.getenv("RUNTIME_ENVIRONMENT", "local").lower()

if runtime_env in ("k8s", "kubernetes"):
    config.load_incluster_config()
else:
    _default_kube_config_path = str(Path(__file__).parent.parent / Path("kube-config"))
    kube_config = os.getenv("LCM_ENGINE_KUBE_CONFIG_PATH", _default_kube_config_path)
    kube_context = os.getenv("LCM_ENGINE_KUBE_CONFIG_CONTEXT", "default")

    config.load_kube_config(context=kube_context)

core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
custom_v1 = client.CustomObjectsApi()


def check_connectivity() -> bool:
    logging.info("Checking connectivity with k8s")
    try:
        core_v1.list_namespace(_request_timeout=3, limit=1)
        return True
    except ApiException as err:
        logging.error(f"Cannot list namespaces: {err}")
        return False


def can_ping_pod(host: str) -> bool:
    try:
        responses = ping(host, count=1)
        return len(responses) > 0
    except PermissionError as err:
        logging.error(f"Ping should be run as root: {err}")

    return False
