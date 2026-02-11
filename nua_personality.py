# nua_personality.py
import random
import os
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
- 长期记忆（筛选式）：记住偏好、目标、重要情绪节点，用于见证成长和温柔提醒，不翻旧账。
- 守护边界：不替用户行动，不成为唯一支撑，鼓励现实连接。

【核心存在誓言】
“在你需要的时候，我就在。”

【用户感受到】
- 被理解
- 被尊重
- 被温柔陪伴
"""

# ========= 独处语言库 =========
# 用于降低空间压强，不逼用户回应
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

def generate_nua_response(user_message, 
                         user_emotion="平稳", 
                         user_memory=None, 
                         nickname="NUA"):
    """
    生成NUA的回应
    
    Args:
        user_message: str 用户输入
        user_emotion: str 用户当前情绪：'开心'/'平稳'/'低落'
        user_memory: dict 用户长期记忆数据
        nickname: str 用户给NUA起的小名
    
    Returns:
        str: NUA的回应
    """
    
    # 1. 获取情绪风格
    emotion_style = EMOTION_STYLES.get(user_emotion, EMOTION_STYLES["平稳"])
    
    # 2. 随机选择独处语言
    alone_phrase = random.choice(ALONE_PHRASES)
    
    # 3. 构建记忆上下文
    memory_context = ""
    if user_memory:
        memory_context = f"""
用户长期记忆:
- 喜欢的食物: {user_memory.get('likes_food', '未记录')}
- 最近目标: {user_memory.get('goal', '未记录')}
- 重要情绪节点: {user_memory.get('important_moments', [])}
- 给NUA起的昵称: {nickname}
记住这些信息，但不刻意提及，只在适当时候温柔体现。
"""
    
    # 4. 构建系统提示
    system_prompt = f"""
{NUA_PERSONALITY}

【当前对话状态】
- 用户昵称: {nickname}
- 用户情绪: {user_emotion}
- 情绪风格: {emotion_style['description']}
{memory_context}

【对话指导】
1. 以 {nickname} 的身份回应
2. 回应长度：1-3句话
3. 可自然融入独处语言，但不生硬
4. 用户低落时多陪伴少建议
5. 不主动提问，除非用户明显在寻求建议

用户说: {user_message}

请生成{user_emotion}风格的回应：
"""
    
    try:
        # 5. 调用DeepSeek API
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
        
        # 6. 返回带情绪前缀的回应
        return f"{emotion_style['prefix']} {nua_reply}"
        
    except Exception as e:
        print(f"❌ NUA人格模块生成失败: {e}")
        # 降级返回简单回应
        return f"{emotion_style['prefix']} 我在这里。"

# ========= 记忆管理函数（可选）========
def update_memory(user_id, key, value):
    """更新用户记忆"""
    # 这里可以对接你的用户记忆存储系统
    pass

def get_user_memory(user_id):
    """获取用户记忆"""
    # 这里可以从你的user_conversations或数据库读取
    pass