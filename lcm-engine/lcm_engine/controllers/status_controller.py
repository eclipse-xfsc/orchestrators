import logging

from lcm_engine.db_models.models import db
from lcm_engine.k8sops import k8sclient
from lcm_engine.models.health_response import HealthResponse  # noqa: E501


def health():  # noqa: E501
    """Get application health

     # noqa: E501


    :rtype: Union[HealthResponse, Tuple[HealthResponse, int], Tuple[HealthResponse, int, Dict[str, str]]
    """

    logging.info("Checking health")

    dependencies = []

    logging.info("Checking database")
    database_ok = True
    query = "select * from user limit 1"
    logging.debug(f"Executing query: {query}")
    try:
        db.session.execute(db.text(query)).all()
    except Exception as ex:
        logging.error(f"Querying database failed: {ex}")
        database_ok = False
    dependencies.append(HealthResponse(healthy=database_ok, name="database"))

    k8s_ok = k8sclient.check_connectivity()
    dependencies.append(HealthResponse(healthy=k8s_ok, name="k8s"))

    app_ok = all(dependency.healthy for dependency in dependencies)

    status_code = 200 if app_ok else 503

    return (
        HealthResponse(
            dependencies=dependencies, healthy=app_ok, name="application"
        ),
        status_code,
    )
