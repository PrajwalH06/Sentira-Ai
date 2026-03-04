import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, AreaChart, Area } from 'recharts';
import { getTrends } from '../api';

export default function Trends() {
    const [trends, setTrends] = useState(null);
    const [days, setDays] = useState(30);

    useEffect(() => {
        getTrends(days).then(res => setTrends(res.data)).catch(console.error);
    }, [days]);

    const tooltipStyle = {
        contentStyle: {
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 12,
            color: 'var(--text-primary)',
            fontSize: '0.85rem',
            backdropFilter: 'blur(20px)',
        },
    };

    return (
        <div className="animate-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 40 }}>
                <div>
                    <h1 className="heading-hero" style={{ fontSize: '3rem', margin: 0 }}>
                        <span className="heading-gradient-accent">Data</span> Trends.
                    </h1>
                </div>
                <div style={{ display: 'flex', gap: 8, background: 'rgba(255,255,255,0.02)', padding: 6, borderRadius: 16, border: '1px solid var(--border)' }}>
                    {[7, 14, 30, 90].map((d) => (
                        <button
                            key={d}
                            onClick={() => setDays(d)}
                            style={{
                                padding: '8px 16px',
                                borderRadius: 10,
                                background: days === d ? 'rgba(255,255,255,0.1)' : 'transparent',
                                color: days === d ? 'var(--text-primary)' : 'var(--text-muted)',
                                border: 'none',
                                cursor: 'pointer',
                                fontWeight: 600,
                                fontSize: '0.85rem',
                                transition: 'all 0.2s'
                            }}
                        >
                            {d} Days
                        </button>
                    ))}
                </div>
            </div>

            <div className="glass-panel" style={{ padding: 32, marginBottom: 32 }}>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 24 }}>Sentiment Velocity</h3>
                {trends?.sentiment_trends?.length > 0 && (
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={trends.sentiment_trends}>
                            <defs>
                                <linearGradient id="gP" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#10b981" stopOpacity={0.2} /><stop offset="100%" stopColor="#10b981" stopOpacity={0} /></linearGradient>
                                <linearGradient id="gN" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#ef4444" stopOpacity={0.2} /><stop offset="100%" stopColor="#ef4444" stopOpacity={0} /></linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => v.slice(5)} />
                            <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                            <Tooltip {...tooltipStyle} />
                            <Area type="monotone" dataKey="positive" stroke="#10b981" fill="url(#gP)" strokeWidth={2} />
                            <Area type="monotone" dataKey="negative" stroke="#ef4444" fill="url(#gN)" strokeWidth={2} />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>

            <div className="glass-panel" style={{ padding: 32 }}>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 24 }}>Category Volumes</h3>
                {trends?.category_trends?.length > 0 && (
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={trends.category_trends}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={v => v.slice(5)} />
                            <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} axisLine={false} />
                            <Tooltip {...tooltipStyle} />
                            <Legend wrapperStyle={{ fontSize: '0.8rem', paddingTop: 20 }} />
                            <Line type="monotone" dataKey="UI/UX" stroke="#60a5fa" strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="Bugs" stroke="#ef4444" strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="Performance" stroke="#06b6d4" strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="Pricing" stroke="#f59e0b" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
}
