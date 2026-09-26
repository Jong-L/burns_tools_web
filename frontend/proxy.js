// 中间件：在请求到达页面前做语言重定向。
// 对应原 react-router 的三条兜底路由：
//   /        → /zh     <Route path="/"> <Navigate>
//   /fr      → /zh     hasLanguage 校验失败
//   其它路径  → /zh     <Route path="*"> <Navigate>
// 注意：hasLanguage 判的是「已发布语言」（config/i18n.js 的 publishedLanguages），
// 所以暂时关闭的 /en 也会被重定向回 /zh，而不是 404——旧链接不会断。
import { NextResponse } from 'next/server'
import { defaultLanguage, hasLanguage } from './config/i18n'

export function proxy(request) {
  const firstSegment = request.nextUrl.pathname.split('/')[1]
  if (hasLanguage(firstSegment)) {
    return NextResponse.next()
  }
  return NextResponse.redirect(new URL(`/${defaultLanguage}`, request.url))
}

// 排除静态资源，只拦截页面路径
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)'],
}
