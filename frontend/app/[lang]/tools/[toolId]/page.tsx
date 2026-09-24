// app/[lang]/tools/[toolId]/page.tsx
// 工具详情占位页：守 style.md「空状态与占位页」规范——
//   大标题居中 + 氛围背景 + 一个体面的主按钮，禁止贴顶小字条；
//   进行中状态用暖琥珀 + 温和图标（非警报样式），颜色之外有图标与文字双重编码。
// 注意：Next.js 15+ 起 params 是 Promise，必须先 await。
import Link from 'next/link'
import Image from 'next/image'
import { getData } from '../../../../data'
import { getTool } from '../../../../data/tools'
import { IconArrowLeft, IconLeaf } from '../../../icons'

export async function generateMetadata({ params }) {
  const { lang, toolId } = await params
  const data = getData(lang)
  const tool = getTool(lang, toolId)
  return {
    title: tool ? `${tool.name} · ${data.meta.title}` : data.meta.title,
  }
}

export default async function ToolDetailPage({ params }) {
  const { lang, toolId } = await params
  const data = getData(lang)
  const tool = getTool(lang, toolId)

  return (
    <main id="main" className="page page--center">
      <div className="placeholder-inner">
        <Link className="back-link" href={`/${lang}/tools`}>
          <IconArrowLeft size={15} />
          {data.placeholder.back}
        </Link>

        {tool ? (
          <>
            <span className="tool-tile tool-tile--lg">
              <Image src={tool.icon} alt="" width={36} height={36} unoptimized />
            </span>
            <p className="badge badge-warm">
              <IconLeaf size={14} />
              {data.placeholder.badge}
            </p>
            <h1 className="page-title">{tool.name}</h1>
            <p className="page-desc">{tool.description}</p>
            <p className="placeholder-note">{data.placeholder.note}</p>
          </>
        ) : (
          <>
            <span className="tool-tile tool-tile--lg tool-tile--quiet">
              <IconLeaf size={30} />
            </span>
            <h1 className="page-title">{data.placeholder.unknown}</h1>
            <p className="placeholder-note">{data.placeholder.unknownNote}</p>
          </>
        )}

        <Link className="btn btn-primary" href={`/${lang}/tools`}>
          {data.placeholder.back}
        </Link>
      </div>
    </main>
  )
}
