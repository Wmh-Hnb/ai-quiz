import json
import base64
import io
import time
import copy
import requests
import importlib
from typing import Any
from utils.db import get_settings_path

genai: Any = importlib.import_module("google.generativeai")

DEFAULT_SETTINGS = {
    "provider": "gemini",
    "gemini": {
        "api_key": "",
        "model": "gemini-2.5-flash"
    },
    "glm": {
        "api_key": "",
        "model": "glm-4.7"
    },
    "nvidia": {
        "api_key": "",
        "model": "z-ai/glm4.7"
    },
    "deepseek": {
        "api_key": "",
        "model": "deepseek-chat"
    }
}

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


def load_settings() -> dict:
    path = get_settings_path()
    if not path.exists():
        return copy.deepcopy(DEFAULT_SETTINGS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        merged = copy.deepcopy(DEFAULT_SETTINGS)
        merged.update({k: v for k, v in data.items() if k in merged})
        merged["gemini"].update(data.get("gemini", {}))
        merged["glm"].update(data.get("glm", {}))
        merged["nvidia"].update(data.get("nvidia", {}))
        return merged
    except Exception:
        return copy.deepcopy(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    path = get_settings_path()
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def get_active_provider() -> str:
    return load_settings().get("provider", "gemini")


def get_provider_with_key(preferred: str | None = None) -> str | None:
    settings = load_settings()
    order = []
    if preferred:
        order.append(preferred)
    order.extend(["gemini", "glm", "nvidia", "deepseek"])
    seen = set()
    for provider in order:
        if provider in seen:
            continue
        seen.add(provider)
        key = settings.get(provider, {}).get("api_key", "")
        if key:
            return provider
    return None


def get_gemini_config() -> dict:
    return load_settings().get("gemini", {})


def get_glm_config() -> dict:
    return load_settings().get("glm", {})


def get_nvidia_config() -> dict:
    return load_settings().get("nvidia", {})


def get_deepseek_config() -> dict:
    return load_settings().get("deepseek", {})


GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


def get_model(model_name: str | None = None):
    gemini_cfg = get_gemini_config()
    api_key = gemini_cfg.get("api_key", "")
    model = model_name or gemini_cfg.get("model", "gemini-2.5-flash")
    if api_key:
        genai.configure(api_key=api_key)
    return genai.GenerativeModel(model)


def glm_generate_from_messages(messages: list[dict], model: str | None = None) -> str:
    glm_cfg = get_glm_config()
    api_key = glm_cfg.get("api_key", "")
    model_name = model or glm_cfg.get("model", "glm-4.7")
    if not api_key:
        raise ValueError("未配置 GLM API Key")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False
    }
    response = requests.post(f"{GLM_BASE_URL}/chat/completions", json=payload, headers=headers)
    if not response.ok:
        raise ValueError(f"GLM 请求失败: {response.status_code} {response.text}")
    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("GLM 返回内容为空")
    return choices[0].get("message", {}).get("content", "")


def glm_generate_content(prompt: str) -> str:
    return glm_generate_from_messages([{"role": "user", "content": prompt}])


def nvidia_generate_from_messages(messages: list[dict], model: str | None = None) -> str:
    nv_cfg = get_nvidia_config()
    api_key = nv_cfg.get("api_key", "")
    model_name = model or nv_cfg.get("model", "z-ai/glm4.7")
    if not api_key:
        raise ValueError("未配置 NVIDIA API Key")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False
    }
    response = requests.post(f"{NVIDIA_BASE_URL}/chat/completions", json=payload, headers=headers)
    if not response.ok:
        raise ValueError(f"NVIDIA 请求失败: {response.status_code} {response.text}")
    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("NVIDIA 返回内容为空")
    return choices[0].get("message", {}).get("content", "")


def nvidia_generate_content(prompt: str) -> str:
    return nvidia_generate_from_messages([{"role": "user", "content": prompt}])


def deepseek_generate_from_messages(messages: list[dict], model: str | None = None) -> str:
    ds_cfg = get_deepseek_config()
    api_key = ds_cfg.get("api_key", "")
    model_name = model or ds_cfg.get("model", "deepseek-chat")
    if not api_key:
        raise ValueError("未配置 DeepSeek API Key")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False
    }
    response = requests.post(f"{DEEPSEEK_BASE_URL}/chat/completions", json=payload, headers=headers)
    if not response.ok:
        raise ValueError(f"DeepSeek 请求失败: {response.status_code} {response.text}")
    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("DeepSeek 返回内容为空")
    return choices[0].get("message", {}).get("content", "")


def deepseek_generate_content(prompt: str) -> str:
    return deepseek_generate_from_messages([{"role": "user", "content": prompt}])


def generate_text(prompt: str) -> str:
    provider = get_provider_with_key(get_active_provider())
    if provider == "glm":
        return glm_generate_content(prompt)
    if provider == "nvidia":
        return nvidia_generate_content(prompt)
    if provider == "deepseek":
        return deepseek_generate_content(prompt)
    if provider == "gemini":
        model = get_model()
        response = model.generate_content(prompt)
        return response.text
    raise ValueError("未配置任何可用的 API Key")


