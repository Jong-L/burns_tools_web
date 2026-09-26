// app/[lang]/tools/page.jsx
// 工具列表页（服务端组件，走 ISR/静态渲染保证 SEO）：
//   工具文案（id、名称、描述）来自后端 GET /api/tools?lang=<lang>，图标在前端 toolMeta 合并；
//   界面文案走 data/*.json。后端不通时 getTools 返回 []，页面落入空态兜底。
// style.md「大方感」：网格 auto-fit minmax(300px, 1fr)，卡片等宽等高；
// 「单个元素的体面」：只有 1 个工具时渲染为特写卡；空状态同样大标题居中 + 主按钮。
import Link from 'next/link'
import Image from 'next/image'
import { getData } from '@/data'
import { getTools } from '@/data/tools'
import { IconArrowRight } from '@/app/_components/icons'

export const revalidate = 60

export async function generateMetadata({ params }) {
  const { lang } = await params
  const data = getData(lang)
  return {
    title: `${data.tools.heading} · ${data.meta.title}`,
    description: data.tools.intro,
  }
}

export default async function ToolsPage({ params }) {
  const { lang } = await params
  const data = getData(lang)
  const tools = await getTools(lang)

  return (
    <main id="main" className="page">
      <div className="container">
        <header className="page-head">
          <p className="eyebrow badge badge-soft">{data.tools.eyebrow}</p>
          <h1 className="page-title">{data.tools.heading}</h1>
          <p className="page-desc">{data.tools.intro}</p>
        </header>

        {/* 极端数量适配：空状态也要守规范——大标题居中 + 氛围背景 + 体面主按钮 */}
        {tools.length === 0 && (
          <div className="tools-empty">
            <h2 className="tools-empty-title">{data.tools.emptyTitle}</h2>
            <p className="tools-empty-desc">{data.tools.emptyDesc}</p>
            <Link className="btn btn-primary" href={`/${lang}`}>
              {data.tools.emptyCta}
            </Link>
          </div>
        )}

        {/* 极端数量适配：只有 1 个工具时升级为特写卡（图标 72px、标题 28px、描述 17px） */}
        {tools.length === 1 && (
          <Link className="tool-card tool-feature" href={`/${lang}/tools/${tools[0].id}`}>
            <span className="tool-tile tool-tile--lg">
              <Image src={tools[0].icon} alt="" width={36} height={36} unoptimized />
            </span>
            <h2 className="tool-name">{tools[0].name}</h2>
            <span className="tool-desc">{tools[0].description}</span>
            <span className="tool-cta">
              {data.tools.cta}
              <IconArrowRight size={15} />
            </span>
          </Link>
        )}

        {tools.length > 1 && (
          <div className="tools-grid">
            {tools.map((tool) => (
              <Link key={tool.id} href={`/${lang}/tools/${tool.id}`} className="tool-card">
                <span className="tool-tile">
                  <Image src={tool.icon} alt="" width={28} height={28} unoptimized />
                </span>
                <h2 className="tool-name">{tool.name}</h2>
                <span className="tool-desc">{tool.description}</span>
                <span className="tool-cta">
                  {data.tools.cta}
                  <IconArrowRight size={15} />
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
