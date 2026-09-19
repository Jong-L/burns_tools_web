// 中间件：在请求到达页面前做语言重定向。
// 对应原 react-router 的三条兜底路由：
//   /        → /zh     <Route path="/"> <Navigate>
//   /fr      → /zh     hasLanguage 校验失败
//   其它路径  → /zh     <Route path="*">
import { NextResponse } from 'next/server'
import { defaultLanguage, hasLanguage } from './data'

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
