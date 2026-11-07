# 桌面 AI 写作

## 范围与验证

1. 配置 OpenAI 兼容服务，在用户状态目录原子保存地址和模型。通过独立进程重建验证会话密钥消失，以及 Windows 用户级加密密钥可读回。
2. 使用已保存配置测试连接、生成草稿或改写正文。用实际回环 HTTP 服务校验请求字段、凭据与重定向边界、错误脱敏和响应大小限制。
3. 在编辑器中并排预览请求前与建议正文。用单测验证 YAML 原样保留、编辑或切换文档导致旧建议失效。用户明确采用后只改变编辑缓冲，沿用原有版本校验保存。

## 设置与数据流

在「AI 写作」填写服务基础地址（例如 `https://api.openai.com/v1` 或本机 `http://127.0.0.1:11434/v1`）和模型 ID，再保存并测试连接。服务需提供非流式 `POST /chat/completions`。HTTP 仅用于字面回环地址，且不发送密钥。远程服务使用 HTTPS 和受信任的 HTTPS 证书。后端直连设定地址，不跟随重定向或从环境读取代理和密钥。

密钥默认只保留在内容服务的当前进程中。用户也可选择由 Windows 数据保护 API 为当前 Windows 用户保存密钥。开发版状态文件随开发会话放在项目的忽略目录，安装版状态文件放在用户本地应用数据目录，内容库中不写入设置。改服务地址会清除旧地址的密钥。选择「清除密钥」并保存可删除当前密钥。

在编辑器展开 AI 写作并填写要求。生成发送写作要求，改写还会发送当前正文。连接测试发送固定短提示。编辑器原有的 YAML 头部、文件路径和历史版本均不作为独立请求字段。请在对照中检查建议，再决定采用或丢弃。保存文章仍需点击编辑器「保存」，按原有规则校验版本和元信息。

## 接口

下列路径使用内容服务的同一会话认证，前缀为 `/api/v1/ai`。错误沿用 `{code, message}`，不包含原始请求字段或上游错误正文。

| 方法与路径 | 输入 | 输出 |
| --- | --- | --- |
| GET `/settings` | 无 | `{base_url, model, key_mode, supports_windows_storage}`。`key_mode` 为 `none`、`session` 或 `windows` |
| PUT `/settings` | `{base_url, model, api_key?, key_mode?}`。省略密钥保留同地址的现有密钥，新密钥默认 `session`，`windows` 为显式加密保存，`clear` 清除密钥 | 同 GET |
| POST `/test` | 无，使用已保存配置 | `{ok: true}` |
| POST `/compose` | `{operation: "generate" 或 "rewrite", instruction, body?}`。改写需要正文 | `{markdown}` |

写作要求最多 4,000 字符，正文最多 60,000 字符。一次上游请求限时 60 秒，响应上限 1 MiB。长度截断、空内容和格式异常均以错误返回，编辑器保留原缓冲。

- [Windows 数据保护 API](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)
- [Chat Completions 请求格式](https://developers.openai.com/api/reference/resources/chat)