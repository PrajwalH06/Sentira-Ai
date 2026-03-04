import { NavLink, useLocation } from 'react-router-dom';
import { Brain, LayoutDashboard, MessageSquarePlus, Activity, TrendingUp } from 'lucide-react';

const links = [
    { to: '/', label: 'Overview' },
    { to: '/submit', label: 'Analyze' },
    { to: '/feedbacks', label: 'History' },
    { to: '/trends', label: 'Stats' },
    { to: '/insights', label: 'Insights' },
];

export default function Navbar() {
    return (
        <nav className="top-navbar">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: 10,
                    background: 'linear-gradient(135deg, var(--primary), var(--accent))',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                }}>
                    <Brain size={18} color="white" />
                </div>
                <h1 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                    Sentira
                </h1>
            </div>

            <div className="nav-links">
                {links.map(({ to, label }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === '/'}
                        className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    >
                        {label}
                    </NavLink>
                ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                    padding: '6px 16px',
                    borderRadius: 20,
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--success)', boxShadow: '0 0 10px var(--success)' }} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--success)' }}>AI Active</span>
                </div>
            </div>
        </nav>
    );
}
