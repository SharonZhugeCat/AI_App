import streamlit as st
import requests
import time
import tempfile
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from openai import OpenAI

# ========== 配置常量 ==========
API_KEY = st.secrets["DASHSCOPE_API_KEY"]
TTS_MODEL = "cosyvoice-v2"
VOICE_ID = "longwan_v2"
MODEL = "qwen-max"

# ========== 初始化客户端 ==========
dashscope.api_key = API_KEY
llm_client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ========== 工具函数定义 ==========

def recognize_speech(audio_path: str) -> str:
    messages = [{"role": "user", "content": [{"audio": audio_path}]}]
    response = dashscope.MultiModalConversation.call(
        model="qwen-audio-asr",
        messages=messages,
        result_format="message"
    )
    return response.output.choices[0].message.content[0]['text']

def generate_answer(prompt: str, output_json=False) -> str:
    sys_promt = "回答内容不要超过1000字。"
    messages = [
        {"role": "system", "content": sys_promt},
        {"role": "user", "content": prompt}]
    if output_json:
        response = llm_client.chat.completions.create(
                model= MODEL,
                response_format={"type": "json_object"},
                messages = messages)
    else:
        response = llm_client.chat.completions.create(
                    model= MODEL,
                    messages = messages)
    return(response.choices[0].message.content)

def write_temp_audio(audio_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_bytes)
        return tmp_file.name

def save_audio_input(audio_data) -> str:
    return write_temp_audio(audio_data.getvalue())

def synthesize_speech(text: str, voice_id: str = VOICE_ID) -> str:
    synthesizer = SpeechSynthesizer(model=TTS_MODEL, voice=voice_id)
    audio = synthesizer.call(text)
    return write_temp_audio(audio)


# ===== 1. 提交异步任务 =====
def submit_task_gen(prompt, size="1024*1024", n=1,model="wanx2.0-t2i-turbo"):
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": n}
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    task_id = response.json()["output"]["task_id"]
    print(f"提交成功，任务ID: {task_id}")
    return task_id, headers

# ===== 2. 轮询任务状态 =====
def poll_task_result(task_id, headers, max_retries=20, interval=5):
    task_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    for attempt in range(max_retries):
        response = requests.get(task_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        task_status = data.get("output", {}).get("task_status")
        print(f"第 {attempt + 1} 次检查，状态: {task_status}")
        if task_status == "SUCCEEDED":
            return data["output"]["results"]
        elif task_status in ["FAILED", "CANCELLED"]:
            raise Exception(f"任务失败，状态: {task_status}")
        time.sleep(interval)
    raise TimeoutError("等待任务超时，请稍后再试")

# ===== 3. 下载图片结果 =====
def download_images(results, output_file="output.png"):
    for result in results:
        url = result["url"]
        img_data = requests.get(url).content
        with open(output_file, "wb") as f:
            f.write(img_data)
        print(f"图片已保存为: {output_file}")


def image_gen(prompt, file_name, size="1024*1024", n=1):
    task_id, headers = submit_task_gen(prompt, size, n)
    results = poll_task_result(task_id, headers)
    download_images(results, file_name)
    return True