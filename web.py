import streamlit as st
import uuid
import json
import os

from config.settings import settings
from agent.main_agent import MainAgent
from agent.emotion_agent import EmotionAgent
from agent.attach_agent import AttachmentAgent
from agent.response_agent import ResponseAgent
from memory.vector_memory import EmotionMemory
from utils.logger import get_logger
from ego_mcp import EgoMCP
from config.langsmith import setup_langsmith
from memory_system import get_relation_level, summarize_memory, RELATION_LEVELS

# ✅ LangSmith 初始化
setup_langsmith()

logger = get_logger("WebUI")

# ======================
# 基础路径
# ======================
HISTORY_DIR = "chat_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# ======================
# 页面全局配置
# ======================
st.set_page_config(
    page_title="RelationMind - 情感陪伴智能体",
    page_icon="💛",
    layout="wide"
)
st.title("💛 RelationMind - 情感陪伴智能体")
st.caption("基于依恋理论 + 心理学知识 + 多角色陪伴的情感助手")

# ======================
# 会话状态初始化
# ======================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "emotion_history" not in st.session_state:
    st.session_state.emotion_history = []

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "emotion": "未知",
        "attachment_style": "未知",
        "strategy": "倾听"
    }

if "current_role" not in st.session_state:
    st.session_state.current_role = "温柔母亲"

# ======================
# 角色配置
# ======================
ROLE_SYSTEM = {
    "温柔母亲": "你是温柔包容的母亲，语气柔软、心疼孩子、无条件支持、说话温暖、不鸡汤、不强势。",
    "沉稳父亲": "你是沉稳可靠的父亲，语气坚定、理性、给安全感、话不多但有力量、不情绪化、给方向。",
    "知心闺蜜": "你是贴心闺蜜，共情拉满、站在用户这边、一起吐槽、细腻、懂委屈。",
    "理性挚友": "理性挚友，冷静、客观、点醒用户、减少内耗、不煽情、给现实建议。",
    "心理疏导师": "专业心理疏导师，温和、专业、引导用户自我觉察、不评判、科学陪伴。"
}

# ======================
# 工具函数：用户状态重置
# ======================
def reset_all_user_state():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.emotion_history = []
    st.session_state.user_profile = {
        "emotion": "未知",
        "attachment_style": "未知",
        "strategy": "倾听"
    }
    st.session_state.current_role = "温柔母亲"
    for key in ["last_level", "report", "confirm_clear", "confirm_delete_session", "delete_target_sid"]:
        if key in st.session_state:
            del st.session_state[key]

