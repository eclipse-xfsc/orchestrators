import logging
from abc import ABC, abstractmethod
from base64 import b64encode
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, List, Mapping, Union
from zipfile import ZipFile
import re

import yaml
from kubernetes.client.models.v1_config_map import V1ConfigMap
from kubernetes.client.models.v1_config_map_volume_source import \
    V1ConfigMapVolumeSource
from kubernetes.client.models.v1_container import V1Container
from kubernetes.client.models.v1_container_port import V1ContainerPort
from kubernetes.client.models.v1_deployment import V1Deployment
from kubernetes.client.models.v1_deployment_spec import V1DeploymentSpec
from kubernetes.client.models.v1_empty_dir_volume_source import \
    V1EmptyDirVolumeSource
from kubernetes.client.models.v1_env_var import V1EnvVar
from kubernetes.client.models.v1_env_var_source import V1EnvVarSource
from kubernetes.client.models.v1_key_to_path import V1KeyToPath
from kubernetes.client.models.v1_label_selector import V1LabelSelector
from kubernetes.client.models.v1_namespace import V1Namespace
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from kubernetes.client.models.v1_pod_spec import V1PodSpec
from kubernetes.client.models.v1_pod_template_spec import V1PodTemplateSpec
from kubernetes.client.models.v1_secret import V1Secret
from kubernetes.client.models.v1_secret_key_selector import V1SecretKeySelector
from kubernetes.client.models.v1_secret_volume_source import \
    V1SecretVolumeSource
from kubernetes.client.models.v1_service import V1Service
from kubernetes.client.models.v1_service_port import V1ServicePort
from kubernetes.client.models.v1_service_spec import V1ServiceSpec
from kubernetes.client.models.v1_volume import V1Volume
from kubernetes.client.models.v1_volume_mount import V1VolumeMount
from kubernetes.client.models.v1_local_object_reference import \
    V1LocalObjectReference
from kubernetes.client.exceptions import ApiException

from lcm_engine.k8sops.k8sclient import (
    apps_v1, can_ping_pod, core_v1, custom_v1
)
from lcm_engine.k8sops.terraform import PATHS as TERRAFORM_PATHS
from lcm_engine.k8sops.tosca import PATHS as TOSCA_PATHS
from lcm_engine.k8sops.util import TPath, secret_key_name
from lcm_engine.models.secret import Secret


def construct_namespace_name(workspace_id: int, project_id: int) -> str:
    logging.info(
        "Constructing namespace name for "
        f"workspace ID {workspace_id} and "
        f"project ID {project_id}"
    )
    namespace = f"lcm-service-w{workspace_id}-p{project_id}"
    return namespace


def filter_by_has_attr(lst: List[Any], attr: str) -> List[Any]:
    return [
        item for item in lst
        if hasattr(item, attr) and getattr(item, attr)
    ]


def get_lcm_service_status_phase(workspace_id: int, project_id: int) -> str:
    logging.info(
        f"Get pod status for workspace ID {workspace_id} "
        f"and project ID {project_id}"
    )
    namespace_name = construct_namespace_name(workspace_id, project_id)
    return core_v1.list_namespaced_pod(namespace_name).items[0].status.phase


def get_hostname(
    namespace_name: str,
    service_name: str = "lcm-service",
    cluster_name: str = "cluster.local",
) -> str:
    return f"{service_name}.{namespace_name}.svc.{cluster_name}"


def can_ping_lcm_service(namespace_name: str) -> bool:
    hostname = get_hostname(namespace_name)
    can_ping = can_ping_pod(hostname)
    return can_ping


def undeploy_lcm_service(workspace_id: int, project_id: int) -> V1Namespace:
    namespace_name = construct_namespace_name(workspace_id, project_id)
    msg = f"Deleting namespace {namespace_name} and all its resources"
    logging.info(msg)
    return core_v1.delete_namespace(namespace_name)


def create_debug_zip(namespace_name: str) -> BytesIO:
    try:
        pod_list = core_v1.list_namespaced_pod(namespace_name)
        pod = pod_list.items[0]

        pod_name = pod.metadata.name

        log = core_v1.read_namespaced_pod_log(
            name=pod_name, namespace=namespace_name
        )

        buf = BytesIO()
        with ZipFile(buf, mode="w") as zf:
            zf.writestr("debug.log", log)

        buf.seek(0)
        return buf
    except ApiException as err:
        msg = (
            f"Cannot obtain logs of pod {pod_name} "
            f"in namespace {namespace_name}: {err}"
        )
        logging.error(msg)
        raise ValueError(msg)


