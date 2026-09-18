// 数据注册中心：界面文案全部来自本目录数据文件，实现数据与界面分离
import zh from './zh.json'
import en from './en.json'

const dataMap = { zh, en }

export const defaultLanguage = 'zh'

// 语言列表（用于渲染切换按钮），名称取自各语言数据文件自身
export const languages = Object.keys(dataMap).map((code) => ({
  code,
  label: dataMap[code].language,
}))

export function hasLanguage(lang) {
  return Object.prototype.hasOwnProperty.call(dataMap, lang)
}

export function getData(lang) {
  return dataMap[lang] ?? dataMap[defaultLanguage]
}
