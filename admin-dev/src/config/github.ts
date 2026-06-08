/**
 * GitHub OAuth 配置
 * 用于 Device Flow 认证
 */
export const githubConfig = {
  // GitHub OAuth App 的 Client ID
  // 请替换为你的实际 Client ID
  clientId: 'YOUR_GITHUB_CLIENT_ID',

  // 授权范围
  scope: 'repo',

  // 仓库 owner，用于身份校验
  owner: 'lucan6290',

  // GitHub Device Flow 端点
  endpoints: {
    deviceCode: 'https://github.com/login/device/code',
    accessToken: 'https://github.com/login/oauth/access_token',
    user: 'https://api.github.com/user'
  }
}