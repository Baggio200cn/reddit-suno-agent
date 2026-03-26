"""
GitHub 发布器（自动推送代码）
"""
import os
from typing import Dict, Optional
from git import Repo, Actor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubPublisher:
    """GitHub 发布器"""

    def __init__(self, config: Dict[str, str], project_dir: str = "."):
        """
        初始化 GitHub 发布器

        Args:
            config: GitHub 配置字典，包含 token, repo
            project_dir: 项目目录
        """
        self.token = config["token"]
        self.repo = config["repo"]
        self.project_dir = project_dir

        # 构建 GitHub URL
        self.github_url = f"https://{self.token}@github.com/{self.repo}.git"

    def push_to_github(self, commit_message: str, branch: str = "main") -> bool:
        """
        推送代码到 GitHub

        Args:
            commit_message: 提交信息
            branch: 分支名称

        Returns:
            推送成功返回 True，失败返回 False
        """
        try:
            logger.info("开始推送到 GitHub...")

            # 打开仓库
            repo = Repo(self.project_dir)

            # 检查是否有更改
            if repo.is_dirty(untracked_files=True):
                # 添加所有更改
                repo.git.add(A=True)

                # 创建提交
                author = Actor("Reddit Suno Bot", "bot@reddit-suno.com")
                repo.index.commit(commit_message, author=author)

                # 推送到远程仓库
                origin = repo.remote(name="origin")
                if not origin.exists():
                    # 如果远程仓库不存在，添加
                    origin = repo.create_remote("origin", self.github_url)

                # 推送
                origin.push(branch)

                logger.info(f"成功推送到 GitHub: {branch}")
                return True
            else:
                logger.info("没有需要推送的更改")
                return False

        except Exception as e:
            logger.error(f"推送到 GitHub 失败: {e}")
            return False

    def pull_from_github(self, branch: str = "main") -> bool:
        """
        从 GitHub 拉取最新代码

        Args:
            branch: 分支名称

        Returns:
            拉取成功返回 True，失败返回 False
        """
        try:
            logger.info("开始从 GitHub 拉取最新代码...")

            # 打开仓库
            repo = Repo(self.project_dir)

            # 拉取
            origin = repo.remote(name="origin")
            if origin.exists():
                origin.pull(branch)
                logger.info("成功从 GitHub 拉取最新代码")
                return True
            else:
                logger.warning("远程仓库不存在，跳过拉取")
                return False

        except Exception as e:
            logger.error(f"从 GitHub 拉取失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    config = {
        "token": "your_github_token",
        "repo": "Baggio200cn/reddit-suno-agent"
    }

    publisher = GitHubPublisher(config, project_dir=".")

    # 测试推送
    success = publisher.push_to_github("测试提交", branch="main")

    if success:
        print("推送成功")
    else:
        print("推送失败")
