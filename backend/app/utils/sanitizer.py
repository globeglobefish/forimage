"""
文本安全处理工具
防止XSS、SQL注入等安全问题
"""

import re
import html
from typing import Optional


# 危险HTML标签
DANGEROUS_TAGS = [
    'script', 'iframe', 'object', 'embed', 'form', 'input', 'button',
    'textarea', 'select', 'style', 'link', 'meta', 'base', 'applet',
    'frame', 'frameset', 'layer', 'ilayer', 'bgsound', 'marquee'
]

# 危险属性
DANGEROUS_ATTRS = [
    'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover',
    'onmousemove', 'onmouseout', 'onkeypress', 'onkeydown', 'onkeyup',
    'onfocus', 'onblur', 'onchange', 'onsubmit', 'onreset', 'onselect',
    'onload', 'onunload', 'onerror', 'onabort', 'onresize', 'onscroll',
    'javascript:', 'vbscript:', 'data:', 'expression'
]


def sanitize_text(text: Optional[str], max_length: int = 500, escape_html: bool = True) -> Optional[str]:
    """
    清理文本输入，防止XSS攻击
    
    Args:
        text: 输入文本
        max_length: 最大长度限制
        escape_html: 是否进行HTML转义（存储到数据库通常不需要，由前端框架处理）
        
    Returns:
        清理后的安全文本
    """
    if text is None:
        return None
    
    if not isinstance(text, str):
        text = str(text)
    
    # 1. 去除首尾空白
    text = text.strip()
    
    # 2. 限制长度
    if len(text) > max_length:
        text = text[:max_length]
    
    # 3. 去除控制字符（除了换行和制表符）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 4. 规范化空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 5. 可选：HTML实体编码（防止XSS）
    # 注意：对于存储到数据库的文本，通常不需要转义，由前端框架自动处理
    if escape_html:
        text = html.escape(text, quote=True)
    
    return text if text else None


def sanitize_html(html_content: Optional[str], max_length: int = 10000) -> Optional[str]:
    """
    清理HTML内容，移除危险标签和属性
    用于允许部分HTML的场景（如富文本）
    
    Args:
        html_content: HTML内容
        max_length: 最大长度限制
        
    Returns:
        清理后的安全HTML
    """
    if html_content is None:
        return None
    
    if not isinstance(html_content, str):
        html_content = str(html_content)
    
    # 限制长度
    if len(html_content) > max_length:
        html_content = html_content[:max_length]
    
    # 移除危险标签
    for tag in DANGEROUS_TAGS:
        pattern = re.compile(rf'<{tag}[^>]*>.*?</{tag}>', re.IGNORECASE | re.DOTALL)
        html_content = pattern.sub('', html_content)
        # 移除自闭合标签
        pattern = re.compile(rf'<{tag}[^>]*/?\s*>', re.IGNORECASE)
        html_content = pattern.sub('', html_content)
    
    # 移除危险属性
    for attr in DANGEROUS_ATTRS:
        pattern = re.compile(rf'\s*{attr}\s*=\s*["\'][^"\']*["\']', re.IGNORECASE)
        html_content = pattern.sub('', html_content)
        pattern = re.compile(rf'\s*{attr}\s*=\s*[^\s>]+', re.IGNORECASE)
        html_content = pattern.sub('', html_content)
    
    # 移除 javascript: 伪协议
    html_content = re.sub(r'javascript\s*:', '', html_content, flags=re.IGNORECASE)
    
    # 移除 data: 伪协议（可能包含恶意内容）
    html_content = re.sub(r'data\s*:[^,]*,', '', html_content, flags=re.IGNORECASE)
    
    return html_content.strip() if html_content.strip() else None


def sanitize_filename(filename: Optional[str], max_length: int = 200) -> Optional[str]:
    """
    清理文件名，移除危险字符
    
    Args:
        filename: 文件名
        max_length: 最大长度
        
    Returns:
        安全的文件名
    """
    if filename is None:
        return None
    
    if not isinstance(filename, str):
        filename = str(filename)
    
    # 移除路径分隔符和危险字符
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*', '\x00']
    for char in dangerous_chars:
        filename = filename.replace(char, '')
    
    # 去除首尾空白和点
    filename = filename.strip().strip('.')
    
    # 限制长度
    if len(filename) > max_length:
        # 保留扩展名
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            max_name_len = max_length - len(ext) - 1
            filename = name[:max_name_len] + '.' + ext
        else:
            filename = filename[:max_length]
    
    return filename if filename else None


def validate_and_sanitize_title(title: Optional[str]) -> Optional[str]:
    """
    验证并清理图片标题
    
    存储到数据库的标题不进行HTML转义，因为：
    1. 前端框架（Vue/React等）会自动对文本进行转义
    2. 保持原始文本便于搜索和显示
    
    Args:
        title: 用户输入的标题
        
    Returns:
        清理后的安全标题，或 None
    """
    if title is None:
        return None
    
    # 清理文本（不进行HTML转义，由前端处理）
    title = sanitize_text(title, max_length=200, escape_html=False)
    
    if not title:
        return None
    
    # 额外检查：必须包含至少一个字母、数字或中文字符
    if not re.search(r'[\w\u4e00-\u9fff]', title):
        return None
    
    return title


def is_safe_url(url: Optional[str]) -> bool:
    """
    检查URL是否安全
    
    Args:
        url: URL字符串
        
    Returns:
        是否安全
    """
    if not url:
        return False
    
    url_lower = url.lower().strip()
    
    # 检查危险协议
    dangerous_protocols = ['javascript:', 'vbscript:', 'data:', 'file:']
    for proto in dangerous_protocols:
        if url_lower.startswith(proto):
            return False
    
    return True
