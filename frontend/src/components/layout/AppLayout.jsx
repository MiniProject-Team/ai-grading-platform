import { ClipboardCheck, FileCheck2, FileClock, House, LifeBuoy, Menu, Moon, PlusCircle, Search, Sun, X } from 'lucide-react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

const navigation = [
  { to: '/', label: 'Home', icon: House, end: true },
  { to: '/evaluate', label: 'New Evaluation', icon: PlusCircle },
  { to: '/evaluations', label: 'Evaluation History', icon: FileClock },
  { to: '/reports', label: 'Reports', icon: FileCheck2 },
  { to: '/help', label: 'Help & Support', icon: LifeBuoy },
];

export default function AppLayout({ children }) {
  const [search, setSearch] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [theme, setTheme] = useState(() => window.localStorage.getItem('smarteval-theme') || 'light');
  const location = useLocation();
  const navigate = useNavigate();
  const activePage = navigation.find((item) => item.to === location.pathname);
  const pageTitle = activePage?.label || (location.pathname.startsWith('/evaluations/') ? 'Evaluation Details' : 'Home');
  const isLandingPage = location.pathname === '/';
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem('smarteval-theme', theme);
  }, [theme]);
  const submitSearch = (event) => {
    event.preventDefault();
    const query = search.trim();
    if (query) navigate(`/evaluations?search=${encodeURIComponent(query)}`);
  };
  const closeMenuOnEscape = (event) => {
    if (event.key === 'Escape') setMenuOpen(false);
  };

  return (
    <div className="app-shell app-shell-no-sidebar">
      <main className="main-content">
        <header className="topbar">
          <div className="header-identity">
            <Link className="header-brand" to="/" aria-label="SmartEval Home">
              <span className="brand-mark"><ClipboardCheck aria-hidden="true" /></span><span>SmartEval</span>
            </Link>
            <p className="eyebrow">Academic assessment</p>
          </div>
          <div className="header-actions">
            {!isLandingPage && <form className="global-search" role="search" onSubmit={submitSearch}>
              <Search aria-hidden="true" />
              <label className="visually-hidden" htmlFor="global-search-input">Search evaluations</label>
              <input id="global-search-input" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search evaluations..." />
              <button type="submit">Search</button>
            </form>}
            {!isLandingPage && <div className="menu-wrap" onKeyDown={closeMenuOnEscape}>
              <button className="icon-button menu-toggle" type="button" aria-label={menuOpen ? 'Close menu' : 'Open menu'} aria-expanded={menuOpen} aria-haspopup="menu" onClick={() => setMenuOpen((open) => !open)}>
                {menuOpen ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
              </button>
              {menuOpen && <nav className="menu-popover" aria-label="Main navigation" role="menu">
                {navigation.map(({ to, label, icon: Icon, end }) => (
                  <NavLink key={to} to={to} end={end} role="menuitem" onClick={() => setMenuOpen(false)} className={({ isActive }) => `menu-link ${isActive ? 'active' : ''}`}>
                    <Icon aria-hidden="true" /><span>{label}</span>
                  </NavLink>
                ))}
              </nav>}
            </div>}
            <button className="icon-button theme-toggle" type="button" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`} onClick={() => setTheme((current) => current === 'dark' ? 'light' : 'dark')}>
              {theme === 'dark' ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
            </button>
          </div>
        </header>
        {!isLandingPage && <div className="page-title-row"><h1>{pageTitle}</h1></div>}
        {children}
      </main>
    </div>
  );
}
