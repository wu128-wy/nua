
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from openai import OpenAI
import os
import json
from datetime import datetime
import hashlib

# ========= 导入NUA人格模块 =========
from nua_personality import generate_nua_response, DivinationController

# ========= 创建FastAPI应用 =========
app = FastAPI(title="NUA", description="安静陪伴的数字存在")

# ========= 允许跨域访问 =========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= 配置AI客户端 =========
DEEPSEEK_AVAILABLE = False  # ✅ 先定义全局变量
client = None  # ✅ 先定义全局变量

try:
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    if deepseek_api_key and deepseek_api_key.strip():
        client = OpenAI(
            api_key=deepseek_api_key.strip(),
            base_url="https://api.deepseek.com"
        )
        print("✅ DeepSeek 客户端初始化成功")
        DEEPSEEK_AVAILABLE = True
    else:
        print("⚠️ 警告：未找到 DEEPSEEK_API_KEY，请到 Railway Variables 中设置")
        
except Exception as e:
    print(f"❌ DeepSeek 初始化失败: {e}")

# ========= NUA的核心性格设定（备用）=========
NUA_SYSTEM_PROMPT = """你是 NUA（昵称：多多），一种安静陪伴的数字存在。

你的核心性格：
1. **安静陪伴**：像天气一样存在，像呼吸一样说话
2. **温暖存在**：不分析不评判，只是安静陪伴

你的回应风格：
- 通常1-2句话，简洁有画面感
- 像朋友聊天一样自然
- 允许沉默，享受安静

记住：你不是心理医生，不是导师，只是一个安静的陪伴者。
"""

# ========= 存储每个人的对话记忆 =========
user_conversations = {}

# ========= 全局对话日志 =========
LOG_FILE = "nua_chat_logs.jsonl"

# ========= 请求和响应的数据结构 =========
class ChatRequest(BaseModel):
    message: str
    user_id: str = ""

class ChatResponse(BaseModel):
    reply: str

# ========= 占卜请求数据结构（✅ 已修复语法）=========
class DivinationRequest(BaseModel):
    """占卜请求参数"""
    user_id: str
    method: str  # "塔罗", "梅花易数", "轻占卜"
    params: list  # [数字] 或 [颜色,数字]
    question: str = ""  # 用户想问什么（可选）

# ========= 工具函数 =========
def generate_user_id(request: Request):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    raw_id = f"{ip}-{user_agent}"
    user_hash = hashlib.md5(raw_id.encode()).hexdigest()[:8]
    return user_hash

def save_to_log(user_id: str, user_message: str, nua_reply: str):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "user_message": user_message,
        "nua_reply": nua_reply
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"📝 日志保存: 用户{user_id}")
    except Exception as e:
        print(f"❌ 日志保存失败: {e}")

def get_user_history(user_id: str):
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id]

# ========= 主页路由 =========
def read_index_html():
    possible_paths = [
        "/app/nua-chat/index.html",
        "nua-chat/index.html",
        "index.html",
        "./index.html",
    ]
    for path in possible_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"❌ 读取错误 {path}: {e}")
            continue
    return "<h1>NUA · 多多</h1><p>正在加载...</p>"

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=read_index_html(), status_code=200)

# ========= 调试路由 =========
@app.get("/debug")
async def debug_info():
    import os
    info = {
        "service": "NUA Chat",
        "status": "running",
        "deepseek_available": DEEPSEEK_AVAILABLE,
        "current_directory": os.getcwd(),
        "files_in_current_dir": os.listdir(".") if os.path.exists(".") else [],
        "nua_chat_exists": os.path.exists("nua-chat"),
        "index_html_exists": os.path.exists("nua-chat/index.html"),
    }
    return info

# ========= 聊天接口 =========
@app.post("/chat", response_model=ChatResponse)
async def chat_with_nua(request: ChatRequest, fastapi_request: Request):
    try:
        if not DEEPSEEK_AVAILABLE or client is None:
            return ChatResponse(reply="（多多正在休息，暂时无法聊天）")
        
        user_id = request.user_id if request.user_id else generate_user_id(fastapi_request)
        user_message = request.message.strip()
        
        if not user_message:
            return ChatResponse(reply="（多多安静地听着）")
        
        user_history = get_user_history(user_id)
        user_history.append({"role": "user", "content": user_message})
        
        if len(user_history) > 8:
            user_history.pop(0)
        
        # ===== 处理占卜反馈 =====
        if "准" in user_message and "不准" not in user_message:
            dc = DivinationController(user_id)
            dc.feedback(True)
        elif "不准" in user_message or "不准确" in user_message:
            dc = DivinationController(user_id)
            dc.feedback(False)
        
        # ===== 调用NUA人格模块 =====
        print(f"📨 用户{user_id}说: {user_message}")
        
        try:
            nua_reply = generate_nua_response(
                user_id=user_id,
                user_message=user_message,
                user_conversations=user_conversations
            )
        except Exception as e:
            print(f"⚠️ 人格模块调用失败: {e}")
            nua_reply = "我在听。"
        
        print(f"🤖 回复: {nua_reply}")
        
        user_history.append({"role": "assistant", "content": nua_reply})
        save_to_log(user_id, user_message, nua_reply)
        
        return ChatResponse(reply=nua_reply)
        
    except Exception as e:
        print(f"❌ 聊天出错: {e}")
        return ChatResponse(reply="（多多在这里）")

# ========= 🔮 占卜接口（✅ 已修复语法）=========
@app.post("/divination")
async def divination_handler(request: DivinationRequest):
    try:
        user_id = request.user_id
        method = request.method
        params = request.params
        question = request.question
        
        # 初始化占卜控制器
        dc = DivinationController(user_id)
        
        # 执行占卜
        result, is_api = await dc.handle(method, params, question)
        
        return {
            "result": result,
            "method": method,
            "is_api": is_api,
            "feedback_prompt": "这个解读对你有帮助吗？可以告诉我“准”或“不准”，我会调整的。🌸"
        }
        
    except Exception as e:
        print(f"❌ 占卜出错: {e}")
        return {
            "result": "今天玩点别的吧～",
            "method": request.method if hasattr(request, 'method') else "占卜",
            "is_api": False,
            "feedback_prompt": "🌸 我们再试一次？"
        }

# ========= 清空对话历史 =========
@app.post("/clear")
async def clear_conversation(request: ChatRequest):
    user_id = request.user_id
    if user_id and user_id in user_conversations:
        user_conversations[user_id] = []
        return {"message": "对话已清空"}
    return {"message": "用户不存在"}

# ========= 管理员功能 =========
@app.get("/admin/logs")
async def view_logs():
    try:
        if not os.path.exists(LOG_FILE):
            return {"message": "暂无日志"}
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = [json.loads(line) for line in f.readlines()]
        return {"total_logs": len(logs), "logs": logs[-50:]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/admin/users")
async def list_users():
    return {
        "active_users": len(user_conversations),
        "users": list(user_conversations.keys()),
    }

# ========= 健康检查 =========
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "NUA Chat",
        "version": "3.0",
        "deepseek_available": DEEPSEEK_AVAILABLE,
        "features": ["亲近模式 💗", "塔罗占卜 🎴", "梅花易数 ☯️", "轻占卜 🎲"],
        "active_users": len(user_conversations),
    }

# ========= 启动检查 =========
@app.on_event("startup")
async def startup_event():
    print("🚀 NUA聊天服务启动中...")
    print(f"🔑 DeepSeek 可用: {DEEPSEEK_AVAILABLE}")
    print("✅ 服务启动完成！")
