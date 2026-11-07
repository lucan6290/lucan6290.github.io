"""User-local AI settings and the bounded Chat Completions client."""
import asyncio
import base64
import ctypes
from ctypes import wintypes
from dataclasses import dataclass, field
import hashlib
from ipaddress import ip_address
import json
import os
from pathlib import Path
import re
import tempfile
from threading import Lock
from urllib.parse import urlsplit

import httpx

from content_store import ContentError


REQUEST_TIMEOUT = 60
RESPONSE_LIMIT = 1024 * 1024
SETTINGS_LIMIT = 16 * 1024
KEY_PATTERN = re.compile(r"[!-~]{1,2048}")
WINDOWS_STORAGE = os.name == "nt"


def normalize_base_url(value: str) -> str:
    try:
        address = value.strip()
        parts = urlsplit(address)
        if (not parts.hostname or "@" in parts.netloc or "\\" in address
                or "?" in address or "#" in address or re.search(r"\s|[\x00-\x1f\x7f]", address)):
            raise ValueError
        if parts.scheme == "http":
            host = ip_address(parts.hostname)
            if not host.is_loopback or "%" in parts.hostname:
                raise ValueError
        elif parts.scheme != "https":
            raise ValueError
        if parts.port == 0:
            raise ValueError
        return str(httpx.URL(address)).rstrip("/")
    except (ValueError, httpx.InvalidURL):
        raise ContentError(400, "ai_invalid_endpoint", "请输入 HTTPS 服务地址，或使用 HTTP 的本机回环 IP。地址不能包含账号、查询参数或片段。") from None


class DataBlob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.c_void_p)]


def windows_protect(value: bytes, endpoint: str, *, decrypt: bool = False) -> bytes:
    if not WINDOWS_STORAGE:
        raise ContentError(400, "ai_windows_storage_unavailable", "此系统无法使用 Windows 密钥保护，请改用本次会话。")
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    local_free = ctypes.WinDLL("kernel32").LocalFree
    local_free.argtypes = [ctypes.c_void_p]
    local_free.restype = ctypes.c_void_p
    source = ctypes.create_string_buffer(value)
    # 将密文绑定到完整服务地址，避免把旧地址的密钥用于其它服务。
    entropy = ctypes.create_string_buffer(hashlib.sha256(endpoint.encode("utf-8")).digest())
    incoming = DataBlob(len(value), ctypes.addressof(source))
    binding = DataBlob(32, ctypes.addressof(entropy))
    outgoing = DataBlob()
    call = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    call.argtypes = [ctypes.POINTER(DataBlob), ctypes.c_void_p, ctypes.POINTER(DataBlob),
                     ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DataBlob)]
    call.restype = wintypes.BOOL
    try:
        # CRYPTPROTECT_UI_FORBIDDEN，默认使用当前 Windows 用户而非整台机器。
        if not call(ctypes.byref(incoming), None, ctypes.byref(binding), None, None, 1, ctypes.byref(outgoing)):
            raise ValueError("DPAPI")
        return ctypes.string_at(outgoing.data, outgoing.size)
    finally:
        ctypes.memset(source, 0, ctypes.sizeof(source))
        if outgoing.data:
            ctypes.memset(outgoing.data, 0, outgoing.size)
            local_free(outgoing.data)


@dataclass(frozen=True)
class Provider:
    base_url: str
    model: str
    api_key: str | None = field(repr=False)


