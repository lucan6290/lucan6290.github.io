"""
博客管理后台 - 入口
用法: python main.py
    或: uvicorn app.main:app --host 0.0.0.0 --port 15000 --reload
"""
import uvicorn
from app.config import SERVER_HOST, SERVER_PORT

if __name__ == "__main__":
    print(f"博客管理后台服务器 (Python FastAPI) 启动中...")
    print(f"  地址: http://localhost:{SERVER_PORT}")
    print(f"  API 文档: http://localhost:{SERVER_PORT}/docs")
    uvicorn.run(
        "app.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        reload_dirs=["app"],
    )
