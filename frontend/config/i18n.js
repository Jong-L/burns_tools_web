// 多语言总开关 —— 日常只需要改这一个文件。
//
// 三处分工，别搞混：
//   config/i18n.js   决定「支持哪些语言」——配置决策，改这里
//   data/<code>.json 每种语言的文案内容——数据
//   data/index.js    把上面两者拼起来的读取入口——代码管道，一般不用动
//
// 只列一种语言时，顶栏的语言切换按钮会自动消失（见 app/_components/LanguageSwitch.jsx）；
// 未列出的语言即使有数据文件也访问不到（会被 proxy.js 重定向回默认语言）。

// 默认语言：访问 / 或访问了不可用语言时，回落到这里
export const defaultLanguage = 'zh'

// 已发布语言：数组顺序 = 切换器上的显示顺序。
// 想开放英文，把 'en' 加进这个数组即可（data/en.json 已经翻译好放在那里）。
export const publishedLanguages = ['zh']

// 是否可用：只有已发布的语言允许通过 URL 直接访问
export function hasLanguage(lang) {
  return publishedLanguages.includes(lang)
}
