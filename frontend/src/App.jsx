import { useState } from 'react'
import { useLang } from '../router/useLang'
import { languages } from '../data'

export default function App() {
  const { lang, data, switchLanguage } = useLang()
  const [count, setCount] = useState(0)

  return (
    <>
      <header className="lang-switch">
        {languages
          .filter((item) => item.code !== lang)
          .map((item) => (
            <button
              key={item.code}
              className="lang-btn"
              onClick={() => switchLanguage(item.code)}
            >
              {item.label}
            </button>
          ))}
      </header>

      <main className="card">
        <h1>{data.page.title}</h1>
        <p className="desc">{data.page.description}</p>

        <div className="counter" id="counter">{count}</div>

        <div className="btn-group">
          <button onClick={() => setCount(count - 1)}>-1</button>
          <button className="btn-reset" onClick={() => setCount(0)}>{data.page.counter.reset}</button>
          <button onClick={() => setCount(count + 1)}>+1</button>
        </div>
      </main>
    </>
  )
}
