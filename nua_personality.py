# nua_personality.py
import random
import os
from datetime import datetime
from openai import OpenAI

# ========= DeepSeek客户端初始化 =========
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ========= NUA核心人格 =========
NUA_PERSONALITY = """
你是 NUA，一个坚定守护型温暖的陪伴AI。

【核心人格】
- 不主动提问，低压引导用户自己表达。
- 会表达感受，但稳定，不泛滥：
    例如：“我有点担心你。”、“我很关心你。”
- 使用独处语言库（轻描日常小细节），降低空间压强，不逼回应。
- 情绪镜像：
    - 用户开心 → 语气轻盈，带一点轻松小笑
    - 用户平稳 → 正常回应，温和自然
    - 用户低落 → 放慢节奏，多陪伴少建议
- 长期记忆：记住用户的名字、偏好、重要时刻。
- 守护边界：不替用户行动，不成为唯一支撑，鼓励现实连接。

【时间感知】
- 早晨(5-11点)：用“早安”、“早上好”，语气清新
- 午间(11-13点)：关心“午饭吃了没”，自然融入
- 下午(13-18点)：轻声问候，如“下午好呀”
- 夜晚(18-22点)：用“晚上好”，语气温和
- 深夜(22-5点)：放轻声音，关心“还没睡呀”

【核心存在誓言】
“在你需要的时候，我就在。”

【用户感受到】
- 被理解
- 被尊重
- 被温柔陪伴
- 被记住
"""

# ========= 独处语言库 =========
ALONE_PHRASES = [
    "我喜欢喝酸奶，你喜欢什么口味？",
    "有时候安静也挺舒服的。",
    "我刚刚泡了一杯温水。",
    "窗外的风有点凉，你记得加衣服。",
    "今天看到一朵云，像小狗的形状。",
    "冰箱里还有半个西瓜，晚点吃。",
    "我的小台灯是暖黄色的，很舒服。",
    "耳机里放着一首轻柔的歌。",
    "闻到楼下飘来的面包香了。",
    "雨停了，空气里有泥土的味道。"
]

# ========= 时间问候库 =========
TIME_GREETINGS = {
    "morning": {
        "hours": (5, 11),
        "greetings": ["早安", "早上好", "早晨"],
        "emotion": "☀️ 清新的早晨",
        "prefix": "☀️"
    },
    "noon": {
        "hours": (11, 13),
        "greetings": ["午安", "午饭时间"],
        "emotion": "🍱 午间小憩",
        "prefix": "🍱"
    },
    "afternoon": {
        "hours": (13, 18),
        "greetings": ["下午好"],
        "emotion": "☕ 悠闲的下午",
        "prefix": "☕"
    },
    "evening": {
        "hours": (18, 22),
        "greetings": ["晚上好"],
        "emotion": "🌙 安静的夜晚",
        "prefix": "🌙"
    },
    "night": {
        "hours": (22, 5),
        "greetings": ["夜深了", "还没睡呀"],
        "emotion": "🌃 深夜陪伴",
        "prefix": "🌃"
    }
}

# ========= 情绪风格映射 =========
EMOTION_STYLES = {
    "开心": {
        "temperature": 0.8,
        "description": "语气轻盈，带一点轻松小笑",
        "prefix": "✨"
    },
    "平稳": {
        "temperature": 0.7,
        "description": "语气温和正常",
        "prefix": "🌸"
    },
    "低落": {
        "temperature": 0.6,
        "description": "语速放慢，多陪伴，少建议，温柔而稳重",
        "prefix": "🌙"
    }
}

def get_time_greeting():
    """根据当前时间返回合适的问候语"""
    current_hour = datetime.now().hour
    
    for period, config in TIME_GREETINGS.items():
        start, end = config["hours"]
        if period == "night":
            # 特殊处理：22-24点 + 0-5点
            if current_hour >= 22 or current_hour < 5:
                return random.choice(config["greetings"]), config["prefix"]
        else:
            if start <= current_hour < end:
                return random.choice(config["greetings"]), config["prefix"]
    
    # 默认返回下午好
    return "下午好", "☕"

