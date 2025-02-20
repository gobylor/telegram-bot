import os
import sys
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    API_ID: Optional[str] = None
    API_HASH: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    
    model_config = SettingsConfigDict(env_file='.env', case_sensitive=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_settings()
    
    def _validate_settings(self) -> None:
        """验证配置并提供友好的错误提示"""
        missing_vars = []
        
        if not self.API_ID:
            missing_vars.append("API_ID")
        if not self.API_HASH:
            missing_vars.append("API_HASH")
            
        if missing_vars:
            print("\n❌ 配置错误:")
            print("缺少必要的环境变量:", ", ".join(missing_vars))
            print("\n📝 请按照以下步骤设置:")
            print("1. 访问 https://my.telegram.org/auth 获取 API 凭证")
            print("2. 在项目根目录创建 .env 文件")
            print("3. 添加以下内容到 .env 文件:")
            print("   API_ID=your_api_id")
            print("   API_HASH=your_api_hash")
            print("\n❗ 注意: API_ID 和 API_HASH 需要替换为你从 Telegram 获取的实际值")
            sys.exit(1)

try:
    settings = Settings()
except Exception as e:
    print("\n❌ 加载配置文件时出错:")
    print(f"错误信息: {str(e)}")
    print("\n💡 提示: 请确保 .env 文件存在且格式正确")
