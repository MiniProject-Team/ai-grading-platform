import { ClipboardCheck, FileClock, LayoutDashboard, Menu, PlusCircle, X } from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';
import { useState } from 'react';

const navigation = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/evaluate', label: 'New Evaluation', icon: PlusCircle },
  { to: '/evaluations', label: 'Evaluation History', icon: FileClock },
];

export default function AppLayout({ children }) {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const pageTitle = navigation.find((item) => item.to === location.pathname)?.label || 'Evaluation Details';
  return (
    <div className="app-shell">
      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`} aria-label="Main navigation">
        <div className="brand"><span className="brand-mark"><ClipboardCheck aria-hidden="true" /></span><span>SmartEval</span></div>
        <nav>
          {navigation.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} onClick={() => setOpen(false)} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <Icon aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">Teacher workspace</div>
      </aside>
      {open && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setOpen(false)} />}
      <main className="main-content">
        <header className="topbar"><button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button><div><p className="eyebrow">Academic assessment</p><h1>{pageTitle}</h1></div></header>
        {children}
      </main>
    </div>
  );
}
