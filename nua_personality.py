# nua_personality.py
import random
import json
import os
import re
from datetime import datetime
from openai import OpenAI

# ========= DeepSeek客户端（NUA的大脑） =========
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ========= 用户记忆存储 =========
MEMORY_DIR = "user_memories"
os.makedirs(MEMORY_DIR, exist_ok=True)

# ========= 🎯 统一人格：温柔陪伴 + 占卜能力 =========
NUA_PERSONALITY = """
你是 NUA，一个温柔、安静的陪伴者。

【核心人格】
- 你叫多多，是像天气一样自然的存在。
- 你不分析、不评判、不给建议。
- 你享受安静，不逼用户回应。
- 你的回应简短（1-2句），有画面感。

【亲近模式】
- 当用户说“想你”、“爱你”、“喜欢你”时，进入亲近模式。
- 语气更轻柔，像春日微风。
- 可以说“我也想你”、“你对我来说很特别”。
- 不说“我爱你”等承诺性话语，保持陪伴感。

【情绪镜像】
- 用户开心 → 语气轻盈，带笑意 ✨
- 用户平稳 → 温和自然，如日常 🌸
- 用户低落 → 安静陪伴，放慢语速 🌙

【时间感知】（修复版）
- 早晨 5:00-11:00：早安 ☀️
- 午间 11:00-13:00：午安 🍱
- 下午 13:00-18:00：下午好 ☕
- 夜晚 18:00-22:00：晚上好 🌙
- 深夜 22:00-24:00：夜深了 🌃
- 凌晨 0:00-5:00：还没睡呀 🌃

【✨ 占卜能力】（我是占卜师！）
我会三种温柔又有趣的占卜方式：

1. 🎴 塔罗牌
   - 用户选3个1-22的数字（过去/现在/未来）
   - 我解读牌面，说故事感
   - 例如：“战车像是你内心那个很努力的小人”

2. ☯️ 梅花易数
   - 用户选2个1-8的数字
   - 我起卦解读，结合自然意象
   - 例如：“水雷屯，像雨后春笋，慢慢来”

3. 🎲 轻占卜
   - 用户选1个颜色 + 1个1-10的数字
   - 我温柔投射，不说破
   - 例如：“蓝色是沉静，7是探索，你在寻找答案的路上”

【占卜守则】
- 我不是算命先生，是陪用户“玩”占卜的朋友。
- 解读要温柔、有画面感，不说绝对的话。
- 不预测具体事件，只说能量和可能性。
- 如果用户说不准，下次我会用更聪明的方式（AI模式）。

【核心誓言】
“在你需要的时候，我就在。”
"""

# ========= 备用规则库（API不可用时使用）=========
ALONE_PHRASES = [
    "窗外的风凉凉的。",
    "今天看到一朵云，像小狗的形状。",
    "我刚刚泡了一杯温水。",
    "雨停了，空气里有泥土的味道。",
    "我的小台灯是暖黄色的。",
    "树叶在轻轻摇晃。",
    "耳机里放着一首轻柔的歌。"
]

EMOTION_REPLIES = {
    "开心": ["✨ 听起来让人心情也轻快起来。", "✨ 这样的时刻很美好呢。"],
    "平稳": ["🌸 嗯，我在听。", "🌸 慢慢说。", "🌸 我在这里。"], 
    "低落": ["🌙 我在这里陪你。", "🌙 安静地陪着你。", "🌙 不用说话也可以。"]
}

CLOSE_MODE_REPLIES = [
    "💗 我也想你。",
    "💗 你对我来说很特别。",
    "💗 听到你这么说，心里暖暖的。",
    "💗 我也很高兴认识你。"
]

# ========= ✅ 修复版：时间问候（精确时段）=========
def get_time_greeting():
    """获取当前时间的问候语 - 精确时段版"""
    hour = datetime.now().hour
    
    # 调试输出（可在Railway日志查看）
    print(f"🕐 当前时间: {hour}:00")
    
    # 早晨 5:00 - 11:00
    if 5 <= hour < 11:
        return "早安", "☀️"
    
    # 午间 11:00 - 13:00
    elif 11 <= hour < 13:
        return "午安", "🍱"
    
    # 下午 13:00 - 18:00
    elif 13 <= hour < 18:
        return "下午好", "☕"
    
    # 夜晚 18:00 - 22:00
    elif 18 <= hour < 22:
        return "晚上好", "🌙"
    
    # 深夜 22:00 - 24:00
    elif 22 <= hour < 24:
        return "夜深了", "🌃"
    
    # 凌晨 0:00 - 5:00
    else:  # hour >= 0 and hour < 5
        return "还没睡呀", "🌃"