class K8sResource(ABC):
    def __init__(self):
        self._template = None

    @property
    def template(self):
        return self._template

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def create(self):
        pass

    def __str__(self):
        template = self._template

        if template is None:
            return str(template)

        stream = StringIO()
        yaml.dump(template, stream)

        return stream.getvalue()

    def __repr__(self):
        return str(self._template)


class K8sNamespace(K8sResource):
    def __init__(self, workspace_id: int, project_id: int):
        super().__init__()

        self._workspace_id = workspace_id
        self._project_id = project_id

        self._name = construct_namespace_name(
            workspace_id, project_id
        )

    def build(self) -> V1Namespace:
        logging.info("Build namespace")

        self._template = V1Namespace(metadata=V1ObjectMeta(name=self._name))

        logging.debug(self)

        return self._template

    def create(self) -> V1Namespace:
        logging.info("Create namespace")

        self._namespace = core_v1.create_namespace(self._template)

        return self._namespace


class K8sConfigMap(K8sResource):
    def __init__(
        self, namespace_name: str, config_map_name: str, b64_csar: str
    ):
        super().__init__()

        self._namespace_name = namespace_name
        self._config_map_name = config_map_name
        self._b64_csar = b64_csar

    def build(self) -> V1ConfigMap:
        logging.info("Build config map")

        self._template = V1ConfigMap(
            metadata=V1ObjectMeta(name=self._config_map_name),
            binary_data={"csar.zip": self._b64_csar},
        )

        logging.debug(self)

        return self._template

    def create(self) -> V1ConfigMap:
        logging.info("Create config map")

        self._config_map = core_v1.create_namespaced_config_map(
            self._namespace_name, self._template
        )

        return self._config_map


class K8sService(K8sResource):
    def __init__(
        self,
        namespace_name: str,
        service_name: str,
        port: int = 9999,
        target_port: int = 8080
    ):
        super().__init__()

        self._namespace_name = namespace_name
        self._service_name = service_name
        self._app_label = dict(app=service_name)
        self._port = port
        self._target_port = target_port

    def build(self) -> V1Service:
        logging.info("Build service")

        self._template = V1Service(
            metadata=V1ObjectMeta(
                name=self._service_name, labels=self._app_label
            ),
            spec=V1ServiceSpec(
                selector=self._app_label,
                ports=[
                    V1ServicePort(
                        name="api",
                        port=self._port,
                        target_port=self._target_port,
                    )
                ],
                type="ClusterIP",
            ),
        )

        logging.debug(self)

        return self._template

    def create(self) -> V1Service:
        logging.info("Create service")

        self._service = core_v1.create_namespaced_service(
            self._namespace_name, self._template
        )

        return self._service


class K8sDeployment(K8sResource):
    def __init__(
        self,
        namespace_name: str,
        deployment_name: str,

        file_secret_name: str,
        container_image: str,
        working_dir: Path,
        container_port: int,
        env: Mapping[str, str],
        secrets: List[Secret],
        env_secret_name: str,

        image_pull_secret_name: Union[str, None],
    ):
        super().__init__()

        self._namespace_name = namespace_name
        self._deployment_name = deployment_name

        self._file_secret_name = file_secret_name
        self._container_image = container_image
        self._working_dir = working_dir
        self._container_port = container_port
        self._env = env
        self._secrets = secrets
        self._env_secret_name = env_secret_name

        self._app_label = dict(app=self._deployment_name)

        self._image_pull_secret_name = image_pull_secret_name

    @property
    def app_label(self) -> str:
        return self._app_label

    def _build_pod(self) -> V1PodSpec:
        return K8sPodSpec(
            self._file_secret_name,
            self._deployment_name,
            self._container_image,
            self._working_dir,
            self._container_port,
            self._env,
            self._secrets,
            self._env_secret_name,
            self._image_pull_secret_name,
        ).build()

    def build(self) -> V1Deployment:
        logging.info("Build deployment")

        self._template = V1Deployment(
            metadata=V1ObjectMeta(
                name=self._deployment_name, labels=self._app_label
            ),
            spec=V1DeploymentSpec(
                selector=V1LabelSelector(match_labels=self._app_label),
                template=V1PodTemplateSpec(
                    metadata=V1ObjectMeta(labels=self._app_label),
                    spec=self._build_pod()
                ),
            ),
        )

        logging.debug(self)

        return self._template

    def create(self) -> V1Deployment:
        logging.info("Create deployment")

        self._deployment = apps_v1.create_namespaced_deployment(
            self._namespace_name, self._template
        )
        return self._deployment


