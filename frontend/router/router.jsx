// 路由脚本：使用 react-router 声明式管理路由，按语言前缀匹配（/zh、/en）
import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router'
import { defaultLanguage, hasLanguage } from '../data'
import { LanguageProvider } from './useLang'
import App from '../src/App'

// 语言路由：校验语言代码，无效时重定向到默认语言
function LangRoute() {
  const { lang } = useParams()
  if (!hasLanguage(lang)) {
    return <Navigate to={`/${defaultLanguage}`} replace />
  }
  return <App />
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 无语言前缀（如 /）时重定向到默认语言 */}
        <Route path="/" element={<Navigate to={`/${defaultLanguage}`} replace />} />
        {/* 语言前缀路由，/* 保留语言后页面路径，便于以后扩展子页面 */}
        <Route
          path="/:lang/*"
          element={
            <LanguageProvider>
              <LangRoute />
            </LanguageProvider>
          }
        />
        {/* 兜底：未匹配路径重定向到默认语言 */}
        <Route path="*" element={<Navigate to={`/${defaultLanguage}`} replace />} />
      </Routes>
    </BrowserRouter>
  )
}
