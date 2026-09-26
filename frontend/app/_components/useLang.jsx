// 语言上下文：由文件路由解析 [lang] 动态段后向页面提供语言数据。
// 与 Vite 版的差异：不再依赖 react-router 的 hooks，改用 Next.js 传下来的 params；
// 文档标题和 <html lang> 改为在服务端通过 generateMetadata 设置（SEO 更友好）。
'use client'

import { createContext, useContext } from 'react'
import { useParams, usePathname, useRouter } from 'next/navigation'
import { getData } from '@/data'

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const { lang } = useParams()
  const pathname = usePathname()
  const router = useRouter()
  const data = getData(lang)

  // 切换语言并保留语言前缀后的路径
  const switchLanguage = (target) => {
    const segments = pathname.split('/')
    segments[1] = target
    router.push(segments.join('/') || `/${target}`)
  }

  return (
    <LanguageContext.Provider value={{ lang, data, switchLanguage }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLang() {
  return useContext(LanguageContext)
}