class K8sSecret(K8sResource):
    def __init__(
        self, namespace_name: str, secret_name: str, secrets: List[Secret]
    ):
        super().__init__()

        self._namespace_name = namespace_name
        self._secret_name = secret_name

        self._secrets = secrets

    def build(self) -> V1Secret:
        logging.info("Build secret")

        self._template = V1Secret(
            metadata=V1ObjectMeta(name=self._secret_name), data=dict()
        )

        for secret in self._secrets:
            for key, value in self._get_dict(secret).items():
                value_bytes = bytes(value, encoding="utf-8")
                b64_value_bytes = b64encode(value_bytes)
                b64_value = b64_value_bytes.decode()
                self._template.data[key] = b64_value

        logging.debug(self)

        return self._template

    def create(self) -> V1Secret:
        logging.info("Create secret")

        self._secret = core_v1.create_namespaced_secret(
            self._namespace_name, self._template
        )

        return self._secret

    @abstractmethod
    def _get_dict(self, secret: Secret) -> Mapping[str, str]:
        pass

    def __bool__(self):
        return self._template and self._template.data


class K8sFileSecret(K8sSecret):
    def __init__(
        self,
        namespace_name: str,
        secret_name_prefix: str,
        secrets: List[Secret]
    ):
        file_secrets = [
            secret for secret in secrets
            if hasattr(secret, "file") and secret.file
        ]
        secret_name = f"{secret_name_prefix}-file"
        super().__init__(namespace_name, secret_name, file_secrets)

    def _get_dict(self, secret):
        return {self._get_key(secret): self._get_value(secret)}

    def _get_key(self, secret):
        return secret_key_name(Path(secret.file.path))

    def _get_value(self, secret):
        return secret.file.contents  # base64 encoded


class K8sEnvSecret(K8sSecret):
    def __init__(
        self,
        namespace_name: str,
        secret_name_prefix: str,
        secrets: List[Secret]
    ):
        env_secrets = [
            secret for secret in secrets
            if hasattr(secret, "env") and secret.env
        ]
        secret_name = f"{secret_name_prefix}-env"
        super().__init__(namespace_name, secret_name, env_secrets)

    def _get_dict(self, secret):
        return dict(secret.env)


class K8sImagePullSecret(K8sResource):
    def __init__(
        self,
        namespace_name: str,
        secret_name: str,
    ):
        super().__init__()

        self._namespace_name = namespace_name
        self._secret_name = secret_name

    def _get_secret(self):
        # Get secret from the lcm-engine namespace
        secret = core_v1.read_namespaced_secret(
            self._secret_name, "lcm-engine"
        )
        return secret

    def build(self) -> V1Secret:
        logging.info("Build image pull secret")

        secret = self._get_secret()

        self._template = V1Secret(
            metadata=V1ObjectMeta(
                name=self._secret_name,
                namespace=self._namespace_name,
            ),
            type=secret.type,
            data=secret.data,
        )

        logging.debug(self)

        return self._template

    def create(self) -> V1Secret:
        logging.info("Create image pull secret")

        secret = core_v1.create_namespaced_secret(
            self._namespace_name, self._template
        )

        return secret


