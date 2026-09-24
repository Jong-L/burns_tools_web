// 首页：服务端组件。[lang] 动态段（文件夹名即路由参数）对应原 react-router 的 <Route path="/:lang">。
// 语言校验/重定向在 proxy.js，<html lang>/<title> 在 layout.jsx，这里只负责页面内容。
// 首屏为服务端渲染：英雄区文案直接进 HTML，利于 SEO；语言切换由 layout 顶栏负责（客户端）。
import { getData } from '../../data'
import App from './App'

export default async function LangPage({ params }) {
  const { lang } = await params
  const data = getData(lang)

  return <App data={data} lang={lang} />
}
