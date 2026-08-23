import React, { useEffect, useRef, useState } from 'react'

// Downscale any image to ≤512px JPEG before it goes anywhere near the wire.
async function shrink(file) {
  const url = URL.createObjectURL(file)
  const img = await new Promise((res, rej) => {
    const i = new Image()
    i.onload = () => res(i); i.onerror = rej; i.src = url
  })
  const scale = Math.min(1, 512 / Math.max(img.width, img.height))
  const c = document.createElement('canvas')
  c.width = Math.round(img.width * scale)
  c.height = Math.round(img.height * scale)
  c.getContext('2d').drawImage(img, 0, 0, c.width, c.height)
  URL.revokeObjectURL(url)
  return c.toDataURL('image/jpeg', 0.85).split(',')[1]
}

export default function App() {
  const [view, setView] = useState({ messages: [], ticket: {}, pending: null, trail: null })
  const [text, setText] = useState('')
  const [photo, setPhoto] = useState(null) // {b64, preview}
  const [busy, setBusy] = useState(false)
  const fileRef = useRef()
  const endRef = useRef()

  const refresh = async () => {
    const r = await fetch('/api/session')
    if (r.ok) setView(await r.json())
  }
  useEffect(() => { refresh(); const t = setInterval(refresh, 2500); return () => clearInterval(t) }, [])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [view.messages.length])

  const send = async () => {
    if (!text.trim() && !photo) return
    setBusy(true)
    const body = { text: text.trim() || 'Here is a photo.', image_b64: photo?.b64 || null }
    setText(''); setPhoto(null)
    const r = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    })
    if (r.ok) setView(await r.json())
    setBusy(false)
  }

  const decide = async (decision) => {
    setBusy(true)
    const r = await fetch('/api/approve', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision }),
    })
    if (r.ok) setView(await r.json())
    setBusy(false)
  }

  const pickPhoto = async (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    const b64 = await shrink(f)
    setPhoto({ b64, preview: 'data:image/jpeg;base64,' + b64 })
    e.target.value = ''
  }

  const t = view.ticket
  return (
    <div className="app">
      <header>
        <div className="mark">◍</div>
        <h1>Lumen</h1>
        <div className={'dot ' + (view.pending ? 'amber' : 'ok')} />
      </header>
      <div className="cols">
        <section className="panel">
          <div className="phead">
            <img className="avatar" src="/avatar-maya.png" alt="Maya" /> Maya
            {t.ticket_order_number && <span className="id">#{t.ticket_order_number}</span>}
            {view.pending && <span className="pend" />}
          </div>
          <div className="body chat">
            {view.messages.map((m, i) => (
              <div key={i} className={'msg ' + m.who}>
                {m.photo ? <span className="photomark">📷 photo</span> : m.text}
                {m.who === 'iris' && view.trail && i === view.messages.length - 1 && m.text?.includes('known') && (
                  <div className="trail">{view.trail.path} ✓ {view.trail.fix}</div>
                )}
              </div>
            ))}
            {busy && <div className="msg iris">…</div>}
            <div ref={endRef} />
          </div>
          <div className="inrow">
            <button className="icon" onClick={() => fileRef.current.click()}>📎</button>
            <input ref={fileRef} type="file" accept="image/*" hidden onChange={pickPhoto} />
            {photo && <img className="staged" src={photo.preview} onClick={() => setPhoto(null)} />}
            <input
              className="box" placeholder="Message…" value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && send()}
            />
            <button className="icon send" onClick={send} disabled={busy}>➤</button>
          </div>
        </section>

        <section className="panel">
          <div className="phead"><img className="avatar" src="/avatar-iris.png" alt="Iris" /> Supervisor</div>
          {view.pending ? (
            <div className="appr">
              <div className="amt">
                ${view.pending.args?.amount}
                <span> refund{t.ticket_order_number ? ` · #${t.ticket_order_number}` : ''}</span>
              </div>
              <div className="btns">
                <button className="btn ok" onClick={() => decide('approved')} disabled={busy}>Approve</button>
                <button className="btn no" onClick={() => decide('denied')} disabled={busy}>Deny</button>
              </div>
            </div>
          ) : (
            <div className="quiet">No approvals waiting</div>
          )}
          <div className="hist">
            {view.messages.map((m, i) => (
              <div key={i} className="hline">
                <b>{m.who === 'maya' ? 'Maya' : 'Iris'}</b> {m.photo ? '📷 photo' : m.text}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