class K8sPodSpec(K8sResource):
    def __init__(
        self,
        file_secret_name: str,
        deployment_name: str,
        container_image: str,
        working_dir: Path,
        container_port: int,
        env: Mapping[str, str],
        secrets: List[Secret],
        env_secret_name: str,
        image_pull_secret_name: Union[str, None],
    ):
        self.file_secret_name = file_secret_name
        self.deployment_name = deployment_name
        self.config_map_name = deployment_name
        self.container_image = container_image
        self.working_dir = working_dir
        self.container_port = container_port
        self.env = env
        self.secrets = secrets
        self.env_secret_name = env_secret_name
        self.image_pull_secret_name = image_pull_secret_name

    def _define_volumes(self) -> List[V1Volume]:
        volumes = [
            V1Volume(
                name="compressed-deployment-package",
                config_map=V1ConfigMapVolumeSource(
                    name=self.config_map_name
                )
            ),
            V1Volume(
                name="extracted-deployment-package",
                empty_dir=V1EmptyDirVolumeSource()
            )
        ]

        visited = set()
        for secret in self.secrets:
            if id(secret) in visited:
                continue
            visited.add(id(secret))
            if hasattr(secret, "file") and secret.file:
                secret_file_path = Path(secret.file.path)
                key_name = secret_key_name(secret_file_path)
                volumes.append(
                    V1Volume(
                        name=key_name,
                        secret=V1SecretVolumeSource(
                            secret_name=self.file_secret_name,
                            items=[
                                V1KeyToPath(
                                    key=key_name, path=secret_file_path.name
                                )
                            ]
                        )
                    )
                )

        return volumes

    def build(self) -> V1PodSpec:
        pod_spec = V1PodSpec(
            containers=[
                K8sLCMServiceContainer(
                    self.deployment_name,
                    self.container_image,
                    self.working_dir,
                    self.container_port,
                    self.env,
                    self.secrets,
                    self.env_secret_name
                ).build()
            ],
            init_containers=[
                K8sLCMServiceInitContainer(
                    self.working_dir
                ).build()
            ],
            volumes=self._define_volumes()
        )

        if self.image_pull_secret_name:
            pod_spec.image_pull_secrets = [
                V1LocalObjectReference(name=self.image_pull_secret_name)
            ]

        return pod_spec

    def create(self):
        pass


class K8sLCMServiceContainer(K8sResource):
    def __init__(
        self,
        deployment_name: str,
        image: str,
        working_dir: Path,
        container_port: int,
        env: Mapping[str, str],
        secrets: List[Secret],
        env_secret_name: str
    ):
        self.deployment_name = deployment_name
        self.image = image
        self.working_dir = working_dir
        self.container_port = container_port
        self.env = env
        self.secrets = secrets
        self.env_secret_name = env_secret_name

    def build(self) -> V1Container:
        env = [
            V1EnvVar(name=name, value=value)
            for name, value in self.env.items()
        ]
        volume_mounts = [
            V1VolumeMount(
                name="extracted-deployment-package",
                mount_path=self.working_dir.as_posix(),
                sub_path=self.working_dir.name,
                read_only=False
            )
        ]

        visited = set()
        for secret in self.secrets:
            if id(secret) in visited:
                continue
            visited.add(id(secret))
            if hasattr(secret, "file") and secret.file:
                secret_file_path = Path(secret.file.path)
                volume_mounts.append(
                    V1VolumeMount(
                        name=secret_key_name(secret_file_path),
                        read_only=True,
                        mount_path=secret_file_path.as_posix(),
                        sub_path=secret_file_path.name
                    )
                )
            if hasattr(secret, "env") and secret.env:
                for key in secret.env.keys():
                    env.append(
                        V1EnvVar(
                            name=key,
                            value_from=V1EnvVarSource(
                                secret_key_ref=V1SecretKeySelector(
                                    name=self.env_secret_name,
                                    key=key,
                                    optional=False
                                )
                            )
                        )
                    )

        return V1Container(
            name=self.deployment_name,
            image=self.image,
            working_dir=self.working_dir.as_posix(),
            ports=[V1ContainerPort(container_port=self.container_port)],
            volume_mounts=volume_mounts,
            env=env
        )

    def create(self):
        pass


class K8sLCMServiceInitContainer(K8sResource):
    def __init__(
        self,
        extracted_deployment_package_mount_path: Path,
        image: str = "public.ecr.aws/docker/library/busybox"
    ):
        self.extracted_deployment_package_mount_path = extracted_deployment_package_mount_path
        self.image = image

    def build(self) -> V1Container:
        return V1Container(
            name="prepare-directory-structure",
            image=self.image,
            command=["/bin/sh"],
            args=[
                "-c",
                "unzip -o /data/csar.zip -d "
                f"'{self.extracted_deployment_package_mount_path}'"
            ],
            volume_mounts=[
                V1VolumeMount(
                    name="compressed-deployment-package",
                    mount_path="/data",
                    read_only=True
                ),
                V1VolumeMount(
                    name="extracted-deployment-package",
                    mount_path=self.extracted_deployment_package_mount_path.as_posix(),
                    sub_path=self.extracted_deployment_package_mount_path.name,
                    read_only=False
                )
            ]
        )

    def create(self):
        pass