class AiSettingsStore:
    def __init__(self, state_dir: Path):
        self.path = state_dir / "ai-settings.json"
        self.lock = Lock()
        self.session_key: tuple[str, str] | None = None

    def _read(self):
        try:
            with self.path.open("rb") as source:
                data = source.read(SETTINGS_LIMIT + 1)
            if len(data) > SETTINGS_LIMIT:
                raise ValueError
            settings = json.loads(data)
            if not isinstance(settings, dict) or any(not isinstance(value, str) for value in settings.values()):
                raise ValueError
            return settings
        except FileNotFoundError:
            return {}
        except (OSError, ValueError, RecursionError):
            raise ContentError(500, "ai_settings_read_failed", "无法读取 AI 设置，请检查本地状态文件。") from None

    def _write(self, settings):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent,
                                             prefix=".ai-settings-", delete=False) as output:
                temporary = Path(output.name)
                json.dump(settings, output, ensure_ascii=False)
            os.replace(temporary, self.path)
        except (OSError, UnicodeError):
            raise ContentError(500, "ai_settings_write_failed", "无法保存 AI 设置，请检查本地状态目录。") from None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _public(self, settings):
        base_url = settings.get("base_url", "")
        mode = "none"
        if self.session_key and self.session_key[0] == base_url:
            mode = "session"
        elif settings.get("windows_key"):
            mode = "windows"
        return {"base_url": base_url, "model": settings.get("model", ""),
                "key_mode": mode, "supports_windows_storage": WINDOWS_STORAGE}

    def public_settings(self):
        with self.lock:
            return self._public(self._read())

    def save(self, base_url, model, api_key, key_mode):
        base_url = normalize_base_url(base_url)
        model = model.strip()
        if not model or re.search(r"[\x00-\x1f\x7f]", model):
            raise ContentError(400, "ai_invalid_model", "请输入有效的模型 ID。")
        if api_key is not None:
            if not KEY_PATTERN.fullmatch(api_key) or key_mode == "clear":
                raise ContentError(400, "ai_invalid_key", "请输入有效的 API 密钥，清除时请留空。")
            if base_url.startswith("http:"):
                raise ContentError(400, "ai_insecure_key", "HTTP 回环服务请使用无密钥配置。")
        elif key_mode in {"session", "windows"}:
            raise ContentError(400, "ai_invalid_key", "请选择密钥保存方式后输入新密钥。")

        with self.lock:
            old = self._read()
            settings = {"base_url": base_url, "model": model}
            session_key = None
            if api_key is not None and key_mode == "windows":
                try:
                    settings["windows_key"] = base64.b64encode(windows_protect(api_key.encode(), base_url)).decode("ascii")
                except (ValueError, OSError):
                    raise ContentError(500, "ai_key_protection_failed", "Windows 无法保护密钥，请改用本次会话。") from None
            elif api_key is not None:
                session_key = (base_url, api_key)
            elif key_mode != "clear" and old.get("base_url") == base_url:
                if self.session_key and self.session_key[0] == base_url:
                    session_key = self.session_key
                elif old.get("windows_key"):
                    settings["windows_key"] = old["windows_key"]
            self._write(settings)
            self.session_key = session_key
            return self._public(settings)

    def provider(self) -> Provider:
        with self.lock:
            settings = self._read()
            base_url, model = settings.get("base_url"), settings.get("model")
            if not base_url or not model:
                raise ContentError(409, "ai_not_configured", "请先在 AI 写作页保存服务地址和模型。")
            base_url = normalize_base_url(base_url)
            api_key = None
            if not base_url.startswith("http:"):
                if self.session_key and self.session_key[0] == base_url:
                    api_key = self.session_key[1]
                elif settings.get("windows_key"):
                    try:
                        encrypted = base64.b64decode(settings["windows_key"], validate=True)
                        api_key = windows_protect(encrypted, base_url, decrypt=True).decode("ascii")
                        if not KEY_PATTERN.fullmatch(api_key):
                            raise ValueError
                    except (ValueError, OSError):
                        raise ContentError(409, "ai_key_unavailable", "无法读取保存的密钥，请重新输入或清除密钥。") from None
            return Provider(base_url, model, api_key)


async def fetch_completion(provider: Provider, messages, max_tokens: int) -> bytearray:
    headers = {"Accept": "application/json", "Accept-Encoding": "identity"}
    if provider.api_key:
        headers["Authorization"] = f"Bearer {provider.api_key}"
    payload = {"model": provider.model, "messages": messages, "stream": False,
               "max_completion_tokens": max_tokens}
    # 不继承代理或证书路径，也不将提示词、文档或密钥发往重定向目标。
    async with httpx.AsyncClient(timeout=httpx.Timeout(REQUEST_TIMEOUT, connect=10), trust_env=False,
                                 follow_redirects=False) as client:
        async with client.stream("POST", provider.base_url + "/chat/completions", headers=headers, json=payload) as response:
            status = response.status_code
            if 300 <= status < 400:
                raise ContentError(502, "ai_redirect", "AI 服务要求重定向，请直接填写最终服务地址。")
            if status in (401, 403):
                raise ContentError(502, "ai_provider_auth", "AI 服务拒绝认证，请核对密钥或模型权限。")
            if status == 429:
                raise ContentError(502, "ai_provider_rate_limited", "AI 服务暂时限流或额度不足，请稍后重试。")
            if status in (400, 404, 422):
                raise ContentError(502, "ai_provider_request", "AI 服务拒绝请求，请核对基础地址、模型 ID 和输入长度。")
            if not response.is_success:
                raise ContentError(502, "ai_provider_error", "AI 服务暂时无法完成请求。")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise ContentError(502, "ai_invalid_response", "AI 服务返回了不支持的压缩格式。")
            data = bytearray()
            async for chunk in response.aiter_raw():
                if len(data) + len(chunk) > RESPONSE_LIMIT:
                    raise ContentError(502, "ai_response_too_large", "AI 返回内容过长，请缩短写作要求。")
                data.extend(chunk)
            return data


async def complete(provider: Provider, messages, max_tokens=2048) -> str:
    try:
        data = await asyncio.wait_for(fetch_completion(provider, messages, max_tokens), timeout=REQUEST_TIMEOUT)
    except (asyncio.TimeoutError, httpx.TimeoutException):
        raise ContentError(504, "ai_timeout", "等待 AI 服务超时，请检查连接或缩短输入。") from None
    except httpx.RequestError:
        raise ContentError(502, "ai_unreachable", "无法连接 AI 服务，请检查地址、服务状态和 HTTPS 证书。") from None

    try:
        choice = json.loads(data)["choices"][0]
        text = choice["message"]["content"]
        if not isinstance(text, str) or not text.strip():
            raise ValueError
        text.encode("utf-8")
        if provider.api_key and provider.api_key in text:
            raise ValueError
        reason = choice.get("finish_reason")
    except (ValueError, KeyError, IndexError, TypeError, RecursionError):
        raise ContentError(502, "ai_invalid_response", "AI 服务未返回有效的正文。") from None
    if reason not in (None, "stop"):
        raise ContentError(502, "ai_incomplete_response", "AI 服务未完整生成正文，请调整要求后重试。")
    return text