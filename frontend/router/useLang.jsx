// 语言上下文：由路由解析 :lang 参数后向页面提供语言数据
import { createContext, useContext, useEffect } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router'
import { getData } from '../data'

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const { lang } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const data = getData(lang)

  // 数据驱动：同步 <html lang> 与页面标题
  useEffect(() => {
    document.documentElement.lang = data.htmlLang
    document.title = data.page.title
  }, [data])

  // 切换语言并保留语言前缀后的路径
  const switchLanguage = (target) => {
    const segments = location.pathname.split('/')
    segments[1] = target
    navigate(segments.join('/') || `/${target}`)
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
