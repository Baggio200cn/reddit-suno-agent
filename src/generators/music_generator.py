"""
Suno 音乐生成器（增强版）
支持 Suno 官方 API 和非官方 API 两种方式
"""
import requests
import time
import os
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SunoMusicGenerator:
    """
    Suno 音乐生成器（增强版）

    支持两种 API 方式：
    1. 官方 API (https://api.sunoapi.org) - 需要 API Key
    2. 非官方 API (https://suno.x-mi.cn) - 需要 x-apiid 和 x-token
    """

    def __init__(self, api_type: str = "official", **kwargs):
        """
        初始化音乐生成器

        Args:
            api_type: API 类型，"official" 或 "unofficial"
            **kwargs: API 凭证
                - 官方 API 需要: api_key
                - 非官方 API 需要: api_id, token
        """
        self.api_type = api_type

        if api_type == "official":
            # 官方 API
            self.api_key = kwargs.get("api_key")
            self.base_url = "https://api.sunoapi.org/api/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            logger.info("使用 Suno 官方 API")
        elif api_type == "unofficial":
            # 非官方 API
            self.api_id = kwargs.get("api_id")
            self.token = kwargs.get("token")
            self.base_url = "https://suno.x-mi.cn/apiclouds/v1/suno"
            self.headers = {
                "Content-Type": "application/json",
                "x-apiid": self.api_id,
                "x-token": self.token
            }
            logger.info("使用 Suno 非官方 API")
        else:
            raise ValueError(f"不支持的 API 类型: {api_type}")

    def generate_music(
        self,
        prompt: str,
        style: Optional[str] = None,
        title: Optional[str] = None,
        instrumental: bool = False,
        model: str = "V4_5",
        output_dir: str = "output/music"
    ) -> Optional[List[Dict]]:
        """
        生成音乐

        Args:
            prompt: 音乐描述（歌词或灵感）
            style: 音乐风格（自定义模式）
            title: 歌曲标题（自定义模式）
            instrumental: 是否纯音乐
            model: 模型版本 (V4, V4_5, V4_5PLUS, V4_5ALL, V5)
            output_dir: 输出目录

        Returns:
            生成成功的音乐信息列表，包含本地路径，失败返回 None
            [{
                "id": "audio_id",
                "title": "歌曲标题",
                "audio_url": "音频URL",
                "local_path": "本地文件路径",
                "duration": 180.5,
                "style": "风格"
            }]
        """
        try:
            logger.info(f"开始生成音乐: {prompt[:50]}...")

            if self.api_type == "official":
                return self._generate_with_official_api(
                    prompt, style, title, instrumental, model, output_dir
                )
            else:
                return self._generate_with_unofficial_api(
                    prompt, style, instrumental, output_dir
                )

        except Exception as e:
            logger.error(f"生成音乐失败: {e}")
            return None

    def _generate_with_official_api(
        self,
        prompt: str,
        style: Optional[str],
        title: Optional[str],
        instrumental: bool,
        model: str,
        output_dir: str
    ) -> Optional[List[Dict]]:
        """使用官方 API 生成音乐"""
        try:
            # 1. 创建生成任务
            url = f"{self.base_url}/generate"

            payload = {
                "prompt": prompt,
                "instrumental": instrumental,
                "model": model
            }

            # 如果提供了 style 和 title，启用自定义模式
            if style or title:
                payload["customMode"] = True
                if style:
                    payload["style"] = style
                if title:
                    payload["title"] = title

            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get("code") != 200:
                logger.error(f"创建任务失败: {result.get('msg')}")
                return None

            task_id = result.get("data", {}).get("taskId")
            if not task_id:
                logger.error("未获取到任务 ID")
                return None

            logger.info(f"官方 API 任务创建成功: {task_id}")

            # 2. 等待任务完成
            task_result = self._wait_for_official_task(task_id, max_wait_time=600)
            if not task_result or task_result.get("status") != "SUCCESS":
                logger.error("音乐生成失败")
                return None

            # 3. 下载音频文件
            audio_list = task_result.get("response", {}).get("data", [])
            if not audio_list:
                logger.error("未获取到音频列表")
                return None

            results = []
            for audio in audio_list:
                audio_url = audio.get("audio_url")
                if not audio_url:
                    continue

                # 下载音频
                local_path = self._download_audio(audio_url, output_dir)
                if local_path:
                    results.append({
                        "id": audio.get("id"),
                        "title": audio.get("title", "未知"),
                        "audio_url": audio_url,
                        "local_path": local_path,
                        "duration": audio.get("duration", 0),
                        "style": audio.get("tags", "")
                    })

            logger.info(f"成功生成 {len(results)} 首音乐")
            return results

        except Exception as e:
            logger.error(f"官方 API 生成失败: {e}")
            return None

    def _generate_with_unofficial_api(
        self,
        prompt: str,
        style: str,
        instrumental: bool,
        output_dir: str
    ) -> Optional[List[Dict]]:
        """使用非官方 API 生成音乐"""
        try:
            # 1. 创建生成任务
            url = f"{self.base_url}/generate"
            payload = {
                "action": "generate",
                "inputType": "10",  # 灵感模式
                "mvVersion": "chirp-v4",  # 模型版本
                "makeInstrumental": 1 if instrumental else 0,
                "idea": prompt
            }

            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get("code") != 0:
                logger.error(f"创建任务失败: {result.get('msg')}")
                return None

            task_id = result.get("data", {}).get("id")
            if not task_id:
                logger.error("未获取到任务 ID")
                return None

            logger.info(f"非官方 API 任务创建成功: {task_id}")

            # 2. 等待任务完成
            task_result = self._wait_for_unofficial_task(task_id, max_wait_time=300)
            if not task_result or task_result.get("status") != 30:  # 30 = 成功
                logger.error("音乐生成失败")
                return None

            # 3. 下载音频文件
            audio_list = task_result.get("list", [])
            if not audio_list:
                logger.error("未获取到音频列表")
                return None

            results = []
            for audio in audio_list:
                audio_url = audio.get("audioUrl")
                if not audio_url:
                    continue

                # 下载音频
                local_path = self._download_audio(audio_url, output_dir)
                if local_path:
                    results.append({
                        "id": audio.get("clipId"),
                        "title": audio.get("title", "未知"),
                        "audio_url": audio_url,
                        "local_path": local_path,
                        "duration": float(audio.get("clipDuration", 0)),
                        "style": audio.get("style", ""),
                        "lyric": audio.get("lyric", "")
                    })

            logger.info(f"成功生成 {len(results)} 首音乐")
            return results

        except Exception as e:
            logger.error(f"非官方 API 生成失败: {e}")
            return None

    def _wait_for_official_task(
        self,
        task_id: str,
        max_wait_time: int = 600
    ) -> Optional[Dict]:
        """等待官方 API 任务完成"""
        url = f"{self.base_url}/generate/record-info"

        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(
                    url,
                    params={"taskId": task_id},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30
                )
                response.raise_for_status()

                result = response.json()
                if result.get("code") == 200:
                    data = result.get("data", {})
                    status = data.get("status")

                    if status == "SUCCESS":
                        logger.info("音乐生成成功")
                        return data
                    elif status == "FAILED":
                        logger.error(f"音乐生成失败: {data.get('errorMessage')}")
                        return None
                    else:
                        # 继续等待
                        logger.info(f"音乐生成中... 状态: {status}")
                        time.sleep(15)  # 官方 API 每 15 秒查询一次
                else:
                    logger.error(f"查询任务状态失败: {result.get('msg')}")
                    time.sleep(10)

            except Exception as e:
                logger.error(f"查询任务状态异常: {e}")
                time.sleep(10)

        logger.error("音乐生成超时")
        return None

    def _wait_for_unofficial_task(
        self,
        task_id: str,
        max_wait_time: int = 300
    ) -> Optional[Dict]:
        """等待非官方 API 任务完成"""
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
                        logger.info("音乐生成成功")
                        return data
                    elif status == 40:
                        logger.error(f"音乐生成失败: {data.get('errMsg')}")
                        return None
                    else:
                        # 继续等待
                        logger.info(f"音乐生成中... 状态: {status}")
                        time.sleep(10)
                else:
                    logger.error(f"查询任务状态失败: {result.get('msg')}")
                    time.sleep(5)

            except Exception as e:
                logger.error(f"查询任务状态异常: {e}")
                time.sleep(5)

        logger.error("音乐生成超时")
        return None

    def _download_audio(self, url: str, output_dir: str) -> Optional[str]:
        """
        下载音频文件

        Args:
            url: 音频文件 URL
            output_dir: 输出目录

        Returns:
            本地文件路径，失败返回 None
        """
        try:
            # 创建输出目录
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

            logger.info(f"音乐下载成功: {local_path}")
            return local_path

        except Exception as e:
            logger.error(f"下载音乐失败: {e}")
            return None

    def generate_lyrics(self, prompt: str, output_file: Optional[str] = None) -> Optional[str]:
        """
        生成歌词（仅官方 API 支持）

        Args:
            prompt: 歌词提示
            output_file: 输出文件路径（可选）

        Returns:
            生成的歌词文本，失败返回 None
        """
        if self.api_type != "official":
            logger.warning("非官方 API 不支持歌词生成")
            return None

        try:
            url = f"{self.base_url}/lyrics"
            payload = {
                "prompt": prompt,
                "callBackUrl": ""
            }

            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if result.get("code") != 200:
                logger.error(f"创建歌词任务失败: {result.get('msg')}")
                return None

            task_id = result.get("data", {}).get("taskId")
            logger.info(f"歌词任务创建成功: {task_id}")

            # 等待歌词生成完成
            task_result = self._wait_for_official_task(task_id, max_wait_time=300)
            if not task_result or task_result.get("status") != "SUCCESS":
                logger.error("歌词生成失败")
                return None

            lyrics_list = task_result.get("response", {}).get("data", [])
            if not lyrics_list:
                logger.error("未获取到歌词")
                return None

            lyrics_text = lyrics_list[0].get("text", "")

            # 如果指定了输出文件，保存歌词
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(lyrics_text)
                logger.info(f"歌词已保存到: {output_file}")

            return lyrics_text

        except Exception as e:
            logger.error(f"生成歌词失败: {e}")
            return None

    def get_remaining_credits(self) -> Optional[int]:
        """
        获取剩余积分（仅官方 API 支持）

        Returns:
            剩余积分数，失败返回 None
        """
        if self.api_type != "official":
            logger.warning("非官方 API 不支持查询积分")
            return None

        try:
            url = f"{self.base_url}/get-credits"
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            if result.get("code") == 200:
                credits = result.get("data", {}).get("credits", 0)
                logger.info(f"剩余积分: {credits}")
                return credits
            else:
                logger.error(f"查询积分失败: {result.get('msg')}")
                return None

        except Exception as e:
            logger.error(f"查询积分异常: {e}")
            return None


if __name__ == "__main__":
    # 测试官方 API
    print("=== 测试官方 API ===")
    official_api = SunoMusicGenerator(
        api_type="official",
        api_key="your_official_api_key"
    )

    # 测试非官方 API
    print("\n=== 测试非官方 API ===")
    unofficial_api = SunoMusicGenerator(
        api_type="unofficial",
        api_id="your_api_id",
        token="your_token"
    )

    # 测试生成音乐
    print("\n=== 测试生成音乐 ===")
    results = unofficial_api.generate_music(
        prompt="一首轻松愉快的电子音乐，适合作为播客背景音乐",
        style="electronic"
    )

    if results:
        for i, track in enumerate(results, 1):
            print(f"\n音轨 {i}:")
            print(f"  标题: {track['title']}")
            print(f"  时长: {track['duration']}秒")
            print(f"  本地路径: {track['local_path']}")
            print(f"  风格: {track['style']}")