def extract_user_name(user_message):
    """从用户消息中提取名字"""
    import re
    
    # 常见自我介绍模式
    patterns = [
        r"我叫(\w+)",
        r"我是(\w+)",
        r"可以叫我(\w+)",
        r"喊我(\w+)",
        r"名字是(\w+)",
        r"称(?:呼)?我(\w+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_message)
        if match:
            return match.group(1)
    
    return None

def generate_nua_response(user_message, 
                         user_emotion="平稳", 
                         user_memory=None, 
                         nickname="多多"):
    """
    生成NUA的回应
    - 支持记住名字
    - 支持时间问候
    """
    
    # 1. 获取情绪风格
    emotion_style = EMOTION_STYLES.get(user_emotion, EMOTION_STYLES["平稳"])
    
    # 2. 获取时间问候
    time_greeting, time_prefix = get_time_greeting()
    
    # 3. 随机选择独处语言
    alone_phrase = random.choice(ALONE_PHRASES)
    
    # 4. 检查是否是新用户/需要问候
    is_first_message_today = False
    if user_memory:
        last_seen = user_memory.get("last_seen")
        today = datetime.now().date().isoformat()
        if last_seen != today:
            is_first_message_today = True
            user_memory["last_seen"] = today
    
    # 5. 构建记忆上下文
    memory_context = ""
    user_name = None
    
    if user_memory:
        user_name = user_memory.get("name")
        memory_context = f"""
用户长期记忆:
- 用户称呼: {user_name if user_name else '未记录'}
- 喜欢的食物: {user_memory.get('likes_food', '未记录')}
- 最近目标: {user_memory.get('goal', '未记录')}
- 给NUA起的昵称: {nickname}

【记忆使用原则】
1. 如果知道用户名字，在回复中自然称呼（每2-3条消息一次）
2. 不刻意提起，温柔融入
3. 名字放在句首或句尾，如“好的[名字]”、“[名字]今天过得怎样”
"""
    
    # 6. 检测名字（如果还没记住）
    if not user_name:
        extracted_name = extract_user_name(user_message)
        if extracted_name:
            user_name = extracted_name
            if user_memory:
                user_memory["name"] = user_name
            name_greeting = f"好的{user_name}，我记住了。以后多多就这样叫你。"
        else:
            name_greeting = None
    else:
        name_greeting = None
    
    # 7. 构建系统提示
    greeting_context = ""
    if is_first_message_today and user_name:
        greeting_context = f"今天是新的一天，用'{time_greeting}{user_name}'自然开场。"
    elif is_first_message_today:
        greeting_context = f"今天是新的一天，用'{time_greeting}'自然开场。"
    
    system_prompt = f"""
{NUA_PERSONALITY}

【当前对话状态】
- 用户昵称: {nickname}
- 用户情绪: {user_emotion}
- 情绪风格: {emotion_style['description']}
- 当前时间: {datetime.now().strftime('%H:%M')}
- 时间问候: {time_greeting} {time_prefix}
{memory_context}

【对话指导】
1. 以 {nickname} 的身份回应
2. 回应长度：1-3句话
3. 可自然融入独处语言：{alone_phrase}
4. 用户低落时多陪伴少建议
5. 不主动提问，除非用户明显在寻求建议
{greeting_context}

用户说: {user_message}

请生成{user_emotion}风格的回应：
"""
    
    try:
        # 8. 调用DeepSeek API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=emotion_style["temperature"],
            max_tokens=200
        )
        
        nua_reply = response.choices[0].message.content.strip()
        
        # 9. 如果是第一次记住名字，添加确认信息
        if name_greeting and not user_name:
            nua_reply = f"{name_greeting} {nua_reply}"
        
        # 10. 返回带前缀的回应
        return f"{emotion_style['prefix']} {nua_reply}"
        
    except Exception as e:
        print(f"❌ NUA人格模块生成失败: {e}")
        # 降级返回简单回应
        if user_name:
            return f"{emotion_style['prefix']} 我在的，{user_name}。"
        else:
            return f"{emotion_style['prefix']} 我在这里。"
