import streamlit as st
from ai import generate_answer, synthesize_speech,image_gen
import json

if "book" not in st.session_state:
    st.session_state.book = []


# ========== 页面配置 ==========

st.title("📚 AI有声绘本创作")
st.markdown("让我们一起用AI创作一个会讲故事的绘本！")

# ========== 用户输入绘本主题与设置 ==========
st.subheader("输入绘本主题与设置")
book_theme = st.text_input("请输入你的绘本主题或故事梗概：", "一只想飞上天的小猪")
page_count = st.slider("请选择绘本页数：", min_value=1, max_value=10, value=4)
style_option = st.selectbox("请选择绘本插图风格：", ["儿童插画风", "水彩风", "像素风", "手绘涂鸦风", "未来幻想风"])
voice_option = st.selectbox("请选择朗读声音：", ["longwan_v2", "longcheng_v2", "longhua_v2"])
book_language = st.selectbox("请选择绘本语言：", ["中文", "英文"])

# ========== 点击生成按钮 ==========
generate_button = st.button("📖 生成绘本内容")

# ========== 调用大模型生成结构化绘本内容 ==========
if generate_button and book_theme:
    prompt = f"""请根据以下主题，以{book_language}作一个童话故事，分成 {page_count} 页。
    每一页都包含一个用于生成图像的提示词(prompt)，以及一段适合语音朗读的文本(text)。一切使用{book_language}
    绘本主题：{book_theme}
    图像生成提示词要加入风格说明：{style_option}
    绘本语言: {book_language}，请按照{book_language}语言生成内容，不要出现任何其他语言
    请以JSON数组形式输出结果，格式示例如下：
    [
    {{"prompt": "提示词内容", "text": "朗读内容"}},
    {{"prompt": "提示词内容", "text": "朗读内容"}},
    ]
    """
    with st.spinner("正在生成绘本结构..."):
        json_str = generate_answer(prompt, output_json=True)
        print(json_str)
        st.success("绘本结构生成完成！")
    try:
        pages = json.loads(json_str) 
        progress_bar = st.progress(0,"正在生成图片和声音...")
        total = len(pages)
        for i, page in enumerate(pages):
            #st.markdown(f"### 📖 第{i+1}页")
            
            image_path = f"page_{i+1}.png"
            image_gen(page["prompt"], image_path)
            #st.image(image_path, caption=page["text"], use_container_width =True)

            audio_path = synthesize_speech(page["text"], voice_id=voice_option)
            #st.audio(audio_path, format="audio/wav")

            st.session_state["book"].append({
                "text": page["text"],
                "image": image_path,
                "audio": audio_path
            })
            progress_bar.progress((i + 1) / total,f"第{i+1}页完成")

        st.session_state["current_page"] = 0
        st.success("绘本图片和声音生成完成！")

    except Exception as e:
        st.error("生成失败，请检查大模型输出格式。")
        st.code(json_str)

def go_prev():
    if st.session_state["current_page"] > 0:
        st.session_state["current_page"] -= 1

def go_next():
    if st.session_state["current_page"] < len(st.session_state["book"]) - 1:
        st.session_state["current_page"] += 1

'''

'''

# ========== 翻页展示 ==========
if st.session_state["book"]:
    total_pages = len(st.session_state["book"])
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = 0

    current = st.session_state["current_page"]
    page = st.session_state["book"][current]

    st.markdown(f"##### 📖 第 {current + 1} 页 / 共 {total_pages} 页")
    st.image(page["image"], caption=page["text"], use_container_width=True)
    st.audio(page["audio"], format="audio/wav")

    col1, col2 = st.columns(2)
    with col1:
        st.button("⬅️ 上一页", on_click=go_prev,use_container_width=True)
    with col2:
        st.button("➡️ 下一页", on_click=go_next,use_container_width=True)