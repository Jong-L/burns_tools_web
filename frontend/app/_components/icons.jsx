// 通用小图标（线条随 currentColor 走，非工具专属图标）。
// 样式走 style.md：soft line、圆角端点、低饱和；颜色继承文字色，自动适配浅/深色。
const base = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
  focusable: false,
}

// 新芽：品牌标识 / 治愈氛围
export function IconSprout({ size = 16, ...rest }) {
  return (
    <svg {...base} width={size} height={size} {...rest}>
      <path d="M12 21v-7" />
      <path d="M12 14C8 14 5.4 11.5 5.4 7.6 9.4 7.6 12 10.5 12 14Z" />
      <path d="M12 14c0-3.4 2.6-6.1 6.2-6.4C18.6 11 16 13.7 12.6 14H12Z" />
    </svg>
  )
}

// 叶片：暖色徽标用的温和图标
export function IconLeaf({ size = 16, ...rest }) {
  return (
    <svg {...base} width={size} height={size} {...rest}>
      <path d="M5.5 18.5C5.5 11.8 10.5 6.5 18.5 5.5c0 8-5 13-11.5 13H5.5Z" />
      <path d="M5.5 18.5c2.8-3.9 6-6.4 9.6-7.8" />
    </svg>
  )
}

// 右箭头：主按钮 / 卡片行动点
export function IconArrowRight({ size = 16, ...rest }) {
  return (
    <svg {...base} width={size} height={size} {...rest}>
      <path d="M4.5 12h14M13 6.5 18.5 12 13 17.5" />
    </svg>
  )
}

// 左箭头：返回
export function IconArrowLeft({ size = 16, ...rest }) {
  return (
    <svg {...base} width={size} height={size} {...rest}>
      <path d="M19.5 12h-14M11 6.5 5.5 12 11 17.5" />
    </svg>
  )
}