def summarize_wrong_questions(wrong_items: list[dict]) -> dict:
    if not wrong_items:
        return {"error": "暂无错题"}

    lines = []
    for idx, item in enumerate(wrong_items[:30], start=1):
        question = item.get("question")
        if not question:
            continue
        lines.append(
            f"{idx}. 类型:{question.type} 分类:{question.category or '未分类'} 题目:{question.content} 标准答案:{question.answer} 你的答案:{item.get('user_answer', '')}"
        )

    prompt = (
        "你是动物医学学习助手，请根据错题列表生成错题总结。\n"
        "要求：\n"
        "1. 总结主要错误类型和高频失误\n"
        "2. 给出总体改进建议\n"
        "3. 输出清晰条目，使用中文\n"
    )

    try:
        summary = generate_text(prompt + "\n错题列表：\n" + "\n".join(lines))
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}


def summarize_weak_points(wrong_items: list[dict]) -> dict:
    if not wrong_items:
        return {"error": "暂无错题"}

    category_counts = {}
    type_counts = {}
    for item in wrong_items:
        question = item.get("question")
        if not question:
            continue
        category = question.category or "未分类"
        qtype = question.type or "未知"
        weight = item.get("wrong_count", 1)
        category_counts[category] = category_counts.get(category, 0) + weight
        type_counts[qtype] = type_counts.get(qtype, 0) + weight

    def format_counts(counts: dict, limit: int = 6) -> str:
        items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return "\n".join([f"- {name}: {count}" for name, count in items])

    stats_text = (
        "错题统计：\n"
        f"按分类：\n{format_counts(category_counts)}\n"
        f"按题型：\n{format_counts(type_counts)}\n"
    )

    samples = []
    for item in sorted(wrong_items, key=lambda x: x.get("wrong_count", 1), reverse=True)[:15]:
        question = item.get("question")
        if not question:
            continue
        samples.append(f"- {question.type} | {question.category or '未分类'} | {question.content}")

    prompt = (
        "你是动物医学学习助手，请根据错题统计生成薄弱知识点总结。\n"
        "要求：\n"
        "1. 指出最薄弱的知识点/学科方向\n"
        "2. 解释可能原因\n"
        "3. 给出复习建议和优先级\n"
        "4. 输出清晰条目，使用中文\n"
    )

    try:
        summary = generate_text(prompt + "\n" + stats_text + "\n高频错题样例：\n" + "\n".join(samples))
        return {"summary": summary}
    except Exception as e:
        return {"error": str(e)}


PARSE_QUESTIONS_PROMPT = """你是一个专业的动物医学试题解析助手。请分析上传的文档/图片，识别其中的所有题目。

请按照以下 JSON 格式输出每道题目：
```json
{
  "questions": [
    {
      "type": "题目类型",
      "content": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "标准答案",
      "keywords": ["关键词1", "关键词2"],
      "explanation": "解析（如果有）",
      "difficulty": 1,
      "category": "学科分类"
    }
  ]
}
```

题目类型只能是以下八种之一：
- 名词解释
- 单选题
- 多选题
- 填空题
- 简答题
- 论述题
- 判断题
- 病例分析题

学科分类请从以下选择（动物医学领域）：
- 动物解剖学
- 动物生理学
- 动物生物化学
- 动物病理学
- 兽医药理学
- 兽医微生物学
- 兽医寄生虫学
- 兽医传染病学
- 兽医内科学
- 兽医外科学
- 兽医产科学
- 中兽医学
- 动物营养学
- 其他

难度等级：1=简单，2=中等，3=困难

注意事项：
1. 如果题目没有明确答案，请根据动物医学专业知识给出标准答案
2. options 字段只有单选题、多选题、判断题需要填写，其他题型留空数组 []。判断题的 options 为 ["对", "错"]
3. 填空题的答案用逗号分隔多个空的答案
4. 请确保输出是有效的 JSON 格式
5. 只输出 JSON，不要有其他内容"""


GENERATE_QUESTIONS_PROMPT = """你是一个专业的动物医学出题专家。请根据给定的关键词生成高质量的试题。

关键词：{keywords}

要求生成的题目数量和类型：
{requirements}

请按照以下 JSON 格式输出：
```json
{{
  "questions": [
    {{
      "type": "题目类型",
      "content": "题目内容",
      "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
      "answer": "标准答案",
      "keywords": ["关键词1", "关键词2"],
      "explanation": "详细解析",
      "difficulty": 2,
      "category": "学科分类"
    }}
  ]
}}
```

题目类型：名词解释、单选题、多选题、填空题、简答题、论述题、判断题、病例分析题

要求：
1. 题目必须是动物医学专业领域的
2. 答案必须准确、专业
3. 解析要详细，有助于学习
4. 难度要适中，符合兽医专业考试水平
5. 只输出 JSON，不要有其他内容"""


