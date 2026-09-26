'use client'

// 语言切换：从浮动的玻璃按钮改为顶栏里的胶囊组（style.md：禁玻璃拟态堆砌）。
// 点击后经 useLang 切换路径前缀的 [lang] 段。
// 当前只发布中文（config/i18n.js 的 publishedLanguages），只有一种语言时整个组件不渲染，
// 顶栏自然只剩品牌名；日后开放第二种语言，本组件无需改动即自动出现。
import { useLang } from './useLang'
import { languages } from '@/data'

export default function LanguageSwitch({ label }) {
  const { lang, switchLanguage } = useLang()

  if (languages.length < 2) return null

  return (
    <nav className="lang-switch" aria-label={label}>
      {languages.map((item) => {
        const active = item.code === lang
        return (
          <button
            key={item.code}
            type="button"
            className={active ? 'lang-btn is-active' : 'lang-btn'}
            aria-pressed={active}
            onClick={() => switchLanguage(item.code)}
          >
            {item.label}
          </button>
        )
      })}
    </nav>
  )
}
