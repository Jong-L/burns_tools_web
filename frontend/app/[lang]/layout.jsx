// 语言布局：拥有 <html>/<body> 骨架，能读取 [lang] 参数，
// 因此 <html lang> 和 <title> 可以按语言在服务端直接生成（SEO 关键）。
// 同时按 style.md 的「版面气场」搭好全局氛围层：
//   氛围光斑（慢漂移）、纸纤噪点、天与地（底部收边带）、顶栏（品牌 + 语言切换）。
// 注意：整个 app 目录下所有路由都在 [lang] 之内，所以它就是根布局。
import Link from 'next/link'
import { getData } from '@/data'
import { hasLanguage } from '@/config/i18n'
import { LanguageProvider } from '@/app/_components/useLang'
import LanguageSwitch from '@/app/_components/LanguageSwitch'
import { IconSprout } from '@/app/_components/icons'
import '../globals.css'

// 数据驱动：按语言生成 <title> 与 <html lang>（原来用 useEffect 手动改 document）
export async function generateMetadata({ params }) {
  const { lang } = await params
  if (!hasLanguage(lang)) return {}
  const data = getData(lang)
  return {
    title: data.meta.title,
    description: data.meta.description,
  }
}

// 深色模式（必备）：跟随系统的 theme-color，浏览器 UI 与页面渐变一致
export const viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#EEF4EE' },
    { media: '(prefers-color-scheme: dark)', color: '#141B18' },
  ],
}

export default async function LangLayout({ children, params }) {
  const { lang } = await params
  const data = getData(lang)

  return (
    <html lang={data.htmlLang}>
      <body>
        {/* 氛围光斑：2–3 个低透明度 radial-gradient，blur + 24s 以上慢漂移 */}
        <div className="ambient" aria-hidden="true">
          <span className="blob blob--moss" />
          <span className="blob blob--apricot" />
          <span className="blob blob--mist" />
        </div>

        <LanguageProvider lang={lang}>
          <a className="skip-link" href="#main">
            {data.a11y.skip}
          </a>

          <header className="topbar">
            <div className="container topbar-inner">
              <Link className="brand" href={`/${lang}`}>
                <span className="brand-mark">
                  <IconSprout size={18} />
                </span>
                <span className="brand-name">{data.brand.name}</span>
              </Link>
              <LanguageSwitch label={data.a11y.langNav} />
            </div>
          </header>

          {children}
        </LanguageProvider>

        {/* 天与地：底部深色渐变收边带，内容像站在地面上。
            带内暂不放文案，预留给你备案号 / 页脚信息 */}
        <div className="ground-band" aria-hidden="true" />

        {/* 纸纤噪点：去掉廉价 CSS 渐变感的最后一笔 */}
        <div className="grain" aria-hidden="true" />
      </body>
    </html>
  )
}
