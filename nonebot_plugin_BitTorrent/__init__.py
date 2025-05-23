import contextlib

from nonebot import on_command

from .utils import bittorrent

# 声明一个响应器, 优先级10, 向下阻断
on_command(
    "磁力搜索", aliases={"bt"}, priority=10, block=True, handlers=[bittorrent.main]
)


with contextlib.suppress(Exception):
    from nonebot.plugin import PluginMetadata

    __plugin_meta__ = PluginMetadata(
        name="bittorrent",
        description="磁力搜索插件",
        usage="磁力搜索 xxx",
        type="application",
        homepage="https://github.com/Bearlele/nonebot_plugin_BitTorrent",
        supported_adapters=None,
        extra={
            "author": "Special-Week & Bear_lele",
            "version": "0.0.22",
            "priority": 10,
        },
    )
