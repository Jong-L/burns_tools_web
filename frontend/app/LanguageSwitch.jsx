'use client'

// 语言切换：从浮动的玻璃按钮改为顶栏里的胶囊组（style.md：禁玻璃拟态堆砌）。
// 点击后经 useLang 切换路径前缀的 [lang] 段。
import { useLang } from './useLang'
import { languages } from '../data'

export default function LanguageSwitch({ label }) {
  const { lang, switchLanguage } = useLang()

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
