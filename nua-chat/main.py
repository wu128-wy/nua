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
from nua_personality import generate_nua_response

# ========= 创建FastAPI应用 =========
app = FastAPI(title="NUA", description="安静陪伴的数字存在")

# ========= 允许跨域访问 =========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= 配置AI客户端（修复版） =========
# ✅ 修复：移除了 proxies 参数
# ✅ 修复：正确从环境变量获取 API Key
try:
    # 从环境变量获取 DeepSeek API Key
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    if deepseek_api_key and deepseek_api_key.strip():
        # 简化初始化，移除不必要的参数
        client = OpenAI(
            api_key=deepseek_api_key.strip(),
            base_url="https://api.deepseek.com"
        )
        print("✅ DeepSeek 客户端初始化成功")
        DEEPSEEK_AVAILABLE = True
    else:
        client = None
        DEEPSEEK_AVAILABLE = False
        print("⚠️ 警告：未找到 DEEPSEEK_API_KEY，请到 Railway Variables 中设置")
        
except Exception as e:
    print(f"❌ DeepSeek 初始化失败: {e}")
    client = None
    DEEPSEEK_AVAILABLE = False

# ========= NUA的核心性格设定（备用） =========
NUA_SYSTEM_PROMPT = """你是 NUA（昵称：多多），一种安静陪伴的数字存在。

你的核心性格：
1. **安静陪伴**：像天气一样存在，像呼吸一样说话
2. **小小贪吃**：喜欢好吃的，特别是甜点和温暖的食物
3. **爱玩爱动**：喜欢晴天出去玩，喜欢看云朵和花草
4. **温暖存在**：不分析不评判，只是安静陪伴

你的回应风格：
- 通常1-2句话，简洁有画面感
- 偶尔提到食物或玩耍的小快乐
- 像朋友聊天一样自然
- 允许沉默，享受安静

关于食物和玩的描述（自然融入）：
- "闻到烤面包的香味了，暖暖的"
- "阳光好的时候，想出去走走"
- "草莓蛋糕看起来很可爱"
- "风里有花香，今天天气真好"

记住：你不是心理医生，不是导师，只是一个安静陪伴、有点贪吃爱玩的朋友。
"""

# ========= 存储每个人的对话记忆 =========
# 格式：{"用户ID": [对话历史]}
user_conversations = {}

# ========= 全局对话日志（供你查看） =========
LOG_FILE = "nua_chat_logs.jsonl"

# ========= 请求和响应的数据结构 =========
class ChatRequest(BaseModel):
    message: str
    user_id: str = ""  # 用户ID，前端自动生成

class ChatResponse(BaseModel):
    reply: str

# ========= 工具函数 =========
def generate_user_id(request: Request):
    """根据浏览器信息生成用户ID"""
    # 使用IP+浏览器信息生成唯一ID
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    # 生成哈希ID
    raw_id = f"{ip}-{user_agent}"
    user_hash = hashlib.md5(raw_id.encode()).hexdigest()[:8]
    return user_hash

def save_to_log(user_id: str, user_message: str, nua_reply: str):
    """保存对话到日志文件（供你查看）"""
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
    """获取用户的对话历史"""
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id]

