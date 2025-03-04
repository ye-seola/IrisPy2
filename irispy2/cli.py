import json
import os
import shlex
import subprocess
import tempfile
import platform
import time
from typing import Annotated
import typer
import requests
from loguru import logger
from ppadb.client import Client as AdbClient
from ppadb.device import Device

IRIS_PACKAGE_NAME = "party.qwer.iris.Main"
IRIS_CONFIG_PATH = "/data/local/tmp/config.json"
IRIS_INSTALL_PATH = "/data/local/tmp/Iris.dex"
IRIS_LOG_PATH = "/data/local/tmp/iris.log"
IRIS_PROCESS_NAME = "Iris.app_process"

app = typer.Typer(add_completion=False, no_args_is_help=True)

client = AdbClient()


def get_device_ip_list(device: Device):
    resp: str = device.shell(
        "ip -4 -o addr show scope global | awk '{print $4}' | cut -d/ -f1"
    )
    resp = resp.strip()
    return resp.split("\n")


def device_ping(device: Device, host: str):
    resp: str = device.shell(
        shlex.join(["ping", "-c", "1", "-W", "1", host]) + " > /dev/null 2>&1; echo $?"
    )
    resp = resp.strip()
    return resp == "0"


def ping(host: str):
    res = subprocess.call(
        (
            ["ping", "-n", "1", "-w", "1000", host]
            if platform.system().lower() == "windows"
            else ["ping", "-c", "1", "-W", "1", host]
        ),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    return res == 0


def kill_iris(device: Device):
    pid = get_iris_pid(device)
    if pid is None:
        return False

    resp: str = device.shell(f'su -c "kill -9 {pid}; echo $?"')
    resp = resp.strip()

    if resp == "0":
        return True
    else:
        return False


def get_device(serial: str = None) -> Device:
    try:
        client.version()
    except Exception:
        raise Exception(
            "adb 서버에 접속을 하지 못했습니다. adb devices 후 재시도 해주세요."
        )

    if serial:
        device = client.device(serial)
        if not device:
            raise Exception(f"{serial}이(가) 연결되어 있지 않습니다.")
    else:
        devices = client.devices()

        if not devices:
            raise Exception("연결된 장치가 없습니다.")

        if len(devices) == 1:
            device = devices[0]
        elif len(devices) > 1:
            raise Exception(
                "연결된 장치가 1개 이상입니다 --serial 옵션을 사용해주세요."
            )
        else:
            raise Exception("알 수 없는 오류가 발생했습니다.")

    return device


def _iris_start(device: Device):
    for _ in range(5):
        pid = get_iris_pid(device)
        if pid is not None:
            logger.success("실행 완료")
            return

        device.shell(
            f'su -c "nohup env CLASSPATH={IRIS_INSTALL_PATH} /system/bin/app_process  / --nice-name={IRIS_PROCESS_NAME} {IRIS_PACKAGE_NAME} > {IRIS_LOG_PATH} 2>&1 &"'
        )
        time.sleep(1)
    else:
        logger.error("오류")


def get_iris_pid(device: Device):
    resp: str = device.shell("pidof Iris.app_process")
    resp = resp.strip()

    if resp:
        return int(resp)
    else:
        return None


def iris_dex_install(device: Device, start=False):
    res = None
    try:
        res = requests.get(
            "https://api.github.com/repos/dolidolih/Iris/releases/latest"
        )
        res.raise_for_status()
    except Exception as e:
        logger.error(
            e,
            res.text if res is not None else None,
            "릴리즈 정보를 가져오는데 오류가 발생했습니다",
        )
        return

    data = res.json()
    iris_asset = next(
        (asset for asset in data["assets"] if asset["name"] == "Iris.dex"), None
    )

    if not iris_asset:
        logger.error("Iris.dex를 릴리즈에서 찾을 수 없습니다")
        return

    with tempfile.NamedTemporaryFile() as tmp:
        logger.info("Iris.dex를 다운로드하고 있습니다")
        iris_res = requests.get(
            iris_asset["browser_download_url"], allow_redirects=True
        )

        tmp.write(iris_res.content)
        tmp.flush()

        kill_iris(device)

        device.push(tmp.name, IRIS_INSTALL_PATH)
        device.shell(f"fsync {IRIS_INSTALL_PATH}")

    logger.success("설치 완료!")

    if start:
        _iris_start(device)


def iris_install_ask(device: Device):
    def select_bot_name():
        while True:
            name = typer.prompt("봇 이름을 정해주세요")
            confirm = typer.confirm("진행 하시겠습니까")

            if confirm:
                return name

    def select_iris_port():
        while True:
            port = typer.prompt("Iris가 열릴 포트를 정해주세요", type=int, default=3000)
            confirm = typer.confirm("진행 하시겠습니까")

            if confirm:
                return port

    def select_web_server_host():
        DOCKER_HOSTS = ["host.docker.internal", "172.17.0.1"]

        for host in DOCKER_HOSTS:
            if device_ping(device, host):
                return host

        while True:
            host = typer.prompt(
                "모바일 기기에서 IrisPy에 접근할 수 있는 호스트를 써주세요 (eg. 현재 컴퓨터의 IP)"
            )

            if device_ping(device, host):
                return host

            confirm = typer.confirm(
                "모바일에서 해당 호스트에 ping을 보내지 못했습니다. 진행 하시겠습니까"
            )

            if confirm:
                return host

    def select_web_server_port():
        while True:
            port = typer.prompt("IrisPy가 열릴 포트를 써주세요")

            confirm = typer.confirm("진행 하시겠습니까")
            if confirm:
                return port

    bot_name = select_bot_name()
    iris_port = select_iris_port()

    web_endpoint = select_web_server_host()
    web_port = select_web_server_port()

    return {
        "bot_name": bot_name,
        "iris_port": iris_port,
        "web_endpoint": web_endpoint,
        "web_port": web_port,
    }


@app.command(short_help="Iris.dex 설치와 설정을 진행합니다")
def install(serial: str = None):
    try:
        device = get_device(serial)
        logger.info(f"현재 장치: {device.serial}")
    except Exception as e:
        logger.error(str(e))
        return

    config = iris_install_ask(device)
    config_json = {
        "bot_name": config["bot_name"],
        "bot_http_port": config["iris_port"],
        "web_server_endpoint": f"http://{config['web_endpoint']}:{config['web_port']}/iris",
    }

    print()
    print("config.json")
    print(json.dumps(config_json, ensure_ascii=False))
    print()

    with tempfile.NamedTemporaryFile(mode="w") as tmp:
        tmp.write(json.dumps(config_json))
        tmp.flush()

        device.push(tmp.name, IRIS_CONFIG_PATH)

    iris_dex_install(device, start=True)
    print()

    print("snippets")
    for ip in get_device_ip_list(device):
        if ping(ip):
            print(
                f"""
                bot.run(port={config["web_port"]}, iris_endpoint="http://{ip}:{config["iris_port"]}")
                """.strip()
            )
            print()


@app.command(short_help="Iris.dex만 설치합니다")
def update(serial: str = None):
    try:
        device = get_device(serial)
        logger.info(f"현재 장치: {device.serial}")
    except Exception as e:
        logger.error(str(e))
        return

    iris_dex_install(device)


@app.command(short_help="iris를 실행합니다")
def start(serial: str = None):
    try:
        device = get_device(serial)
        logger.info(f"현재 장치: {device.serial}")
    except Exception as e:
        logger.error(str(e))
        return

    pid = get_iris_pid(device)
    if pid is not None:
        logger.error(f"이미 Iris가 실행 중입니다 ({pid})")
        return

    _iris_start(device)


@app.command(short_help="iris를 정지합니다")
def stop(serial: str = None):
    try:
        device = get_device(serial)
        logger.info(f"현재 장치: {device.serial}")
    except Exception as e:
        logger.error(str(e))
        return

    if kill_iris(device):
        logger.info("종료되었습니다")


@app.command(short_help="iris의 상태를 확인합니다")
def status(serial: str = None):
    try:
        device = get_device(serial)
        logger.info(f"현재 장치: {device.serial}")
    except Exception as e:
        logger.error(str(e))
        return

    resp: str = device.shell("pidof Iris.app_process")
    resp = resp.strip()

    if resp:
        logger.info(f"Running (PID: {resp})")
    else:
        logger.info("Stopped")

    config = device.shell(f"cat {IRIS_CONFIG_PATH}")

    try:
        logger.info("config")
        print(json.dumps(json.loads(config), indent=4, ensure_ascii=False))
    except Exception:
        logger.error("config.json 파싱 오류")
        print(config)


@app.command(short_help="iris의 URL로 접속을 시도합니다")
def check(iris_endpoint: str):
    try:
        res = requests.get(f"{iris_endpoint}/config/info")
        res.raise_for_status()

        logger.success("성공")
    except Exception as e:
        logger.error(f"실패: {e}")


@app.command(short_help="iris 로그를 추출합니다")
def log(
    serial: str = None,
    export: Annotated[bool, typer.Option("--export", "-e")] = False,
):
    try:
        device = get_device(serial)
        logger.info(f"현재 장치: {device.serial}")
    except Exception as e:
        logger.error(str(e))
        return

    if export:
        path = os.path.join(os.getcwd(), "iris.log")

        device.pull(IRIS_LOG_PATH, path)
        logger.success(f"{path} 에 로그가 추출되었습니다")
        return
    else:
        print(device.shell(f"tail {IRIS_LOG_PATH}").strip())


@app.command(short_help="연결된 기기의 IP를 확인합니다")
def ip(serial: str = None):
    try:
        device = get_device(serial)
        logger.info(f"현재 장치: {device.serial}")
    except Exception as e:
        logger.error(str(e))
        return

    for ip in get_device_ip_list(device):
        print(ip)


if __name__ == "__main__":
    app()
