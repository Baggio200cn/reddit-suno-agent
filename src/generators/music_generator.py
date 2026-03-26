"""
Suno 音乐生成器
"""
import requests
import time
import os
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MusicGenerator:
    """Suno 音乐生成器"""

    def __init__(self, api_id: str, token: str):
        """
        初始化音乐生成器

        Args:
            api_id: Suno API ID
            token: Suno Token
        """
        self.api_id = api_id
        self.token = token
        self.base_url = "https://suno.x-mi.cn/apiclouds/v1/suno"
        self.headers = {
            "Content-Type": "application/json",
            "x-apiid": api_id,
            "x-token": token
        }

    def generate_music(self, idea: str, style: str = "electronic", make_instrumental: int = 0) -> Optional[str]:
        """
        生成音乐

        Args:
            idea: 音乐灵感描述
            style: 音乐风格
            make_instrumental: 是否纯音乐（1是，0否）

        Returns:
            生成的音乐文件路径，失败返回 None
        """
        try:
            logger.info(f"开始生成音乐: {idea}")

            # 1. 创建生成任务
            task_id = self._create_task(idea, style, make_instrumental)
            if not task_id:
                logger.error("创建音乐生成任务失败")
                return None

            logger.info(f"音乐生成任务创建成功，任务ID: {task_id}")

            # 2. 轮询任务状态
            music_url = self._wait_for_completion(task_id, max_wait_time=300)
            if not music_url:
                logger.error("音乐生成超时或失败")
                return None

            logger.info(f"音乐生成成功: {music_url}")

            # 3. 下载音乐文件
            local_path = self._download_music(music_url)
            if local_path:
                logger.info(f"音乐下载成功: {local_path}")
                return local_path
            else:
                logger.error("音乐下载失败")
                return None

        except Exception as e:
            logger.error(f"生成音乐失败: {e}")
            return None

    def _create_task(self, idea: str, style: str, make_instrumental: int) -> Optional[str]:
        """
        创建音乐生成任务

        Args:
            idea: 音乐灵感
            style: 音乐风格
            make_instrumental: 是否纯音乐

        Returns:
            任务 ID，失败返回 None
        """
        url = f"{self.base_url}/generate"
        payload = {
            "action": "generate",
            "inputType": "10",
            "mvVersion": "chirp-v4",  # 使用 v4 模型
            "makeInstrumental": make_instrumental,
            "idea": idea
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get("code") == 0:
                return result.get("data", {}).get("id")
            else:
                logger.error(f"创建任务失败: {result.get('msg')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"创建任务请求失败: {e}")
            return None

    def _wait_for_completion(self, task_id: str, max_wait_time: int = 300) -> Optional[str]:
        """
        等待音乐生成完成

        Args:
            task_id: 任务 ID
            max_wait_time: 最大等待时间（秒）

        Returns:
            音乐文件 URL，失败返回 None
        """
        url = f"{self.base_url}/query"
        payload = {"id": task_id}

        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.post(url, headers=self.headers, json=payload, timeout=30)
                response.raise_for_status()

                result = response.json()
                if result.get("code") == 0:
                    data = result.get("data", {})
                    status = data.get("status")

                    # 10=排队，20=执行中，30=成功，40=失败
                    if status == 30:
                        # 生成成功，获取音乐 URL
                        music_list = data.get("list", [])
                        if music_list and len(music_list) > 0:
                            return music_list[0].get("audioUrl")
                    elif status == 40:
                        logger.error(f"音乐生成失败: {data.get('errMsg')}")
                        return None
                    else:
                        # 继续等待
                        logger.info(f"音乐生成中... 状态: {status}")
                        time.sleep(10)
                else:
                    logger.error(f"查询任务状态失败: {result.get('msg')}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"查询任务状态请求失败: {e}")
                time.sleep(5)

        logger.error("音乐生成超时")
        return None

    def _download_music(self, url: str) -> Optional[str]:
        """
        下载音乐文件

        Args:
            url: 音乐文件 URL

        Returns:
            本地文件路径，失败返回 None
        """
        try:
            # 创建输出目录
            output_dir = "output/music"
            os.makedirs(output_dir, exist_ok=True)

            # 生成文件名
            filename = f"music_{int(time.time())}.mp3"
            local_path = os.path.join(output_dir, filename)

            # 下载文件
            logger.info(f"开始下载音乐: {url}")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            # 写入文件
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return local_path

        except Exception as e:
            logger.error(f"下载音乐失败: {e}")
            return None


if __name__ == "__main__":
    # 测试代码
    config = {
        "api_id": "your_api_id",
        "token": "your_token"
    }

    generator = MusicGenerator(config["api_id"], config["token"])

    # 测试生成音乐
    music_path = generator.generate_music(
        idea="一首轻松愉快的电子音乐，适合作为播客背景音乐",
        style="electronic"
    )

    if music_path:
        print(f"音乐生成成功: {music_path}")
    else:
        print("音乐生成失败")