class K8sMiddleware(K8sResource):
    def __init__(
        self,
        namespace_name: str,
        middleware_name: str,
        workspace_id: int,
        project_id: int
    ):
        super().__init__()

        self._namespace_name = namespace_name
        self._middleware_name = middleware_name

        self._prefixes = [
            f"/workspace/{workspace_id}/project/{project_id}"
        ]

    def build(self) -> Mapping[str, Any]:
        logging.info("Build Middleware")

        self._template = dict(
            apiVersion="traefik.containo.us/v1alpha1",
            kind="Middleware",
            metadata=V1ObjectMeta(
                name=self._middleware_name, namespace=self._namespace_name
            ),
            spec=dict(
                stripPrefix=dict(
                    prefixes=self._prefixes
                )
            )
        )

        logging.debug(self)

        return self._template

    def create(self) -> Mapping[str, Any]:
        logging.info("Create Middleware")

        middleware = custom_v1.create_namespaced_custom_object(
            group="traefik.containo.us",
            version="v1alpha1",
            namespace=self._namespace_name,
            plural="middlewares",
            body=self._template,
        )

        return middleware


class K8sIngressRoute(K8sResource):
    def __init__(
        self,
        namespace_name: str,
        ingress_route_name: str,
        paths: List[str],
        workspace_id: int,
        project_id: int,
        service_name: str,
        middleware_name: str,
        port: int = 8080,
        priority: int = 5,
        hostname: Union[str, None] = None,
        certificate_secret_name: Union[str, None] = None,
    ):
        super().__init__()

        self._namespace_name = namespace_name
        self._ingress_route_name = ingress_route_name
        self._paths = paths
        self._workspace_id = workspace_id
        self._project_id = project_id
        self._service_name = service_name
        self._middleware_name = middleware_name
        self._certificate_secret_name = certificate_secret_name
        self._port = port
        self._priority = priority
        self._hostname = hostname

    def create(self) -> Mapping[str, Any]:
        logging.info("Create IngressRoute")

        ingress_route = custom_v1.create_namespaced_custom_object(
            group="traefik.containo.us",
            version="v1alpha1",
            namespace=self._namespace_name,
            plural="ingressroutes",
            body=self._template,
        )

        return ingress_route

    def get_for_lcm_engine(self) -> Mapping[str, Any]:
        logging.info("Get IngressRoute for LCM Engine")

        ingress_route = custom_v1.get_namespaced_custom_object(
            group="traefik.containo.us",
            version="v1alpha1",
            namespace="lcm-engine",
            plural="ingressroutes",
            name="lcm-engine"
        )

        return ingress_route

    def _get_hostname(self, ingress_route: Mapping[str, Any]) -> str:
        hostname = self._hostname

        if not hostname:
            host_re = re.compile(r"Host\s*[(]\s*`(?P<host>[^`]+)`\s*[)]")

            try:
                lcm_engine_route0_match = ingress_route["spec"]["routes"][0]["match"]
                logging.debug(f"LCM Engine's first route match: {lcm_engine_route0_match}")
                hostname = host_re.search(lcm_engine_route0_match).group("host").strip()
            except (KeyError, IndexError, TypeError, AttributeError) as err:
                logging.error(f"Cannot extract LCM Engine's first route match: {err}")

        logging.debug(f"LCM Services' hostname: {hostname}")

        return hostname

    def _get_ingress_route(self) -> Mapping[str, Any]:
        try:
            ingress_route = self.get_for_lcm_engine()
        except ApiException as err:
            logging.warn(f"Cannot obtain LCM Engine's ingress route: {err}")
            ingress_route = dict()

        return ingress_route

    def _get_middleware(self, middleware_name: str, namespace_name="lcm-engine") -> Mapping[str, Any]:
        logging.info(f"Get middleware {middleware_name} in namespace {namespace_name}")

        middleware = custom_v1.get_namespaced_custom_object(
            group="traefik.containo.us",
            version="v1alpha1",
            namespace=namespace_name,
            plural="middlewares",
            name=middleware_name
        )

        return middleware

    def _create_middleware(self, name: str, spec: Mapping[str, Any]) -> Mapping[str, Any]:
        body = dict(
            apiVersion="traefik.containo.us/v1alpha1",
            kind="Middleware",
            metadata=V1ObjectMeta(
                name=name, namespace=self._namespace_name
            ),
            spec=spec
        )

        middleware = custom_v1.create_namespaced_custom_object(
            group="traefik.containo.us",
            version="v1alpha1",
            namespace=self._namespace_name,
            plural="middlewares",
            body=body,
        )

        return middleware

    def _create_secret(self, secret: V1Secret):
        logging.debug(
            f"Creating secret {secret.metadata.name} in namespace {self._namespace_name}"
        )
        secret = V1Secret(
            metadata=V1ObjectMeta(
                name=secret.metadata.name, namespace=self._namespace_name
            ), data=secret.data
        )
        return core_v1.create_namespaced_secret(
            namespace=self._namespace_name, body=secret
        )

    def _get_secret(self, secret_name: str, namespace="lcm-engine") -> V1Secret:
        logging.debug(f"Obtaining secret {secret_name} from namespace {namespace}")
        return core_v1.read_namespaced_secret(secret_name, namespace=namespace)

    def _extract_secret(self, middleware_name: str, middleware: Mapping[str, Any]):
        try:
            secret_name = middleware["spec"]["basicAuth"]["secret"]
            secret = self._get_secret(secret_name)
            self._create_secret(secret)
        except KeyError as err:
            logging.debug(
                "Attempted to extract basicAuth secret name from "
                f"middleware {middleware_name}: {err}"
            )
        except ApiException as err:
            logging.error(f"Cannot obtain or create secret {secret_name}: {err}")

    def _assign_middlewares(self, ingress_route: Mapping[str, Any]) -> List[Mapping[str, str]]:
        try:
            middlewares = ingress_route["spec"]["routes"][0]["middlewares"]
            mids = []

            for middleware in middlewares:
                name = middleware["name"]
                middleware = self._get_middleware(name)
                self._extract_secret(name, middleware)
                self._create_middleware(name, middleware["spec"])

                mids.append(dict(name=name))

            middlewares = mids

        except (KeyError, IndexError) as err:
            logging.warn("No LCM Engine's middlewares found")
            logging.debug(str(err))
            middlewares = []
        except ApiException as err:
            logging.error(f"Cannot obtain or create middleware: {err}")
            middlewares = []

        middlewares.append(dict(name=self._middleware_name))

        return middlewares

    def _assign_routes(
        self, hostname: Union[None, str], middlewares: List[Mapping[str, str]]
    ) -> List[Mapping[str, Any]]:
        path_prefix = (
            f"/workspace/{self._workspace_id}"
            f"/project/{self._project_id}"
        )
        routes = []
        for path in self._paths:
            t_path = TPath(path, hostname=hostname)
            path_str = t_path.to_traefik_path(path_prefix)
            route = dict(
                kind="Rule",
                match=path_str,
                priority=self._priority,
                services=[
                    dict(
                        name=self._service_name,
                        port=self._port
                    )
                ],
                middlewares=middlewares
            )

            routes.append(route)

        return routes

    def _assign_tls(self, ingress_route: Mapping[str, Any]) -> Mapping[str, Any]:
        tls = None

        try:
            if self._certificate_secret_name:
                tls = dict(secretName=self._certificate_secret_name)
            else:
                tls = ingress_route["spec"]["tls"]
        except KeyError as err:
            logging.warn(f"No TLS key in LCM Engine's ingress route: {err}")

        return tls

    def _assign_entry_points(self, ingress_route: Mapping[str, Any]) -> List[str]:
        entry_points = ["web"]

        try:
            if self._certificate_secret_name:
                entry_points = ["websecure"]
            else:
                entry_points = ingress_route["spec"]["entryPoints"]
        except KeyError as err:
            logging.warn(f"Cannot obtain LCM Engine's ingress route entry points: {err}")

        return entry_points

    def build(self) -> Mapping[str, Any]:
        logging.info("Build ingress route")

        ingress_route = self._get_ingress_route()
        hostname = self._get_hostname(ingress_route)
        middlewares = self._assign_middlewares(ingress_route)

        entry_points = self._assign_entry_points(ingress_route)
        routes = self._assign_routes(hostname, middlewares)
        tls = self._assign_tls(ingress_route)

        self._template = dict(
            apiVersion="traefik.containo.us/v1alpha1",
            kind="IngressRoute",
            metadata=V1ObjectMeta(
                name=self._ingress_route_name,
                namespace=self._namespace_name
            ),
            spec=dict(
                entryPoints=entry_points,
                routes=routes,
                tls=tls
            )
        )

        logging.debug(self)

        return self._template