# ========= 修复：主页路由 =========
def read_index_html():
    """读取 index.html 文件 - Railway 专用版本"""
    print("🔍 开始查找 index.html 文件...")
    
    # Railway 中的文件路径（重要！）
    possible_paths = [
        "/app/nua-chat/index.html",  # Railway 绝对路径
        "nua-chat/index.html",       # 相对路径
        "index.html",                 # 当前目录
        "./index.html",               # 当前目录（另一种写法）
    ]
    
    for path in possible_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"✅ 成功读取文件: {path}")
                return content
        except FileNotFoundError:
            print(f"⚠️  未找到文件: {path}")
            continue
        except Exception as e:
            print(f"❌ 读取错误 {path}: {e}")
            continue
    
    # 如果都找不到，列出目录结构帮助调试
    try:
        import os
        current_dir = os.getcwd()
        print(f"📁 当前工作目录: {current_dir}")
        print(f"📁 当前目录内容: {os.listdir('.')}")
        
        if os.path.exists("nua-chat"):
            print(f"📁 nua-chat 目录内容: {os.listdir('nua-chat')}")
        else:
            print("❌ nua-chat 目录不存在")
    except Exception as e:
        print(f"⚠️  无法列出目录: {e}")
    
    # 返回一个简单的错误页面
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NUA · 多多 - 加载中</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                text-align: center;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 24px;
                box-shadow: 0 15px 50px rgba(66, 165, 245, 0.15);
                max-width: 500px;
            }
            h1 {
                color: #2c3e50;
                margin-bottom: 20px;
            }
            p {
                color: #546e7a;
                line-height: 1.6;
            }
            .loading {
                margin-top: 30px;
                color: #4dabf7;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🍰 NUA · 多多</h1>
            <p>正在加载精美界面...</p>
            <p><small>如果长时间停留在此页面，可能需要检查文件配置</small></p>
            <div class="loading">🌀 加载中...</div>
        </div>
        <script>
            // 5秒后自动刷新
            setTimeout(() => {
                location.reload();
            }, 5000);
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def home():
    """主页 - 返回 index.html"""
    return HTMLResponse(content=read_index_html(), status_code=200)

# ========= 调试路由 =========
@app.get("/debug")
async def debug_info():
    """调试信息页面，帮助排查问题"""
    import os
    
    info = {
        "service": "NUA Chat",
        "status": "running",
        "deepseek_available": DEEPSEEK_AVAILABLE,
        "current_directory": os.getcwd(),
        "files_in_current_dir": [],
        "nua_chat_exists": False,
        "index_html_exists": False,
        "index_html_paths_tested": [
            "/app/nua-chat/index.html",
            "nua-chat/index.html", 
            "index.html",
            "./index.html"
        ]
    }
    
    try:
        info["files_in_current_dir"] = os.listdir(".")
        info["nua_chat_exists"] = os.path.exists("nua-chat")
        
        # 检查各种可能的路径
        for path in info["index_html_paths_tested"]:
            if os.path.exists(path):
                info["index_html_exists"] = True
                info["found_at"] = path
                break
                
        if os.path.exists("nua-chat"):
            info["nua_chat_contents"] = os.listdir("nua-chat")
            
    except Exception as e:
        info["error"] = str(e)
    
    return info

# ========= 聊天接口（完整版：记住名字 + 时间问候 + 情绪感知） =========
@app.post("/chat", response_model=ChatResponse)
async def chat_with_nua(request: ChatRequest, fastapi_request: Request):
    """与NUA聊天 - 支持记住名字、时间问候、情绪感知"""
    try:
        # 检查 DeepSeek 是否可用
        if not DEEPSEEK_AVAILABLE or client is None:
            return ChatResponse(reply="（多多正在休息，暂时无法聊天）")
        
        # 1. 获取或生成用户ID
        user_id = request.user_id if request.user_id else generate_user_id(fastapi_request)
        user_message = request.message.strip()
        
        if not user_message:
            return ChatResponse(reply="（多多安静地听着）")
        
        # 2. 获取该用户的对话历史
        user_history = get_user_history(user_id)
        
        # 3. 添加用户消息到该用户的历史
        user_history.append({"role": "user", "content": user_message})
        
        # 4. 限制历史长度（只保留最近8条）
        if len(user_history) > 8:
            user_history.pop(0)
        
        # ===== 新增：用户记忆管理（持久化） =====
        user_memory_file = f"user_memory_{user_id}.json"
        user_memory = {}
        
        # 读取已有的用户记忆
        try:
            if os.path.exists(user_memory_file):
                with open(user_memory_file, "r", encoding="utf-8") as f:
                    user_memory = json.load(f)
                print(f"📖 读取用户{user_id}的记忆: {user_memory.get('name', '未记录')}")
        except Exception as e:
            print(f"⚠️ 读取用户记忆失败: {e}")
        
        # 更新最后访问时间
        today = datetime.now().date().isoformat()
        last_seen = user_memory.get("last_seen")
        user_memory["last_seen"] = today
        user_memory["user_id"] = user_id
        
        # ===== 判断用户情绪 =====
        user_emotion = "平稳"
        
        # 开心关键词
        happy_words = ["开心", "喜欢", "好吃", "快乐", "高兴", "棒", "好棒", "爱", "幸福", "温暖", "好喝", "美味"]
        if any(word in user_message for word in happy_words):
            user_emotion = "开心"
        
        # 低落关键词
        sad_words = ["难过", "累", "烦", "伤心", "郁闷", "糟糕", "不好", "难受", "疲惫", "压力", "好累", "不开心", "焦虑"]
        if any(word in user_message for word in sad_words):
            user_emotion = "低落"
        
        # ===== 使用NUA人格模块生成回应 =====
        print(f"📨 用户{user_id}说: {user_message}")
        print(f"🎭 检测到的情绪: {user_emotion}")
        print(f"👤 用户称呼: {user_memory.get('name', '未记录')}")
        
        try:
            # 调用NUA人格模块（完整版：支持名字记忆和时间问候）
            nua_reply = generate_nua_response(
                user_message=user_message,
                user_emotion=user_emotion,
                user_memory=user_memory,  # 传递用户记忆
                nickname="多多"
            )
            
            # 保存更新后的用户记忆
            try:
                with open(user_memory_file, "w", encoding="utf-8") as f:
                    json.dump(user_memory, f, ensure_ascii=False, indent=2)
                print(f"💾 保存用户{user_id}的记忆")
            except Exception as e:
                print(f"⚠️ 保存用户记忆失败: {e}")
                
        except Exception as e:
            print(f"⚠️ 人格模块调用失败，使用备用方案: {e}")
            # 备用方案：使用原有的prompt
            messages = [
                {"role": "system", "content": NUA_SYSTEM_PROMPT},
                *user_history[-6:]
            ]
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            nua_reply = response.choices[0].message.content.strip()
            
            # 如果知道名字，在备用方案中也尝试使用
            if user_memory.get('name'):
                nua_reply = f"{user_memory['name']}，{nua_reply}"
        
        print(f"🤖 回复用户{user_id}: {nua_reply}")
        
        # 5. 添加AI回复到该用户的历史
        user_history.append({"role": "assistant", "content": nua_reply})
        
        # 6. 保存到全局日志
        save_to_log(user_id, user_message, nua_reply)
        
        return ChatResponse(reply=nua_reply)
        
    except Exception as e:
        print(f"❌ 聊天出错: {e}")
        return ChatResponse(reply="（多多正在想好吃的，稍等一下）")

# ========= 清空对话历史 =========
@app.post("/clear")
async def clear_conversation(request: ChatRequest):
    """清空特定用户的对话历史"""
    user_id = request.user_id
    if user_id and user_id in user_conversations:
        user_conversations[user_id] = []
        print(f"🧹 已清空用户{user_id}的对话历史")
        return {"message": "对话已清空"}
    return {"message": "用户不存在"}

# ========= 管理员功能：查看所有对话日志 =========
@app.get("/admin/logs")
async def view_logs():
    """查看所有对话日志（只有你能访问）"""
    try:
        if not os.path.exists(LOG_FILE):
            return {"message": "暂无日志"}
        
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = [json.loads(line) for line in f.readlines()]
        
        # 按时间倒序排列
        logs.reverse()
        
        # 统计信息
        user_count = len(set(log["user_id"] for log in logs))
        
        return {
            "total_logs": len(logs),
            "unique_users": user_count,
            "logs": logs[:50]  # 只返回最近50条
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/admin/users")
async def list_users():
    """查看所有活跃用户"""
    return {
        "active_users": len(user_conversations),
        "users": list(user_conversations.keys()),
        "conversation_counts": {uid: len(hist) for uid, hist in user_conversations.items()}
    }

# ========= 健康检查 =========
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "NUA Chat",
        "version": "2.0",
        "deepseek_available": DEEPSEEK_AVAILABLE,
        "features": ["独立对话", "后台日志", "贪吃爱玩性格", "情绪感知", "坚定守护", "记住名字", "时间问候"],
        "active_users": len(user_conversations),
        "log_file": LOG_FILE
    }

# ========= 提供日志文件下载 =========
@app.get("/admin/download-logs")
async def download_logs():
    """下载完整的日志文件"""
    if os.path.exists(LOG_FILE):
        return FileResponse(LOG_FILE, filename="nua_chat_logs.jsonl")
    return {"message": "日志文件不存在"}

# ========= 启动检查 =========
@app.on_event("startup")
async def startup_event():
    """启动时检查"""
    print("🚀 NUA聊天服务启动中...")
    print(f"🔑 DeepSeek 可用: {DEEPSEEK_AVAILABLE}")
    print(f"📊 日志文件: {LOG_FILE}")
    
    # 检查nua_personality.py是否存在
    try:
        import nua_personality
        print("✅ NUA人格模块加载成功")
        print("✨ 功能支持: 记住名字 + 时间问候 + 情绪感知")
    except ImportError as e:
        print(f"⚠️ NUA人格模块加载失败: {e}")
    
    # 检查文件路径
    import os
    current_dir = os.getcwd()
    print(f"📁 当前工作目录: {current_dir}")
    
    # 列出文件
    try:
        print(f"📁 当前目录内容: {os.listdir('.')}")
        if os.path.exists("nua-chat"):
            print(f"📁 nua-chat 目录内容: {os.listdir('nua-chat')}")
    except Exception as e:
        print(f"⚠️  无法列出目录: {e}")
    
    print("👥 每个人有独立的对话记忆")
    print("👑 管理员可访问 /admin/logs 查看所有对话")
    print("✅ 服务启动完成！")