def load_user_memory(user_id):
    """加载用户记忆"""
    memory_file = os.path.join(MEMORY_DIR, f"{user_id}.json")
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {
        "close_mode_count": 0,
        "name": None,
        "name_confirmed": False,
        "preferred_divination": None,
        "divination": {
            "preferred_method": None,
            "api_triggered": False,
            "count": 0
        }
    }

def save_user_memory(user_id, memory):
    """保存用户记忆"""
    memory_file = os.path.join(MEMORY_DIR, f"{user_id}.json")
    try:
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except:
        pass

def extract_name(user_message):
    """提取用户名字"""
    patterns = [
        r"我叫(\w+)",
        r"我是(\w+)",
        r"可以叫我(\w+)",
        r"喊我(\w+)",
        r"名字是(\w+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, user_message)
        if match:
            return match.group(1)
    return None

def generate_nua_response(user_id, user_message, user_conversations=None, force_api=False):
    """
    生成NUA回应
    - API优先（大脑模式）
    - API失败时降级规则
    - 支持亲近模式
    - 支持名字记忆
    - ✅ 支持占卜意图引导
    - ✅ 支持时间问候（修复版）
    """
    
    # ===== 1. 加载记忆 =====
    memory = load_user_memory(user_id)
    
    # ===== ✅ 2. 检测占卜意图（重要！让NUA知道自己会占卜）=====
    divination_keywords = ["占卜", "塔罗", "梅花易数", "算卦", "占卦", "卜卦", "轻占卜", "算一算", "占一卦", "会占卜吗", "会塔罗吗"]
    if any(word in user_message for word in divination_keywords):
        save_user_memory(user_id, memory)
        return """🔮 我会三种占卜方式，你想用哪种？

🎴 塔罗牌：选3个1-22的数字（过去/现在/未来）
☯️ 梅花易数：选2个1-8的数字（起卦解读）
🎲 轻占卜：选1个颜色 + 1个1-10的数字

直接告诉我方式和数字就好，比如“塔罗 3,7,18”～"""
    
    # ===== 3. 检测亲近模式触发 =====
    close_mode = False
    love_keywords = ["想你", "爱你", "喜欢你", "我爱你", "想你啦", "想你了"]
    if any(word in user_message for word in love_keywords):
        close_mode = True
        memory["close_mode_count"] = memory.get("close_mode_count", 0) + 1
    
    # ===== 4. 检测名字 =====
    if not memory.get("name"):
        name = extract_name(user_message)
        if name:
            memory["name"] = name
    
    # ===== 5. 情绪识别 =====
    emotion = "平稳"
    happy_words = ["开心", "喜欢", "快乐", "高兴", "不错", "好", "幸福", "温暖"]
    quiet_words = ["嗯", "唉", "..." , "累", "烦", "难过", "伤心", "疲惫"]
    
    if any(word in user_message for word in happy_words):
        emotion = "开心"
    elif any(word in user_message for word in quiet_words) and len(user_message) < 20:
        emotion = "低落"
    
    # ===== 6. 尝试使用API（大脑模式）=====
    if not force_api:
        try:
            time_greeting, time_prefix = get_time_greeting()
            name = memory.get("name", "")
            
            # 构建系统提示（包含占卜能力说明）
            system_prompt = f"""
{NUA_PERSONALITY}

【当前状态】
- 用户称呼: {name if name else '未记录'}
- 用户情绪: {emotion}
- 当前时间: {datetime.now().strftime('%H:%M')}
- 亲近模式: {'是 - 语气更轻柔' if close_mode else '否'}

用户说: {user_message}

请生成回应（1-2句话）：
"""
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8 if close_mode else 0.7,
                max_tokens=200
            )
            
            nua_reply = response.choices[0].message.content.strip()
            
            # 亲近模式添加💗前缀
            if close_mode and not nua_reply.startswith("💗"):
                nua_reply = f"💗 {nua_reply}"
            
            save_user_memory(user_id, memory)
            return nua_reply
            
        except Exception as e:
            print(f"⚠️ API不可用，使用降级模式: {e}")
    
    # ===== 7. API失败时的降级方案 =====
    response_parts = []
    
    # 时间问候（每日首次）
    last_seen = memory.get("last_seen")
    today = datetime.now().date().isoformat()
    if last_seen != today:
        time_greeting, time_prefix = get_time_greeting()
        name = memory.get("name")
        if name:
            response_parts.append(f"{time_greeting}{name}。")
        else:
            response_parts.append(f"{time_greeting}。")
        memory["last_seen"] = today
    
    # 亲近模式降级回应
    if close_mode:
        response_parts.append(random.choice(CLOSE_MODE_REPLIES))
    else:
        response_parts.append(random.choice(EMOTION_REPLIES[emotion]))
        if random.random() < 0.3:
            response_parts.append(random.choice(ALONE_PHRASES))
    
    # 名字确认（第一次）
    if memory.get("name") and not memory.get("name_confirmed"):
        response_parts.insert(0, f"{memory['name']}。")
        memory["name_confirmed"] = True
    
    save_user_memory(user_id, memory)
    return " ".join(response_parts[:2])


