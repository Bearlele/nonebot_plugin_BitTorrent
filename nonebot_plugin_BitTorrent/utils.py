import re
import base64
import urllib.parse
from typing import List

from bs4 import BeautifulSoup
from httpx import AsyncClient
from nonebot import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.internal.adapter import Bot, Event, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from .config import config

class BitTorrent:
    BASE_URL = "http://clm10.xyz"

    async def main(
        self,
        bot: Bot,
        matcher: Matcher,
        event: Event,
        msg: Message = CommandArg(),
    ) -> None:
        """主函数, 用于响应命令"""

        logger.info("开始搜索")
        keyword: str = msg.extract_plain_text()
        if not keyword:
            await matcher.finish("虚空搜索?来点车牌gkd")
        try:
            await bot.call_api("set_msg_emoji_like", message_id=event.message_id, emoji_id="314") # 思考表情
            data = await self.get_items(keyword)
        except Exception as e:
            await matcher.finish("搜索失败, 下面是错误信息:\n" + repr(e))
        if not data:
            await matcher.finish("没有找到结果捏, 换个关键词试试吧")
        
        tasks = await self.get_magnet(data) 

        if config.onebot_group_forward_msg and isinstance(event, GroupMessageEvent):
            messages = [
                {
                    "type": "node",
                    "data": {
                        "name": "然然",
                        "uin": bot.self_id,
                        "content": i,
                    },
                }
                for i in tasks
            ]
            await bot.call_api("set_msg_emoji_like", message_id=event.message_id, emoji_id="314", set="false")
            try:
                await bot.send_group_forward_msg(group_id=event.group_id, message=messages)
            except ActionFailed:
                await matcher.finish("消息发送失败，账号可能被风控")
        else:
            await matcher.finish("\n".join(tasks))

    async def get_items(self, keyword) -> List[str]:
        # Base64编码
        b64_keyword = base64.b64encode(keyword.encode()).decode().rstrip("=")
        search_url = f"{self.BASE_URL}/search?word={b64_keyword}"
        
        async with AsyncClient() as client:
            resp = await client.get(search_url)
        
        # 提取base64加密串
        m = re.search(r'atob\("([^"]+)"\)', resp.text)
        if not m:
            logger.info("未找到加密内容")
            return []
        encrypted_str = m.group(1)

        # 解密
        decoded = base64.b64decode(encrypted_str)
        html = urllib.parse.unquote(decoded.decode())

        # 用解密后的html解析
        soup = BeautifulSoup(html, "lxml")
        ul = soup.find("ul", id="Search_list_wrapper")
        if not ul:
            return []
        
        li_list = ul.find_all("li", limit=config.magnet_max_num)
        hrefs = []
        for li in li_list:
            a_tag = li.find("a", class_="SearchListTitle_result_title")
            if a_tag and a_tag.get("href"):
                hrefs.append(self.BASE_URL + a_tag.get("href"))
        
        return hrefs

    async def get_magnet(self, search_urls: str) -> str:
        result = []
    
        for detail_url in search_urls:
            async with AsyncClient() as client:
                resp = await client.get(detail_url)
            
            # 提取base64加密串
            m = re.search(r'atob\("([^"]+)"\)', resp.text)
            if not m:
                logger.info(f"未找到加密内容: {detail_url}")
                result.append(f"未找到加密内容: {detail_url}")
                continue

            encrypted_str = m.group(1)

            # 解密
            decoded = base64.b64decode(encrypted_str)
            html = urllib.parse.unquote(decoded.decode())

            # 用解密后的html解析
            soup = BeautifulSoup(html, "lxml")

            # 提取标题
            title_tag = soup.find("h1", class_="Information_title")
            title = title_tag.get_text() if title_tag else "未找到标题"
            
            # 提取磁力链接
            magnet_input = soup.find("input", id="Information_copy_text")
            magnet_link = magnet_input.get("value") if magnet_input else "未找到磁力链接"
            
            # 提取文件信息
            info_block = soup.find("div", class_="Information_info_wrapper")
            if info_block:
                text = info_block.get_text()
                file_count = "未知"
                file_size = "未知"
                if "文件数目：" in text:
                    file_count = text.split("文件数目：")[1].split("个文件")[0].strip()
                if "文件大小：" in text:
                    file_size = text.split("文件大小：")[1].split("收录时间")[0].strip()
            else:
                file_count = "未知"
                file_size = "未知"
            
            result.append(f"标题: {title}\n磁力链接: {magnet_link}\n文件数目: {file_count}个文件\n文件大小: {file_size}")
        
        return result


# 实例化
bittorrent = BitTorrent()
