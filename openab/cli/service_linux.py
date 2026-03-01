"""Linux 用户级 systemd 服务安装（仅限 Linux）。"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"
SERVICE_NAME = "openab.service"
SERVICE_DISCORD_NAME = "openab-discord.service"


def _is_linux() -> bool:
    return sys.platform == "linux"


def _find_openab_executable() -> tuple[str, list[str]]:
    """返回 (executable, args)，用于 ExecStart。"""
    exe = shutil.which("openab")
    if exe:
        return (exe, [])
    return (sys.executable, ["-m", "openab"])


def _escape_exec_start_arg(s: str) -> str:
    """systemd ExecStart 参数中空格需反斜杠转义。"""
    return s.replace("\\", "\\\\").replace(" ", "\\ ")


def _write_unit_file(path: Path, exec_start: list[str], description: str) -> None:
    """写入 systemd unit 文件。exec_start 为 [exe, arg1, arg2, ...]。"""
    # ExecStart 格式：参数内空格用 \ 转义（Linux/Mac 路径兼容）
    start_line = " ".join(_escape_exec_start_arg(a) for a in exec_start)
    content = f"""[Unit]
Description={description}
After=network-online.target

[Service]
Type=simple
ExecStart={start_line}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""
    path.write_text(content, encoding="utf-8")


def install_user_service(
    *,
    discord: bool = False,
    start: bool = False,
) -> str:
    """
    安装用户级 systemd 服务（仅 Linux）。
    默认安装的 openab.service 使用「openab run」，启动目标仅从配置文件 service.run 解析；
    --discord 时安装 openab-discord.service，固定运行 Discord 机器人（可与主服务并存）。
    返回创建的单位文件路径；失败时抛出 RuntimeError。
    """
    if not _is_linux():
        raise RuntimeError("install-service is only supported on Linux")

    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    exe, args = _find_openab_executable()
    exec_list = [exe] + args
    if discord:
        exec_list = exec_list + ["run", "discord"]
        name = SERVICE_DISCORD_NAME
        description = "OpenAB Discord bot"
    else:
        # 通过配置启动：openab run 会根据 config 的 service.run 或 token 自动选择 serve/telegram/discord
        exec_list = exec_list + ["run"]
        name = SERVICE_NAME
        description = "OpenAB (config-driven: serve / telegram / discord)"
    unit_path = SYSTEMD_USER_DIR / name
    _write_unit_file(unit_path, exec_list, description)

    subprocess.run(
        ["systemctl", "--user", "daemon-reload"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["systemctl", "--user", "enable", name],
        check=True,
        capture_output=True,
    )
    if start:
        subprocess.run(
            ["systemctl", "--user", "start", name],
            check=True,
            capture_output=True,
        )
    return str(unit_path)


def uninstall_user_services(*, discord: bool = False, all_services: bool = False) -> list[str]:
    """
    卸载用户级 systemd 服务（仅 Linux）。
    discord=False 且 all_services=False：只卸载 openab.service；
    discord=True：只卸载 openab-discord.service；
    all_services=True：卸载 openab.service 与 openab-discord.service。
    先 stop、disable，再删除 unit 文件，最后 daemon-reload。
    返回已删除的 unit 文件路径列表；若本来就不存在则跳过，不抛错。
    """
    if not _is_linux():
        raise RuntimeError("uninstall-service is only supported on Linux")

    removed: list[str] = []
    if all_services:
        names = [SERVICE_NAME, SERVICE_DISCORD_NAME]
    else:
        names = [SERVICE_DISCORD_NAME] if discord else [SERVICE_NAME]
    for name in names:
        unit_path = SYSTEMD_USER_DIR / name
        if not unit_path.is_file():
            continue
        subprocess.run(
            ["systemctl", "--user", "stop", name],
            capture_output=True,
        )
        subprocess.run(
            ["systemctl", "--user", "disable", name],
            capture_output=True,
        )
        unit_path.unlink()
        removed.append(str(unit_path))
    if removed:
        subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            check=True,
            capture_output=True,
        )
    return removed
