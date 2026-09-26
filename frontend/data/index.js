// 数据注册中心：界面文案全部来自本目录数据文件，实现数据与界面分离。
// 「支持哪些语言」由 config/i18n.js 决定，本文件只负责按语言把数据取出来。
import zh from './zh.json'
import en from './en.json'
import { defaultLanguage, publishedLanguages } from '@/config/i18n'

// 已有译文的数据，key = 语言码。
// en 已翻译好但尚未发布，仍然留在这里注册：这样开放英文只需改 config/i18n.js 一行，
// 不必回来动这个文件的 import。
const dataMap = { zh, en }

// 语言列表（用于渲染切换按钮），名称取自各语言数据文件自身
export const languages = publishedLanguages.map((code) => {
  const data = dataMap[code]
  // 配置里发布了不存在的语言时直接报错，而不是静默少显示一种语言
  if (!data) {
    throw new Error(
      `config/i18n.js 发布了语言 "${code}"，但找不到数据文件 data/${code}.json`
    )
  }
  return { code, label: data.language }
})

export function getData(lang) {
  return dataMap[lang] ?? dataMap[defaultLanguage]
}
