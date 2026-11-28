"use client";

import { useEffect, useMemo, useState } from "react";

const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api").replace(/\/$/, "");
const categories = ["Family", "Kids", "Work", "Health", "Personal", "Other"];
const emptyForm = { title: "", description: "", category: "Family", remind_at: "" };

function localDateTime(value) {
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 16);
}
function displayDate(value) {
  return new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

export default function Home() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [auth, setAuth] = useState({ username: "", email: "", first_name: "", password: "", password_confirm: "" });
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState(null);
  const [filter, setFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [aiText, setAiText] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [aiQuestion, setAiQuestion] = useState("");

  async function request(path, options = {}, authToken = token) {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...options.headers,
      },
    });
    if (response.status === 401 && authToken && typeof window !== "undefined") {
      const refresh = window.localStorage.getItem("moment_refresh");
      if (refresh && !options._retried) {
        const refreshed = await fetch(`${API}/auth/token/refresh/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
        });
        const refreshedData = await refreshed.json().catch(() => ({}));
        if (refreshed.ok && refreshedData.access) {
          window.localStorage.setItem("moment_access", refreshedData.access);
          return request(path, { ...options, _retried: true }, refreshedData.access);
        }
        window.localStorage.removeItem("moment_access");
        window.localStorage.removeItem("moment_refresh");
      }
    }
    const data = response.status === 204 ? null : await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.detail || Object.values(data || {}).flat().join(" ") || "Something went wrong.");
    return data;
  }

  async function loadDashboard(activeToken = token) {
    const [profile, reminders] = await Promise.all([
      request("/auth/me/", {}, activeToken),
      request("/reminders/?ordering=remind_at", {}, activeToken),
    ]);
    setUser(profile);
    setItems(reminders);
  }

  // The initial session restore intentionally runs once on mount.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    const saved = window.localStorage.getItem("moment_access");
    if (saved) {
      setToken(saved);
      loadDashboard(saved).catch(() => {
        window.localStorage.removeItem("moment_access");
        setToken("");
      });
    }
  }, []);

  const visibleItems = useMemo(() => items.filter((item) => {
    const matchesCategory = filter === "All" || item.category === filter;
    const matchesSearch = `${item.title} ${item.description}`.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  }), [items, filter, search]);

  async function submitAuth(event) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      if (authMode === "register") {
        await request("/auth/register/", { method: "POST", body: JSON.stringify(auth) }, "");
      }
      const data = await request("/auth/token/", {
        method: "POST",
        body: JSON.stringify({ username: auth.username, password: auth.password }),
      }, "");
      window.localStorage.setItem("moment_access", data.access);
      window.localStorage.setItem("moment_refresh", data.refresh);
      setToken(data.access);
      await loadDashboard(data.access);
      setMessage(authMode === "register" ? "Your account is ready. Welcome!" : "Welcome back!");
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function draftWithAI() {
    if (!aiText.trim()) { setAiQuestion("Tell me what you want to remember."); return; }
    setAiBusy(true); setError(""); setMessage(""); setAiQuestion("");
    try {
      const result = await request("/reminders/parse/", {
        method: "POST",
        body: JSON.stringify({ text: aiText }),
      });
      if (result.needs_clarification) {
        setAiQuestion(result.question || "Please add a date and time, then try again.");
      } else if (result.draft) {
        setForm({
          title: result.draft.title || "",
          description: result.draft.description || "",
          category: result.draft.category || "Personal",
          remind_at: localDateTime(result.draft.remind_at),
        });
        setEditing(null);
        setAiQuestion("Draft ready. Review the details below, then select Save reminder to confirm.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setAiBusy(false);
    }
  }

  async function saveReminder(event) {
    event.preventDefault(); setBusy(true); setError(""); setMessage("");
    try {
      const payload = { ...form, remind_at: new Date(form.remind_at).toISOString() };
      if (editing) await request(`/reminders/${editing}/`, { method: "PATCH", body: JSON.stringify(payload) });
      else await request("/reminders/", { method: "POST", body: JSON.stringify(payload) });
      setForm(emptyForm); setEditing(null);
      await loadDashboard();
      setMessage(editing ? "Reminder updated." : "Reminder saved.");
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function toggleComplete(item) {
    setError("");
    try {
      await request(`/reminders/${item.id}/`, { method: "PATCH", body: JSON.stringify({ is_completed: !item.is_completed }) });
      await loadDashboard();
    } catch (err) { setError(err.message); }
  }

  async function deleteReminder(id) {
    if (!window.confirm("Delete this reminder?")) return;
    try {
      await request(`/reminders/${id}/`, { method: "DELETE" });
      await loadDashboard(); setMessage("Reminder deleted.");
    } catch (err) { setError(err.message); }
  }

  function editReminder(item) {
    setEditing(item.id);
    setForm({ title: item.title, description: item.description, category: item.category, remind_at: localDateTime(item.remind_at) });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function logout() {
    window.localStorage.removeItem("moment_access");
    setToken(""); setUser(null); setItems([]); setForm(emptyForm); setEditing(null);
  }

  const pending = items.filter((item) => !item.is_completed).length;
  const completed = items.length - pending;

  if (!token || !user) return (
    <main className="auth-shell">
      <section className="auth-aside">
        <div className="brand"><span className="brand-mark">M</span><span>MOMent<span className="brand-ai">AI</span></span></div>
        <div className="aside-copy">
          <span className="eyebrow">A LITTLE MORE PEACE OF MIND</span>
          <h1>Remember what matters.<br /><em>Enjoy the moment.</em></h1>
          <p>One thoughtful place for the family plans, little tasks and important moments you don&apos;t want to miss.</p>
          <div className="mini-note"><span>✦</span> Made for real life, and all the things it holds.</div>
        </div>
        <div className="aside-foot">YOUR FAMILY, THOUGHTFULLY ORGANISED</div>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <span className="eyebrow muted">WELCOME TO MOMENT AI</span>
          <h2>{authMode === "login" ? "A calmer day starts here." : "Create your space."}</h2>
          <p className="subcopy">{authMode === "login" ? "Sign in to see what your family has planned." : "Set up your account and make room for what matters."}</p>
          <form onSubmit={submitAuth} className="stack-form">
            {authMode === "register" && <>
              <label>Your name<input value={auth.first_name} onChange={(e) => setAuth({ ...auth, first_name: e.target.value })} placeholder="Your name" /></label>
              <label>Email address<input type="email" required value={auth.email} onChange={(e) => setAuth({ ...auth, email: e.target.value })} placeholder="you@example.com" /></label>
            </>}
            <label>Username<input required autoComplete="username" value={auth.username} onChange={(e) => setAuth({ ...auth, username: e.target.value })} placeholder="Choose a username" /></label>
            <label>Password<input required type="password" minLength="8" autoComplete={authMode === "login" ? "current-password" : "new-password"} value={auth.password} onChange={(e) => setAuth({ ...auth, password: e.target.value })} placeholder="At least 8 characters" /></label>
            {authMode === "register" && <label>Confirm password<input required type="password" value={auth.password_confirm} onChange={(e) => setAuth({ ...auth, password_confirm: e.target.value })} placeholder="Enter password again" /></label>}
            {error && <p className="alert error">{error}</p>}
            <button className="primary-btn" disabled={busy}>{busy ? "Please wait..." : authMode === "login" ? "Sign in" : "Create account"} <span>→</span></button>
          </form>
          <p className="switch-auth">{authMode === "login" ? "New to MOMent AI?" : "Already have an account?"} <button onClick={() => { setAuthMode(authMode === "login" ? "register" : "login"); setError(""); }}>{authMode === "login" ? "Create an account" : "Sign in"}</button></p>
          <p className="privacy-note">Your reminders are private to your account.</p>
        </div>
      </section>
    </main>
  );

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">M</span><span>MOMent<span className="brand-ai">AI</span></span></div>
        <div className="side-label">WORKSPACE</div>
        <button className="side-link active">▦ <span>My reminders</span></button>
        <div className="side-label category-label">CATEGORIES</div>
        {categories.map((category) => <button key={category} className={filter === category ? "side-link selected" : "side-link"} onClick={() => setFilter(category)}><span className="category-dot" />{category}</button>)}
        <div className="sidebar-bottom"><div className="avatar">{(user.first_name || user.username).slice(0, 1).toUpperCase()}</div><div className="profile-text"><strong>{user.first_name || user.username}</strong><span>Personal space</span></div><button className="logout" onClick={logout} title="Sign out">↗</button></div>
      </aside>
      <section className="main-area">
        <header className="topbar"><div><span className="eyebrow muted">YOUR FAMILY OVERVIEW</span><h1>Hello, {user.first_name || user.username} <span className="wave">✦</span></h1></div><button className="quiet-btn" onClick={logout}>Sign out</button></header>
        <div className="content">
          <section className="welcome-banner"><div><span className="eyebrow">A MOMENT FOR WHAT MATTERS</span><h2>Make today a little lighter.</h2><p>Keep the important things close, so you can focus on the moments in between.</p></div><div className="banner-art" aria-hidden="true"><span>✿</span><i>♡</i></div></section>
          <section className="stats">
            <div className="stat-card"><span className="stat-icon lavender">◷</span><div><strong>{pending}</strong><span>Upcoming reminders</span></div></div>
            <div className="stat-card"><span className="stat-icon peach">✓</span><div><strong>{completed}</strong><span>Moments taken care of</span></div></div>
            <div className="stat-card"><span className="stat-icon mint">♡</span><div><strong>{items.length}</strong><span>Total reminders</span></div></div>
          </section>
          <div className="dashboard-grid">
            <section className="panel create-panel"><div className="panel-heading"><div><span className="eyebrow muted">{editing ? "MAKE A CHANGE" : "GET IT OUT OF YOUR HEAD"}</span><h3>{editing ? "Edit reminder" : "Create a reminder"}</h3></div><span className="sparkle">✧</span></div>
              <div className="ai-draft-box">
                <label htmlFor="ai-reminder-text">Describe it in your own words</label>
                <textarea id="ai-reminder-text" rows="3" value={aiText} onChange={(e) => setAiText(e.target.value)} placeholder="For example: Remind me to take Amma to her appointment tomorrow at 10 AM" />
                <button type="button" className="ai-draft-btn" onClick={draftWithAI} disabled={aiBusy || !aiText.trim()}>{aiBusy ? "Thinking..." : "✦ Create a draft with AI"}</button>
                {aiQuestion && <p className="ai-hint" role="status">{aiQuestion}</p>}
                <p className="ai-caption">AI prepares a draft only. You review and save it yourself.</p>
              </div>
              <form onSubmit={saveReminder} className="stack-form">
                <label>What do you need to remember?<input required maxLength="255" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Pick up the kids from school" /></label>
                <label>A little more detail <textarea rows="2" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Add a note (optional)" /></label>
                <div className="form-row"><label>Category<select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>{categories.map((c) => <option key={c}>{c}</option>)}</select></label><label>Date & time<input required type="datetime-local" min={localDateTime(new Date())} value={form.remind_at} onChange={(e) => setForm({ ...form, remind_at: e.target.value })} /></label></div>
                {error && <p className="alert error">{error}</p>}
                <div className="form-actions"><button className="primary-btn" disabled={busy}>{busy ? "Saving..." : editing ? "Save changes" : "Save reminder"} <span>→</span></button>{editing && <button type="button" className="quiet-btn" onClick={() => { setEditing(null); setForm(emptyForm); }}>Cancel</button>}</div>
              </form>
            </section>
            <section className="panel list-panel"><div className="panel-heading list-heading"><div><span className="eyebrow muted">THE THINGS THAT MATTER</span><h3>Your reminders <span className="count">{visibleItems.length}</span></h3></div><input className="search-input" aria-label="Search reminders" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
              <div className="filter-row"><button className={filter === "All" ? "filter-chip chosen" : "filter-chip"} onClick={() => setFilter("All")}>All</button>{["Family", "Kids", "Work", "Health", "Personal"].map((c) => <button key={c} className={filter === c ? "filter-chip chosen" : "filter-chip"} onClick={() => setFilter(c)}>{c}</button>)}</div>
              <div className="reminder-list">{visibleItems.length === 0 ? <div className="empty-state"><span>♡</span><strong>Nothing on your list just yet.</strong><p>Add a reminder and give your mind a little breathing room.</p></div> : visibleItems.map((item) => <article className={item.is_completed ? "reminder completed" : "reminder"} key={item.id}><button className="check-btn" onClick={() => toggleComplete(item)} aria-label={item.is_completed ? "Mark as incomplete" : "Mark as complete"}>{item.is_completed ? "✓" : ""}</button><div className="reminder-copy"><strong>{item.title}</strong>{item.description && <p>{item.description}</p>}<div className="reminder-meta"><span>{item.category}</span><span>·</span><span>{displayDate(item.remind_at)}</span></div></div><div className="item-actions"><button onClick={() => editReminder(item)} aria-label="Edit reminder">Edit</button><button onClick={() => deleteReminder(item.id)} aria-label="Delete reminder">Delete</button></div></article>)}</div>
            </section>
          </div>
          {message && <p className="toast">{message}</p>}
          <footer className="app-footer">A little more space for the moments that matter. <span>MOMent AI ✦</span></footer>
        </div>
      </section>
    </main>
  );
}
