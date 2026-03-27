"""
配置加载器
"""
import json
import os
from typing import Dict, Any


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_dir: str = "config"):
        """
        初始化配置加载器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        self._credentials = None
        self._schedule = None

    def load_credentials(self) -> Dict[str, Any]:
        """
        加载凭证配置

        Returns:
            凭证配置字典
        """
        if self._credentials is None:
            config_path = os.path.join(self.config_dir, "credentials.json")
            if not os.path.exists(config_path):
                raise FileNotFoundError(
                    f"配置文件不存在: {config_path}\n"
                    f"请从 {config_path}.example 复制并填写配置信息"
                )

            with open(config_path, 'r', encoding='utf-8') as f:
                self._credentials = json.load(f)

            # 验证必需字段（Reddit 现在使用 RSS Feed，无需配置）
            required_sections = ["suno", "doubao", "email", "github"]
            for section in required_sections:
                if section not in self._credentials:
                    raise ValueError(f"配置文件缺少必需的 section: {section}")

            # 检查是否有 reddit 配置（为了兼容，不强制要求）
            if "reddit" not in self._credentials:
                self._credentials["reddit"] = {}  # 提供空配置

        return self._credentials

    def load_schedule(self) -> Dict[str, Any]:
        """
        加载定时任务配置

        Returns:
            定时任务配置字典
        """
        if self._schedule is None:
            config_path = os.path.join(self.config_dir, "schedule.json")
            if not os.path.exists(config_path):
                # 使用默认配置
                self._schedule = {
                    "enabled": True,
                    "cron": {
                        "hour": 0,
                        "minute": 0
                    },
                    "timezone": "Asia/Shanghai"
                }
            else:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._schedule = json.load(f)

        return self._schedule

    def get_reddit_config(self) -> Dict[str, str]:
        """
        获取 Reddit 配置（现在使用 RSS Feed，无需凭证）

        Returns:
            空字典（保留接口以兼容）
        """
        return self.load_credentials().get("reddit", {})

    def get_suno_config(self) -> Dict[str, str]:
        """获取 Suno 配置"""
        return self.load_credentials()["suno"]

    def get_doubao_config(self) -> Dict[str, str]:
        """获取豆包配置"""
        return self.load_credentials()["doubao"]

    def get_email_config(self) -> Dict[str, str]:
        """获取邮件配置"""
        return self.load_credentials()["email"]

    def get_github_config(self) -> Dict[str, str]:
        """获取 GitHub 配置"""
        return self.load_credentials()["github"]


# 全局配置加载器实例
config_loader = ConfigLoader()
