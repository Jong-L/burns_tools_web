// 工具元数据：与语言无关的结构信息（tool_id 顺序 + 专属图标）。
// 工具文案（名称、描述）从后端 GET /api/tools?lang=<lang> 获取，按 tool_id 与这里合并；
// tool_id 与桌面版 / docs/data-layer-spec.md 保持一致。
// 注意：这些函数在服务端组件里被 await，网络错误时返回空结果，
// 页面自然落入已有的空态/未知工具兜底，前端不因此白屏。
import thoughtJournalIcon from '@/assets/thought-journal.svg'
import thoughtCounterIcon from '@/assets/thought-counter.svg'
import dailyActivityPlanIcon from '@/assets/daily-activity-plan.svg'
import antiProcrastinationIcon from '@/assets/anti-procrastination-table.svg'
import butRebuttalIcon from '@/assets/but-rebuttal.svg'
//后端 API 地址
const apiBaseUrl = process.env.API_BASE_URL ?? 'http://127.0.0.1:8000'

// 每个工具配专属语义图标，禁止复用同一个通用图标（style.md 组件规则）
export const toolMeta = [
  { id: 'thought_journal', icon: thoughtJournalIcon },
  { id: 'thought_counter', icon: thoughtCounterIcon },
  { id: 'daily_activity_plan', icon: dailyActivityPlanIcon },
  { id: 'anti_procrastination_table', icon: antiProcrastinationIcon },
  { id: 'but_rebuttal_tool', icon: butRebuttalIcon },
]

// 按语言从后端取完整工具列表信息
// revalidate 与列表页的 ISR 周期一致：数据 60 秒内复用，后端改内容最迟 1 分钟生效。
export async function getTools(lang) {
  try {
    const res = await fetch(`${apiBaseUrl}/api/tools?lang=${lang}`, {
      next: { revalidate: 60 },
    })
    if (!res.ok) return []
    const items = await res.json()
    const byId = Object.fromEntries(items.map((tool) => [tool.id, tool]))
    // 列表顺序与图标由前端 toolMeta 决定；后端数据里没有的 id 直接跳过
    return toolMeta
      .filter((meta) => byId[meta.id])
      .map((meta) => ({
        id: meta.id,
        icon: meta.icon,
        name: byId[meta.id].name,
        description: byId[meta.id].description,
      }))
  } catch {
    // 后端没启动 / 网络不通：返回空列表，页面走空态兜底
    return []
  }
}

// 按 tool_id 取单个工具；未命中返回 null（占位页据此走兜底文案）
export async function getTool(lang, toolId) {
  const tools = await getTools(lang)
  return tools.find((tool) => tool.id === toolId) ?? null
}
