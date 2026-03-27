"""
测试 Suno 音乐生成功能
"""
import sys
import os
import logging
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_loader import config_loader
from src.generators.music_generator import SunoMusicGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def test_music_generation():
    """测试音乐生成功能"""
    logger.info("=" * 70)
    logger.info("测试 Suno 音乐生成功能")
    logger.info("=" * 70)

    try:
        # 加载配置
        suno_config = config_loader.get_suno_config()

        api_type = suno_config.get("api_type", "unofficial")
        logger.info(f"API 类型: {api_type}")

        # 初始化音乐生成器
        if api_type == "official":
            music_generator = SunoMusicGenerator(
                api_type="official",
                api_key=suno_config.get("api_key")
            )
        else:
            music_generator = SunoMusicGenerator(
                api_type="unofficial",
                api_id=suno_config.get("api_id"),
                token=suno_config.get("token")
            )

        # 生成音乐
        logger.info("\n开始生成音乐...")
        logger.info("这可能需要 2-3 分钟，请耐心等待...")

        music_prompt = "一首轻松愉快的电子音乐，适合作为 AI 科技文章的背景音乐，节奏明快，氛围积极向上"
        music_style = "electronic pop"
        music_title = "AI Technology"

        start_time = time.time()

        music_results = music_generator.generate_music(
            prompt=music_prompt,
            style=music_style,
            title=music_title,
            instrumental=True  # 纯音乐
        )

        elapsed_time = time.time() - start_time

        logger.info(f"\n{'=' * 70}")
        logger.info(f"音乐生成完成！耗时: {elapsed_time:.1f} 秒")
        logger.info(f"{'=' * 70}")

        if not music_results or len(music_results) == 0:
            logger.error("音乐生成失败")
            return False

        # 显示结果
        logger.info(f"\n成功生成 {len(music_results)} 首音乐：")

        for i, music in enumerate(music_results, 1):
            logger.info(f"\n音乐 {i}:")
            logger.info(f"  ID: {music.get('id')}")
            logger.info(f"  标题: {music.get('title')}")
            logger.info(f"  风格: {music.get('style')}")
            logger.info(f"  时长: {music.get('duration')} 秒")
            logger.info(f"  在线地址: {music.get('audio_url')}")
            logger.info(f"  本地路径: {music.get('local_path')}")

            # 检查文件是否存在
            local_path = music.get('local_path')
            if local_path and os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                logger.info(f"  文件大小: {file_size / 1024:.1f} KB")
                logger.info(f"  ✅ 文件验证成功")
            else:
                logger.warning(f"  ⚠️ 文件不存在或无法访问")

        logger.info(f"\n{'=' * 70}")
        logger.info("✅ 音乐生成测试成功！")
        logger.info(f"{'=' * 70}")

        return True

    except Exception as e:
        logger.error(f"\n{'=' * 70}")
        logger.error("❌ 音乐生成测试失败")
        logger.error(f"{'=' * 70}")
        logger.error(f"错误信息: {e}")
        logger.error("错误详情:", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("Suno 音乐生成器 - 独立测试")
    logger.info("开始时间: " + time.strftime("%Y-%m-%d %H:%M:%S"))

    success = test_music_generation()

    logger.info("\n结束时间: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 70)

    if success:
        logger.info("✅ 所有测试通过！")
        sys.exit(0)
    else:
        logger.error("❌ 测试失败，请查看日志了解详情")
        sys.exit(1)
