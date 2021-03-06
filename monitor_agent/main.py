from core.command import Command
from core.helper import getLogger
from fastapi import FastAPI, UploadFile, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi_utils.tasks import repeat_every
from settings import Settings
import contextlib
import json
import logging
import requests
import uvicorn


try:
    CONFIG = Settings()
except json.decoder.JSONDecodeError as msg:
    logging.critical(f'Error in "settings.json". {msg}')
    exit()

getLogger(CONFIG.logging.level, CONFIG.logging.filename)

from core.metricFunctions import send_metrics, send_metrics_adapter, static, dynamic

api = FastAPI()
security = HTTPBasic()

endpoints = {
    "root": "/",
    "command": "/command/",
    "metrics": "/metrics/",
    "settings": "/settings/",
    "thresholds": "/thresholds/",
}


async def check_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
) -> None:
    """Checks if the credentials are correct.

    Args:
        credentials (HTTPBasicCredentials, optional): Credentials. Defaults to Depends(security).

    Raises:
        HTTPException: Raises a 401 error if the credentials are incorrect.
    """
    if (
        credentials.username != "monitor"
        and credentials.password != CONFIG.auth.user_token
    ):
        raise HTTPException(status_code=401, detail="Incorrect credentials")


# GET
@api.get(endpoints["root"])
async def root(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    """Endpoint for the root of the API.

    Args:
        credentials (HTTPBasicCredentials, optional): Credentials. Defaults to Depends(security).

    Returns:
        dict: Dictionary with the endpoints.
    """
    await check_credentials(credentials)
    return {"endpoints": endpoints}


@api.get(endpoints["thresholds"])
async def thresholds(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    """Endpoint for getting the thresholds.

    Args:
        credentials (HTTPBasicCredentials, optional): Credentials. Defaults to Depends(security).

    Returns:
        dict: Dictionary with the thresholds.
    """
    await check_credentials(credentials)
    return {"thresholds": CONFIG.thresholds.__dict__}


if CONFIG.metrics.get_endpoint:

    @api.get(endpoints["metrics"])
    async def metrics_endpoint(
        credentials: HTTPBasicCredentials = Depends(security),
    ) -> dict:
        """Endpoint for getting the metrics.

        Args:
            credentials (HTTPBasicCredentials, optional): Credentials. Defaults to Depends(security).

        Returns:
            dict: Dictionary with the metrics.
        """
        await check_credentials(credentials)
        elapsed_time, data = send_metrics_adapter([static, dynamic])
        return {"data": data, "elapsed_time": elapsed_time}


# POST
@api.post(endpoints["command"])
async def command(
    command: str, timeout: int, credentials: HTTPBasicCredentials = Depends(security)
) -> dict:
    """Executes a command and returns the output.

    Args:
        command (str): Command as string.
        timeout (int): Timeout in seconds for the command to finish.
        credentials (HTTPBasicCredentials, optional): Credentials. Defaults to Depends(security).

    Returns:
        dict: A dictionary with the output of the command.
    """
    await check_credentials(credentials)
    return Command(command, timeout).__dict__


@api.post(endpoints["settings"])
async def mod_settings(
    settings: UploadFile, credentials: HTTPBasicCredentials = Depends(security)
) -> dict:
    """Modifies the settings.json file.

    Args:
        settings (UploadFile): A file containing the new settings.
        credentials (HTTPBasicCredentials, optional): Credentials. Defaults to Depends(security).

    Returns:
        dict: Dict with status of the write operation, and the data as a dictionary if successful.
    """
    await check_credentials(credentials)
    global CONFIG
    data: str = settings.file.read().decode()
    msg = CONFIG.write_settings(data)
    CONFIG = Settings()
    return msg


logging.debug(f"POST Interval: {CONFIG.metrics.post_interval}")


@api.on_event("startup")
@repeat_every(seconds=CONFIG.metrics.post_interval, logger=logging, wait_first=True)
def periodic() -> None:
    """Sends metrics to the server at a given interval. Also sends alerts in case the thresholds are exceeded."""
    # https://github.com/tiangolo/fastapi/issues/520
    # https://fastapi-utils.davidmontague.xyz/user-guide/repeated-tasks/#the-repeat_every-decorator
    # Changed Timeloop for this
    elapsed_time, metrics = send_metrics_adapter([static, dynamic])
    send_metrics(
        elapsed_time=elapsed_time,
        metrics=metrics,
        file_enabled=CONFIG.metrics.enable_logfile,
        file_path=CONFIG.metrics.log_filename,
        metric_endpoint=CONFIG.endpoints.metric_endpoint,
        agent_endpoint=CONFIG.endpoints.agent_endpoint,
        agent_token=CONFIG.auth.agent_token,
        user_token=CONFIG.auth.user_token,
        name=CONFIG.auth.name,
    )

    alert = {
        "cpu_percent": metrics["cpu_percent"],
        "ram_percent": metrics["ram"]["percent"],
    }

    with contextlib.suppress(KeyError):
        if metrics.get("processes", None):
            alert["processes"] = metrics["processes"]

    if (
        metrics.get("cpu_percent", 0) >= CONFIG.thresholds.cpu_percent
        or metrics.get("ram", {}).get("percent", 0) >= CONFIG.thresholds.ram_percent
    ):
        try:
            agent_endpoint = CONFIG.endpoints.agent_endpoint
            agent_token = CONFIG.auth.agent_token
            agent_token = f"{agent_endpoint}{agent_token}/"
            alert["agent"] = agent_token
            r = requests.post(
                CONFIG.alerts.url,
                json=alert,
                headers={"Authorization": f"Token {CONFIG.auth.user_token}"},
            )
            logging.debug(f"Alert Response: {r.text}")
            logging.debug(f"Alert Status Code: {r.status_code}")
        except requests.exceptions.InvalidSchema:
            logging.error(
                f"Agent could not send an alert to {CONFIG.alerts.url}", exc_info=True
            )


def start() -> None:
    """Retrieves the Uvicorn server settings and starts the server."""
    uviconfig = {"app": "main:api", "interface": "asgi3"}
    uviconfig.update(CONFIG.uvicorn.__dict__)
    uviconfig.pop("__module__", None)
    uviconfig.pop("__dict__", None)
    uviconfig.pop("__weakref__", None)
    uviconfig.pop("__doc__", None)
    try:
        uvicorn.run(**uviconfig)
    except Exception:
        logging.critical("Unable to run server.", exc_info=True)


if __name__ == "__main__":
    start()