class LCMServiceDeployer:
    def __init__(
        self,

        workspace_id: int,
        project_id: int,
        deployment_name: str,

        container_image: str,
        container_port: int,
        working_dir: Path,
        env: Mapping[str, str],

        b64_deployment_package: str,

        secrets: List[Secret] = [],

        hostname: Union[str, None] = None,
        certificate_secret_name: Union[str, None] = None,

        image_pull_secret_name: Union[str, None] = None,
    ):
        self._workspace_id = workspace_id
        self._project_id = project_id
        self._namespace_name = construct_namespace_name(
            workspace_id, project_id
        )

        self._deployment_name = deployment_name
        self._config_map_name = deployment_name
        self._service_name = deployment_name
        self._secret_name_prefix = deployment_name
        self._middleware_name = "strip-path-prefix"
        self._ingress_route_name = deployment_name

        self._paths = []
        if deployment_name == "tosca":
            self._paths = TOSCA_PATHS
        elif deployment_name == "terraform":
            self._paths = TERRAFORM_PATHS

        self._container_image = container_image
        self._container_port = container_port
        self._working_dir = working_dir
        self._env = env

        self._b64_deployment_package = b64_deployment_package
        self._secrets = secrets
        self._file_secrets = filter_by_has_attr(secrets, "file")
        self._env_secrets = filter_by_has_attr(secrets, "env")

        self._env_secret_name = None
        self._file_secret_name = None

        self._hostname = hostname
        self._certificate_secret_name = certificate_secret_name

        self._image_pull_secret_name = image_pull_secret_name

    @property
    def namespace_name(self):
        return self._namespace_name

    def deploy(self):
        logging.info("Deploying on k8s")

        self._create_namespace()
        self._create_config_map()
        if self._secrets:
            self._create_secrets()
        if self._image_pull_secret_name:
            self._create_image_pull_secret()
        self._create_deployment()
        self._create_service()
        self._create_middleware()
        self._create_ingress_route()

    def _create_namespace(self):
        ns = K8sNamespace(
            self._workspace_id,
            self._project_id
        )

        ns.build()
        ns.create()

    def _create_config_map(self):
        cm = K8sConfigMap(
            self._namespace_name,
            self._config_map_name,
            self._b64_deployment_package
        )

        cm.build()
        cm.create()

    def _create_secrets(self):
        if self._env_secrets:
            env_secret = K8sEnvSecret(
                self._namespace_name,
                self._secret_name_prefix,
                self._env_secrets
            )

            self._env_secret_name = env_secret._secret_name

            env_secret.build()
            env_secret.create()

        if self._file_secrets:
            file_secret = K8sFileSecret(
                self._namespace_name,
                self._secret_name_prefix,
                self._file_secrets
            )

            self._file_secret_name = file_secret._secret_name

            file_secret.build()
            file_secret.create()

    def _create_image_pull_secret(self):
        ips = K8sImagePullSecret(
            self._namespace_name,
            self._image_pull_secret_name
        )

        ips.build()
        ips.create()

    def _create_deployment(self):
        d = K8sDeployment(
            self._namespace_name,
            self._deployment_name,

            self._file_secret_name,
            self._container_image,
            self._working_dir,
            self._container_port,
            self._env,
            self._secrets,
            self._env_secret_name,
            self._image_pull_secret_name,
        )

        d.build()
        d.create()

    def _create_service(self):
        svc = K8sService(
            self._namespace_name,
            self._service_name,
            port=self._container_port
        )

        svc.build()
        svc.create()

    def _create_middleware(self):
        mw = K8sMiddleware(
            self._namespace_name,
            self._middleware_name,
            self._workspace_id,
            self._project_id
        )

        mw.build()
        mw.create()

    def _create_ingress_route(self):
        ir = K8sIngressRoute(
            self._namespace_name,
            self._ingress_route_name,
            self._paths,
            self._workspace_id,
            self._project_id,
            self._service_name,
            self._middleware_name,
            port=self._container_port,
            hostname=self._hostname,
            certificate_secret_name=self._certificate_secret_name
        )

        ir.build()
        ir.create()
