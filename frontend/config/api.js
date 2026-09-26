// 后端 API 地址：页面（服务端组件）在渲染时用它去 fetch 后端，浏览器不直接调用。
// 本地开发用默认值；部署时通过环境变量 API_BASE_URL 覆盖（例如指向本机 nginx 反代）。
export const apiBaseUrl = process.env.API_BASE_URL ?? 'http://127.0.0.1:8000'