GRADE_ANSWER_PROMPT = """你是一个专业的动物医学阅卷老师。请评判学生的答案。

题目类型：{question_type}
题目：{question}
标准答案：{standard_answer}
学生答案：{user_answer}

请按照以下 JSON 格式输出评分结果：
```json
{{
  "is_correct": true或false,
  "score": 0-100的分数,
  "feedback": "详细的评语和解析",
  "key_points_hit": ["答对的要点1", "答对的要点2"],
  "key_points_missed": ["遗漏的要点1", "遗漏的要点2"]
}}
```

评分标准：
- 名词解释：核心概念准确得 60 分，表述完整得 40 分
- 单选题：完全正确 100 分，错误 0 分
- 多选题：全部选项正确 100 分，部分正确按比例计分，多选/漏选扣分
- 判断题：正确 100 分，错误 0 分
- 填空题：每空平均分，答对一空得相应分数
- 简答题：按要点给分，表述专业性占 20%
- 论述题：论点 30%，论据 40%，逻辑性 20%，专业表述 10%
- 病例分析题：诊断正确 30%，分析过程 30%，治疗方案 20%，专业表述 20%

只输出 JSON，不要有其他内容"""


def extract_json(text: str) -> dict:
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    
    if json_start != -1 and json_end > json_start:
        json_str = text[json_start:json_end]
        return json.loads(json_str)
    
    return {"error": "无法解析返回结果", "raw": text}


def extract_text_from_docx(file_bytes: bytes) -> str:
    import zipfile
    from xml.etree import ElementTree

    with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
        with zf.open("word/document.xml") as doc_xml:
            tree = ElementTree.parse(doc_xml)

    texts = []
    for node in tree.iter():
        if node.tag.endswith("}t") and node.text:
            texts.append(node.text)
    return "\n".join(texts)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import importlib

    PdfReader = importlib.import_module("PyPDF2").PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    texts = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            texts.append(page_text)
    return "\n".join(texts)


def parse_questions_from_file(file_bytes: bytes, file_type: str) -> dict:
    file_type = file_type.lower()
    provider = get_provider_with_key(get_active_provider())

    if not provider:
        return {"error": "未配置任何可用的 API Key"}

    if file_type == "docx":
        try:
            text = extract_text_from_docx(file_bytes)
            if not text.strip():
                return {"error": "Word文档内容为空"}
            return parse_questions_from_text(text)
        except Exception as e:
            return {"error": f"解析Word文档失败: {str(e)}"}

    if provider in ("glm", "nvidia"):
        if file_type == "pdf":
            try:
                text = extract_text_from_pdf(file_bytes)
                if not text.strip():
                    return {"error": "PDF文档内容为空"}
                return parse_questions_from_text(text)
            except Exception as e:
                return {"error": f"解析PDF失败: {str(e)}"}
        if file_type in ("png", "jpg", "jpeg"):
            try:
                image_b64 = base64.b64encode(file_bytes).decode("utf-8")
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PARSE_QUESTIONS_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{file_type};base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ]
                if provider == "glm":
                    result = glm_generate_from_messages(messages)
                else:
                    result = nvidia_generate_from_messages(messages)
                return extract_json(result)
            except Exception as e:
                return {"error": str(e)}
        return {"error": "当前模型暂不支持该文件类型"}

    model = get_model()

    mime_type_map = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }

    mime_type = mime_type_map.get(file_type, "application/octet-stream")

    file_data = {
        "mime_type": mime_type,
        "data": base64.standard_b64encode(file_bytes).decode("utf-8")
    }

    try:
        response = model.generate_content([
            PARSE_QUESTIONS_PROMPT,
            file_data
        ])
        return extract_json(response.text)
    except Exception as e:
        return {"error": str(e)}


def parse_questions_from_text(text: str) -> dict:
    prompt = PARSE_QUESTIONS_PROMPT + f"\n\n以下是需要解析的文本内容：\n\n{text}"
    
    try:
        response_text = generate_text(prompt)
        return extract_json(response_text)
        
    except Exception as e:
        return {"error": str(e)}


def generate_questions(keywords: str, requirements: dict) -> dict:
    req_text = "\n".join([
        f"- {q_type}：{count} 道"
        for q_type, count in requirements.items()
        if count > 0
    ])
    
    prompt = GENERATE_QUESTIONS_PROMPT.format(
        keywords=keywords,
        requirements=req_text if req_text else "每种题型各 2 道"
    )
    
    try:
        response_text = generate_text(prompt)
        return extract_json(response_text)
        
    except Exception as e:
        return {"error": str(e)}


def grade_answer(question_type: str, question: str, standard_answer: str, user_answer: str) -> dict:
    prompt = GRADE_ANSWER_PROMPT.format(
        question_type=question_type,
        question=question,
        standard_answer=standard_answer,
        user_answer=user_answer
    )
    
    try:
        response_text = generate_text(prompt)
        return extract_json(response_text)
        
    except Exception as e:
        return {"error": str(e)}


def check_api_key() -> bool:
    provider = get_provider_with_key(get_active_provider())
    if not provider:
        return False
    try:
        if provider == "glm":
            _ = glm_generate_content("你好")
            return True
        if provider == "nvidia":
            _ = nvidia_generate_content("你好")
            return True
        if provider == "deepseek":
            _ = deepseek_generate_content("你好")
            return True
        model = get_model()
        model.generate_content("你好")
        return True
    except Exception:
        return False