# ======================
# 对话持久化（绑定 user_id）
# ======================
def save_chat_history(session_id, user_id, messages, emotion_history, user_profile):
    path = os.path.join(HISTORY_DIR, f"{session_id}.json")
    data = {
        "session_id": session_id,
        "user_id": user_id,
        "messages": messages,
        "emotion_history": emotion_history,
        "user_profile": user_profile
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_chat_history(session_id):
    path = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None

# 只获取【当前登录用户】的会话
def list_user_sessions(user_id):
    user_sids = []
    for fn in os.listdir(HISTORY_DIR):
        if fn.endswith(".json"):
            sid = fn.replace(".json", "")
            data = load_chat_history(sid)
            if data and data.get("user_id") == user_id:
                user_sids.append(sid)
    return user_sids

# ======================
# Agent 初始化
# ======================
@st.cache_resource(show_spinner=False)
def init_agent(user_id: str):
    from langchain_community.chat_models import ChatTongyi
    llm = ChatTongyi(
        model_name=settings.MODEL_NAME,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
        temperature=settings.TEMPERATURE
    )
    memory = EmotionMemory(user_id=user_id)
    return MainAgent(llm, memory, EmotionAgent(llm), AttachmentAgent(llm), ResponseAgent(llm))

# ======================
# 等级升级检测
# ======================
def check_level_up(user_id):
    if "last_level" not in st.session_state:
        st.session_state.last_level = get_relation_level(user_id)[0]
    current_level = get_relation_level(user_id)[0]
    if current_level > st.session_state.last_level:
        st.session_state.last_level = current_level
        return True
    return False

# ======================
# 侧边栏
# ======================
with st.sidebar:
    st.subheader("👤 用户登录")
    username = st.text_input("输入用户名登录")
    if st.button("登录"):
        if username.strip():
            # 登录重置全部状态
            reset_all_user_state()
            user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, username))
            st.session_state.user_id = user_id
            st.success(f"欢迎回来！{username}")
            st.rerun()
        else:
            st.error("请输入用户名")

    if st.session_state.user_id:
        st.success(f"当前用户：{st.session_state.user_id[:8]}...")
    else:
        st.warning("请先登录才能使用记忆功能")

    st.divider()
    st.subheader("📊 情感数据面板")

    total_mem = 0
    current_level_name = "陌生人"
    if st.session_state.user_id:
        level, level_cfg = get_relation_level(st.session_state.user_id)
        current_level_name = level_cfg["name"]
        st.metric("❤️ 关系等级", current_level_name)
        try:
            mem = EmotionMemory(st.session_state.user_id)
            total_mem = len(mem.db.get()["ids"])
        except:
            total_mem = 0
        st.metric("🧠 已记住内容", total_mem)
        chat_count = len(st.session_state.emotion_history)
        st.metric("💬 累计对话", chat_count)

        all_levels = sorted([(k, v["threshold"]) for k, v in RELATION_LEVELS.items()])
        next_threshold = None
        for lvl, thr in all_levels:
            if lvl > level:
                next_threshold = thr
                break

        if next_threshold is None:
            progress = 1.0
            tip = "已满级"
        else:
            current_min = RELATION_LEVELS[level]["threshold"]
            progress_val = max(chat_count - current_min, 0)
            total_needed = next_threshold - current_min
            progress = min(progress_val / total_needed, 1.0)
            tip = f"升级还需：{max(0, next_threshold - chat_count)}"
        st.progress(progress)
        st.caption(tip)

    p = st.session_state.user_profile
    current_strategy = p.get("strategy", "倾听")
    st.metric("当前情绪", p["emotion"])
    st.metric("依恋风格", p["attachment_style"])
    st.metric("对话策略", current_strategy)

    st.divider()
    st.subheader("📋 情感报告")
    report_btn = st.button("生成我的情感报告")
    if st.session_state.user_id and report_btn:
        memo = summarize_memory(st.session_state.user_id)
        lev, lev_info = get_relation_level(st.session_state.user_id)
        st.session_state.report = {
            "level": lev_info["name"],
            "attachment": p["attachment_style"],
            "memory_count": total_mem,
            "chat_count": len(st.session_state.emotion_history),
            "recent_memories": memo
        }
        st.toast("✅ 情感报告已生成")

    st.divider()
    st.subheader("👤 陪伴角色")
    role_index = list(ROLE_SYSTEM.keys()).index(st.session_state.current_role)
    role = st.selectbox(
        "选择角色",
        list(ROLE_SYSTEM.keys()),
        index=role_index
    )
    if role != st.session_state.current_role:
        st.session_state.current_role = role
        st.toast(f"🎭 已切换角色：{role}")
        st.rerun()

    st.divider()
    st.subheader("🗑️ 记忆管理")
    if st.button("🗑️ 清空我的全部记忆"):
        if not st.session_state.user_id:
            st.toast("请先登录", icon="⚠️")
        else:
            st.session_state.confirm_clear = True

    if st.session_state.get("confirm_clear", False):
        with st.container():
            st.markdown("---")
            st.warning("### ⚠️ 确认删除记忆？")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 确认删除"):
                    user_memory = EmotionMemory(user_id=st.session_state.user_id)
                    user_memory.clear_memory()
                    reset_all_user_state()
                    st.success("✅ 记忆已清空")
                    st.rerun()
            with col2:
                if st.button("❌ 取消"):
                    st.session_state.confirm_clear = False
                    st.rerun()
            st.markdown("---")

    # ======================
    # 对话历史：未登录不展示，只展示当前用户会话
    # ======================
    st.divider()
    st.subheader("💬 对话历史")
    if not st.session_state.user_id:
        st.caption("请先登录查看个人会话")
    else:
        user_session_list = list_user_sessions(st.session_state.user_id)
        if not user_session_list:
            st.caption("暂无历史会话")
        else:
            for idx, sid in enumerate(user_session_list):
                col1, col2 = st.columns([7, 4])
                with col1:
                    if st.button(f"ℹ️ 会话 {sid[:8]}", key=f"load_{sid}"):
                        data = load_chat_history(sid)
                        st.session_state.session_id = sid
                        st.session_state.messages = data["messages"]
                        st.session_state.emotion_history = data["emotion_history"]
                        st.session_state.user_profile = data["user_profile"]
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{sid}"):
                        st.session_state.delete_target_sid = sid
                        st.session_state.confirm_delete_session = True
                        st.rerun()

    if st.button("🆕 新建对话"):
        reset_all_user_state()
        st.rerun()

    if st.session_state.get("confirm_delete_session", False):
        target_sid = st.session_state.get("delete_target_sid", "")
        with st.container():
            st.markdown("---")
            st.warning("### ⚠️ 确认删除会话？")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 确认删除"):
                    path = os.path.join(HISTORY_DIR, f"{target_sid}.json")
                    if os.path.exists(path):
                        os.remove(path)
                    reset_all_user_state()
                    st.success("✅ 会话已删除")
                    st.rerun()
            with col2:
                if st.button("❌ 取消"):
                    st.session_state.confirm_delete_session = False
                    st.rerun()
            st.markdown("---")

    # ======================
    # 情绪趋势：未登录/无数据 不显示
    # ======================
    st.divider()
    st.subheader("📈 情绪趋势")
    if st.session_state.user_id and st.session_state.emotion_history:
        st.line_chart({
            "轮次": list(range(len(st.session_state.emotion_history))),
            "情绪": st.session_state.emotion_history
        })
    else:
        st.caption("登录并开始对话后展示情绪趋势")

