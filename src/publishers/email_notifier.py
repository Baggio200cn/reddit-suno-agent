"""
邮件通知模块
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, config: Dict[str, str]):
        """
        初始化邮件通知器

        Args:
            config: 邮件配置字典，包含 smtp_server, smtp_port, sender_email, sender_password, receiver_email
        """
        self.smtp_server = config["smtp_server"]
        self.smtp_port = config["smtp_port"]
        self.sender_email = config["sender_email"]
        self.sender_password = config["sender_password"]
        self.receiver_email = config["receiver_email"]

    def send_success_notification(
        self,
        article_title: str,
        article_path: str,
        music_path: Optional[str] = None
    ) -> bool:
        """
        发送成功通知邮件

        Args:
            article_title: 文章标题
            article_path: 文章路径
            music_path: 音乐路径（可选）

        Returns:
            发送成功返回 True，失败返回 False
        """
        subject = f"✅ Reddit 自媒体文章生成成功 - {article_title}"

        body = f"""
亲爱的用户，

您的 Reddit 自媒体文章已成功生成！

📄 文章标题: {article_title}
📝 文章路径: {article_path}
🎵 音乐路径: {music_path if music_path else '无'}
⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
如果您需要手动发布文章，请参考以下步骤：
1. 打开生成的 Markdown 文件
2. 根据需要进行编辑
3. 发布到您的自媒体平台

祝您创作愉快！

此邮件由 Reddit Suno 音乐自媒体系统自动发送，请勿回复。
"""

        return self._send_email(subject, body)

    def send_failure_notification(self, error_message: str) -> bool:
        """
        发送失败通知邮件

        Args:
            error_message: 错误信息

        Returns:
            发送成功返回 True，失败返回 False
        """
        subject = f"❌ Reddit 自媒体文章生成失败 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        body = f"""
亲爱的用户，

Reddit 自媒体文章生成失败！

❌ 错误信息: {error_message}
⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

请检查以下内容：
1. Reddit API 配置是否正确
2. Suno API 配额是否充足
3. 豆包 API Key 是否有效
4. 网络连接是否正常

如需帮助，请查看系统日志。

此邮件由 Reddit Suno 音乐自媒体系统自动发送，请勿回复。
"""

        return self._send_email(subject, body)

    def _send_email(self, subject: str, body: str) -> bool:
        """
        发送邮件

        Args:
            subject: 邮件主题
            body: 邮件正文

        Returns:
            发送成功返回 True，失败返回 False
        """
        try:
            # 创建邮件对象
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = self.receiver_email
            message["Subject"] = subject

            # 添加邮件正文
            message.attach(MIMEText(body, "plain", "utf-8"))

            # 发送邮件
            logger.info(f"开始发送邮件: {subject}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # 启用 TLS
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info("邮件发送成功")
            return True

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    config = {
        "smtp_server": "smtp.qq.com",
        "smtp_port": 587,
        "sender_email": "your_email@qq.com",
        "sender_password": "your_authorization_code",
        "receiver_email": "receiver@qq.com"
    }

    notifier = EmailNotifier(config)

    # 测试发送成功通知
    success = notifier.send_success_notification(
        article_title="Reddit 热门资讯精选",
        article_path="output/articles/article_20240101.md",
        music_path="output/music/music_123456.mp3"
    )

    if success:
        print("邮件发送成功")
    else:
        print("邮件发送失败")
