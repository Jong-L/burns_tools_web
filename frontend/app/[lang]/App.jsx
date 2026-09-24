// 首页英雄区（服务端组件）：
// style.md「垂直居中律」——min-height: 100dvh + flex 双居中，内容光学上浮约 4%；
// 主标题 48–56px/800，主 CTA padding 14px 36px、字号 16px（高度 ≥ 44px）。
// 每屏只讲一件事：一句标题、一句描述、一个按钮。
import Link from 'next/link'
import { IconSprout, IconArrowRight } from '../icons'

export default function App({ data, lang }) {
  const { home } = data

  return (
    <main id="main" className="hero">
      <div className="hero-inner">
        <p className="eyebrow badge badge-soft">
          <IconSprout size={15} />
          {home.eyebrow}
        </p>
        <h1 className="hero-title">{home.title}</h1>
        <p className="hero-desc">{home.desc}</p>
        <div className="hero-actions">
          <Link className="btn btn-primary" href={`/${lang}/tools`}>
            {home.cta}
            <IconArrowRight size={18} />
          </Link>
        </div>
        <p className="hero-note">{home.note}</p>
      </div>
    </main>
  )
}