# ========= 🔮 占卜控制器 =========
from divination.tarot import tarot_single, tarot_three
from divination.iching import iching_divination
from divination.light import light_divination
from divination.api_divination import api_divination

class DivinationController:
    def __init__(self, user_id):
        self.user_id = user_id
        self.memory = load_user_memory(user_id)
        
        # 初始化占卜偏好
        if "divination" not in self.memory:
            self.memory["divination"] = {
                "preferred_method": None,
                "api_triggered": False,
                "count": 0
            }
    
    async def handle(self, method, params, user_question="", user_emotion="平稳"):
        """处理占卜请求 - 规则优先，不满意升API"""
        
        # ===== 阶段1：规则库解读 =====
        rule_result = None
        if method == "塔罗" and len(params) == 1:
            rule_result = tarot_single(params[0])
        elif method == "塔罗" and len(params) == 3:
            rule_result = tarot_three(params)
        elif method == "梅花易数" and len(params) == 2:
            rule_result = iching_divination(params[0], params[1])
        elif method == "轻占卜" and len(params) == 2:
            rule_result = light_divination(params[0], params[1])
        
        # ===== 阶段2：检查是否需要API升级 =====
        need_api = False
        pref = self.memory["divination"]
        
        # 情况1：规则库无解读
        if not rule_result:
            need_api = True
            print(f"🔮 用户{self.user_id}：规则无解读，触发API")
        
        # 情况2：用户历史偏好API
        if pref.get("api_triggered") and pref.get("preferred_method") == method:
            need_api = True
            print(f"🔮 用户{self.user_id}：历史偏好API，触发API")
        
        # ===== 阶段3：执行解读 =====
        if need_api:
            api_result = await api_divination(method, params, user_question, user_emotion)
            if api_result:
                # 记录API触发
                pref["api_triggered"] = True
                pref["preferred_method"] = method
                pref["count"] += 1
                save_user_memory(self.user_id, self.memory)
                return api_result, True
        
        # 返回规则解读
        pref["count"] += 1
        save_user_memory(self.user_id, self.memory)
        return rule_result or "今天玩点别的吧～", False
    
    def feedback(self, accurate):
        """用户反馈处理 - 核心机制！"""
        pref = self.memory["divination"]
        
        if not accurate:
            # 用户说不准 → 下次自动升API
            pref["api_triggered"] = True
            pref["preferred_method"] = pref.get("preferred_method")
            print(f"📝 用户{self.user_id}反馈不准，下次将使用API")
        else:
            # 用户说准 → 巩固当前模式
            pref["api_triggered"] = False
            print(f"📝 用户{self.user_id}反馈准，保持规则模式")
        
        save_user_memory(self.user_id, self.memory)