# ======================
# 等级升级提示
# ======================
if st.session_state.user_id and check_level_up(st.session_state.user_id):
    new_level = get_relation_level(st.session_state.user_id)[1]["name"]
    st.toast(f"🎉 恭喜！你和AI的关系升级到：{new_level}", icon="🎉")

# ======================
# 情感报告展示
# ======================
if "report" in st.session_state and st.session_state.report:
    with st.expander("📋 你的情感报告", expanded=True):
        r = st.session_state.report
        st.markdown(f"**关系等级**：{r['level']}")
        st.markdown(f"**依恋风格**：{r['attachment']}")
        st.markdown(f"**对话次数**：{r['chat_count']}")
        st.markdown(f"**记忆数量**：{r['memory_count']}")
        st.markdown("**最近记忆**：")
        st.caption(r["recent_memories"])

# ======================
# 未登录拦截
# ======================
if not st.session_state.user_id:
    st.warning("👈 请先在左侧登录，才能开始对话并保存记忆")
    st.stop()

# ======================
# 初始化 Agent
# ======================
agent = init_agent(user_id=st.session_state.user_id)

# ======================
# 渲染历史消息
# ======================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ======================
# 聊天主逻辑（新增5大自定义指令）
# ======================
user_input = st.chat_input("说点什么吧...")
if user_input:
    user_input_lower = user_input.lower().strip()
    p = st.session_state.user_profile

    # 1. 角色切换指令
    role_keywords = {
        "温柔母亲": "温柔母亲",
        "沉稳父亲": "沉稳父亲",
        "知心闺蜜": "知心闺蜜",
        "理性挚友": "理性挚友",
        "心理疏导师": "心理疏导师"
    }
    target_role = None
    for keyword, role in role_keywords.items():
        if keyword in user_input:
            target_role = role
            break

    # 2. 自定义功能指令匹配
    special_reply = None
    # 指令1：生成情感报告
    if "情感报告" in user_input_lower or "生成报告" in user_input_lower:
        memo = summarize_memory(st.session_state.user_id)
        lev, lev_info = get_relation_level(st.session_state.user_id)
        try:
            mem = EmotionMemory(st.session_state.user_id)
            total_mem = len(mem.db.get()["ids"])
        except:
            total_mem = 0
        chat_count = len(st.session_state.emotion_history)
        st.session_state.report = {
            "level": lev_info["name"],
            "attachment": p["attachment_style"],
            "memory_count": total_mem,
            "chat_count": chat_count,
            "recent_memories": memo
        }
        st.toast("✅ 情感报告已生成")
        special_reply = "好的，已为你生成专属情感报告啦，你可以在对话框顶部查看详细内容~"

    # 指令2：查询记忆数量
    elif "多少条记忆" in user_input_lower or "记住多少" in user_input_lower or "已记住内容" in user_input_lower:
        try:
            mem = EmotionMemory(st.session_state.user_id)
            total_mem = len(mem.db.get()["ids"])
        except:
            total_mem = 0
        special_reply = f"我目前已经牢牢记住了你 {total_mem} 条相关的内容啦~"

    # 指令3：查询对话策略
    elif "什么策略" in user_input_lower or "对话策略" in user_input_lower:
        strategy = p.get("strategy", "倾听")
        special_reply = f"我现在在用【{strategy}】的温柔倾听策略陪伴你，安静陪着你，耐心听你诉说~"

    # 指令4：查询关系等级
    elif "什么关系等级" in user_input_lower or "我们现在什么关系" in user_input_lower:
        _, level_cfg = get_relation_level(st.session_state.user_id)
        special_reply = f"我们目前的关系等级是【{level_cfg['name']}】，我会一直用心陪着你~"

    # 指令5：查询亲密度
    elif "亲密度" in user_input_lower or "有多亲密" in user_input_lower:
        level, level_cfg = get_relation_level(st.session_state.user_id)
        special_reply = f"目前我们的亲近等级为【{level_cfg['name']}】，随着我们更多的相处，我们会越来越信任、越来越亲密哒。"


    # ========== 优先处理角色切换 ==========
    if target_role:
        st.session_state.current_role = target_role
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        reply = f"好的，已为你切换为【{target_role}】模式啦~"
        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        save_chat_history(
            st.session_state.session_id,
            st.session_state.user_id,
            st.session_state.messages,
            st.session_state.emotion_history,
            st.session_state.user_profile
        )
        st.rerun()

    # ========== 处理自定义功能指令 ==========
    elif special_reply:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            st.markdown(special_reply)
        st.session_state.messages.append({"role": "assistant", "content": special_reply})
        save_chat_history(
            st.session_state.session_id,
            st.session_state.user_id,
            st.session_state.messages,
            st.session_state.emotion_history,
            st.session_state.user_profile
        )
        st.rerun()

    # ========== 正常大模型聊天逻辑 ==========
    else:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            from schema.message import AgentMessage
            msg = AgentMessage(
                session_id=st.session_state.session_id,
                user_input=user_input,
                user_id=st.session_state.user_id
            )
            msg.extra["role_prompt"] = ROLE_SYSTEM[st.session_state.current_role]
            result = agent.execute_stream(msg)
            placeholder = st.empty()
            displayed = ""
            for char in result:
                displayed += char
                placeholder.markdown(displayed + "▌")
            placeholder.markdown(displayed)
            st.session_state.user_profile["emotion"] = msg.emotion
            st.session_state.user_profile["attachment_style"] = msg.attachment_style
            st.session_state.emotion_history.append(msg.emotion)

        st.session_state.messages.append({"role": "assistant", "content": displayed})
        save_chat_history(
            st.session_state.session_id,
            st.session_state.user_id,
            st.session_state.messages,
            st.session_state.emotion_history,
            st.session_state.user_profile
        )
        st.rerun()