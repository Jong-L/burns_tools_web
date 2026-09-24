// 工具元数据：与语言无关的结构信息（tool_id 顺序 + 专属图标）。
// 文案（工具名、描述）在 data/*.json 的 tools.items 里，遵循「文案与组件分离」。
// tool_id 与桌面版 / docs/data-layer-spec.md 保持一致，后续接后端 API 时按同一 id 对应。
import thoughtJournalIcon from '../assets/thought-journal.svg'
import thoughtCounterIcon from '../assets/thought-counter.svg'
import dailyActivityPlanIcon from '../assets/daily-activity-plan.svg'
import antiProcrastinationIcon from '../assets/anti-procrastination-table.svg'
import butRebuttalIcon from '../assets/but-rebuttal.svg'
import { getData } from './index'

// 每个工具配专属语义图标，禁止复用同一个通用图标（style.md 组件规则）
export const toolMeta = [
  { id: 'thought_journal', icon: thoughtJournalIcon },
  { id: 'thought_counter', icon: thoughtCounterIcon },
  { id: 'daily_activity_plan', icon: dailyActivityPlanIcon },
  { id: 'anti_procrastination_table', icon: antiProcrastinationIcon },
  { id: 'but_rebuttal_tool', icon: butRebuttalIcon },
]

// 按语言取出完整的工具列表（含文案），页面渲染只依赖这一个函数
export function getTools(lang) {
  const items = getData(lang).tools.items
  return toolMeta.map((tool) => ({
    id: tool.id,
    icon: tool.icon,
    name: items[tool.id].name,
    description: items[tool.id].description,
  }))
}

// 按 tool_id 取单个工具；未命中返回 null（占位页据此走兜底文案）
export function getTool(lang, toolId) {
  return getTools(lang).find((tool) => tool.id === toolId) ?? null
}
