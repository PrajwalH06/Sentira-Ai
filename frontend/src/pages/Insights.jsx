import { useState, useEffect } from 'react';
import { Lightbulb, AlertCircle, TrendingUp, CheckCircle, ArrowRight, ShieldAlert, Sparkles } from 'lucide-react';
import { getInsights } from '../api';

const ICONS = { warning: AlertCircle, improvement: TrendingUp, positive: CheckCircle, info: Sparkles };
const ICON_COLORS = { warning: 'var(--danger)', improvement: 'var(--warning)', positive: 'var(--success)', info: 'var(--primary-light)' };

export default function Insights() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getInsights().then(res => setData(res.data)).catch(console.error).finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div style={{ height: '50vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <div className="spinner" />
                <p style={{ marginTop: 16, color: 'var(--text-muted)' }}>Generating Actionable Insights...</p>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="animate-in">
            <div style={{ marginBottom: 40 }}>
                <h1 className="heading-hero" style={{ fontSize: '3rem', margin: 0 }}>
                    <span className="heading-gradient-accent">Actionable</span> Insights.
                </h1>
                <p style={{ fontSize: '1.05rem', color: 'var(--text-secondary)' }}>
                    AI-powered recommendations based on your master feedback matrix.
                </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 32, marginBottom: 32 }}>

                {/* Health Orb */}
                <div className="glass-panel" style={{ padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 24, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                        System Health
                    </p>
                    <div style={{
                        width: 120, height: 120, borderRadius: '50%',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '1.2rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em',
                        background: data.overall_health === 'good' ? 'rgba(16, 185, 129, 0.1)' : data.overall_health === 'moderate' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        border: `2px solid ${data.overall_health === 'good' ? 'var(--success)' : data.overall_health === 'moderate' ? 'var(--warning)' : 'var(--danger)'}`,
                        color: data.overall_health === 'good' ? 'var(--success)' : data.overall_health === 'moderate' ? 'var(--warning)' : 'var(--danger)',
                        boxShadow: `0 0 40px ${data.overall_health === 'good' ? 'rgba(16, 185, 129, 0.2)' : data.overall_health === 'moderate' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                    }}>
                        {data.overall_health}
                    </div>
                </div>

                {/* Top Issues */}
                <div className="glass-panel" style={{ padding: 32 }}>
                    <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <ShieldAlert size={16} color="var(--danger)" /> Critical Vectors
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        {data.top_issues.map((issue, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16, background: 'rgba(255,255,255,0.02)', padding: '12px 16px', borderRadius: 12, border: '1px solid var(--border)' }}>
                                <span style={{ color: 'var(--danger)', fontWeight: 800, fontSize: '1.2rem', width: 24 }}>0{i + 1}</span>
                                <div style={{ flex: 1 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{issue.category}</span>
                                        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{issue.count} reports ({issue.percentage}%)</span>
                                    </div>
                                    <div style={{ height: 4, background: 'rgba(255,255,255,0.05)', borderRadius: 2, overflow: 'hidden' }}>
                                        <div style={{ height: '100%', width: `${Math.min(issue.percentage * 2, 100)}%`, background: 'var(--danger)', borderRadius: 2 }} />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Recommendations Log */}
            <div className="glass-panel" style={{ padding: 32 }}>
                <h3 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Lightbulb size={16} color="var(--primary-light)" /> Action Matrix
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {data.insights.map((insight, i) => {
                        const Icon = ICONS[insight.type] || Sparkles;
                        const color = ICON_COLORS[insight.type] || 'var(--primary-light)';
                        return (
                            <div key={i} style={{ display: 'flex', gap: 20, background: 'rgba(255,255,255,0.02)', padding: 24, borderRadius: 16, border: '1px solid var(--border)', borderLeft: `2px solid ${color}` }}>
                                <div style={{ width: 48, height: 48, borderRadius: 12, background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                    <Icon size={24} color={color} />
                                </div>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                                        <h4 style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)' }}>{insight.title}</h4>
                                        <span className={`badge`} style={{ borderColor: color, color: color, background: `${color}10` }}>{insight.priority} priority</span>
                                    </div>
                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, marginBottom: 12 }}>
                                        {insight.description}
                                    </p>
                                    {insight.category && (
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                            <ArrowRight size={14} /> Matrix Vector: <span style={{ color: 'var(--text-secondary)' }}>{insight.category}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
