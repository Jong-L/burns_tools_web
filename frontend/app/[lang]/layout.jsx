// 语言布局：拥有 <html>/<body> 骨架，能读取 [lang] 参数，
// 因此 <html lang> 和 <title> 可以按语言在服务端直接生成（SEO 关键）。
// 注意：整个 app 目录下所有路由都在 [lang] 之内，所以它就是根布局。
import { getData, hasLanguage } from '../../data'
import { LanguageProvider } from '../useLang'
import '../globals.css'

// 数据驱动：按语言生成 <title> 与 <html lang>（原来用 useEffect 手动改 document）
export async function generateMetadata({ params }) {
  const { lang } = await params
  if (!hasLanguage(lang)) return {}
  return { title: getData(lang).page.title }
}

export default async function LangLayout({ children, params }) {
  const { lang } = await params
  const data = getData(lang)

  return (
    <html lang={data.htmlLang}>
      <body>
        <LanguageProvider lang={lang}>{children}</LanguageProvider>
      </body>
    </html>
  )
}
