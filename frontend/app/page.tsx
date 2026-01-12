"use client";

import React, { useState, useRef, useEffect } from 'react';
import {
    LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    PieChart, Pie, Cell, Sankey
} from 'recharts';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    data?: any[];
    sql?: string;
    agent?: string;
}

const SUGGESTIONS = [
    "📉 상하이(CNSHG)행 총 물량 및 파손율",
    "🔥 구간별 충격 리스크 히트맵 분석",
    "⚠️ 누적 충격 피로도 Top 5 운송 건",
    "🍬 오사카행 온도 이탈 평균 지속 시간",
    "📊 포장 타입별 파손율 및 안전 점수 비교",
    "🛳️ 해상 운송 중 5G 이상 충격 발생 비율",
    "📍 베트남 경로 습도 취약 구간 분석",
    "❄️ 영하 온도에서 발생한 충격 건수",
    "🏆 운송사별 배송 품질 벤치마킹",
    "🚨 최근 1주일 High Risk 등급 운송 건",
    "📦 포장재별 평균 온도 유지 성능",
    "✈️ 항공 운송 중 과도한 기울기(Tilt) 발생 건수",
    "📅 월별 화물 무사고(파손 0) 비율 추이",
    "🚛 트럭 운송 시 평균 충격량(G) 통계",
    "🌡️ 여름철(7-8월) 온도 이탈 화물 집중 분석"
];

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: '안녕하세요! Willog Intelligence Assistant입니다. 무엇을 도와드릴까요?' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async (text?: string) => {
        const contentToUse = text || input;
        if (!contentToUse.trim() || loading) return;

        if (!text) setInput('');

        const userMessage: Message = { role: 'user', content: contentToUse };
        const newMessages = [...messages, userMessage];
        setMessages(newMessages);
        setLoading(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: newMessages }),
            });

            if (!response.ok) throw new Error('Failed');

            const resData = await response.json();
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: resData.answer,
                data: resData.data,
                sql: resData.sql,
                agent: resData.agent
            }]);
        } catch {
            setMessages(prev => [...prev, { role: 'assistant', content: '서버 연결에 실패했습니다.' }]);
        } finally {
            setLoading(false);
        }
    };

    const renderVisualization = (data: any[]) => {
        // CRITICAL FIX: Early return for empty or invalid data
        if (!data || !Array.isArray(data) || data.length === 0 || !data[0]) {
            return null;
        }

        try {
            const columns = Object.keys(data[0]);
            if (columns.length === 0) return null;

            const dateCol = columns.find(c => c.toLowerCase().includes('date') || c.toLowerCase().includes('day') || c.toLowerCase().includes('time') || c.toLowerCase().includes('month'));
            const numCol = columns.find(c => typeof data[0][c] === 'number' && !c.toLowerCase().includes('lat') && !c.toLowerCase().includes('lon'));
            const catCols = columns.filter(c => typeof data[0][c] === 'string' && !c.toLowerCase().includes('date') && !c.toLowerCase().includes('time'));
            const catCol = catCols.length > 0 ? catCols[0] : undefined;

            const sourceCol = columns.find(c => c.includes('source') || c.includes('start') || c.includes('departure') || c.includes('출발'));
            const targetCol = columns.find(c => c.includes('target') || c.includes('end') || c.includes('destination') || c.includes('도착'));

            // 0. Stacked Trend Chart (Ratio/Share over Time)
            // Trigger: Date + Number(Ratio/Percent) + Category
            const isRatio = numCol && (numCol.includes('ratio') || numCol.includes('share') || numCol.includes('percent') || numCol.includes('비중'));

            if (dateCol && catCol && numCol && isRatio) {
                // Pivot Data for Stacked Chart
                const pivotMap = new Map();
                const categories = new Set<string>();

                data.forEach(row => {
                    const dateVal = row[dateCol];
                    const catVal = row[catCol];
                    const numVal = row[numCol];
                    categories.add(String(catVal));

                    if (!pivotMap.has(dateVal)) {
                        pivotMap.set(dateVal, { [dateCol]: dateVal });
                    }
                    pivotMap.get(dateVal)[catVal] = numVal;
                });

                const chartData = Array.from(pivotMap.values()).sort((a, b) => new Date(a[dateCol]).getTime() - new Date(b[dateCol]).getTime());
                const categoryList = Array.from(categories);
                const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#a4de6c', '#d0ed57', '#8dd1e1', '#83a6ed', '#8e44ad', '#e74c3c'];

                return (
                    <div style={{ height: 400, width: '100%', marginTop: 20 }}>
                        <h4 style={{ marginBottom: 10, color: '#444' }}>📊 Stacked Trend Analysis ({catCol})</h4>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey={dateCol} fontSize={12} tickMargin={10} />
                                <YAxis fontSize={12} unit="%" />
                                <Tooltip contentStyle={{ borderRadius: 8 }} />
                                <Legend />
                                {categoryList.map((cat, idx) => (
                                    <Bar key={cat} dataKey={cat} stackId="a" fill={colors[idx % colors.length]} isAnimationActive={false} />
                                ))}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                );
            }

            // 1. Heatmap (Category vs Category)
            // Trigger: No Date + 2 Categories + Number
            if (!dateCol && catCols.length >= 2 && numCol && !sourceCol) {
                const xCol = catCols[0];
                const yCol = catCols[1];

                // Pivot data for heatmap
                const xValues = Array.from(new Set(data.map(d => d[xCol]))).sort();
                const yValues = Array.from(new Set(data.map(d => d[yCol]))).sort();
                const valueMap = new Map();
                let maxValue = 0;

                data.forEach(d => {
                    const key = `${d[xCol]}-${d[yCol]}`;
                    const val = Number(d[numCol]);
                    valueMap.set(key, val);
                    if (val > maxValue) maxValue = val;
                });

                return (
                    <div style={{ width: '100%', marginTop: 20, overflowX: 'auto' }}>
                        <h4 style={{ marginBottom: 10, color: '#444' }}>🔥 Heatmap Analysis ({xCol} vs {yCol})</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: `auto repeat(${xValues.length}, 1fr)`, gap: 4, minWidth: 500 }}>
                            {/* Header Row */}
                            <div />
                            {xValues.map(x => (
                                <div key={x} style={{ textAlign: 'center', fontSize: '0.8rem', fontWeight: 600, padding: 5, color: '#555' }}>
                                    {x}
                                </div>
                            ))}

                            {/* Data Rows */}
                            {yValues.map(y => (
                                <React.Fragment key={y}>
                                    <div style={{ textAlign: 'right', fontSize: '0.8rem', fontWeight: 600, padding: 8, color: '#555', whiteSpace: 'nowrap' }}>
                                        {y}
                                    </div>
                                    {xValues.map(x => {
                                        const val = valueMap.get(`${x}-${y}`) || 0;
                                        const intensity = val / (maxValue || 1);
                                        const bgColor = val > 0 ? `rgba(0, 122, 255, ${0.1 + intensity * 0.9})` : '#f5f5f5';
                                        const textColor = intensity > 0.6 ? 'white' : '#333';

                                        return (
                                            <div key={`${x}-${y}`} style={{
                                                background: bgColor,
                                                color: textColor,
                                                borderRadius: 6,
                                                padding: 10,
                                                textAlign: 'center',
                                                fontSize: '0.85rem',
                                                transition: 'transform 0.1s',
                                                cursor: 'default'
                                            }} title={`${x} - ${y}: ${val}`}>
                                                {val > 0 ? val : '-'}
                                            </div>
                                        );
                                    })}
                                </React.Fragment>
                            ))}
                        </div>
                    </div>
                );
            }

            // 2. Time Series (Line Chart)
            if (dateCol && numCol) {
                return (
                    <div style={{ height: 300, width: '100%', marginTop: 20 }}>
                        <h4 style={{ marginBottom: 10, color: '#444' }}>📈 Trend Analysis</h4>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey={dateCol} fontSize={12} tickMargin={10} />
                                <YAxis fontSize={12} />
                                <Tooltip contentStyle={{ borderRadius: 8 }} />
                                <Legend />
                                <Line type="monotone" dataKey={numCol} stroke="#8884d8" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} isAnimationActive={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                );
            }

            // 2. Geospatial (Scatter Chart)
            const latCol = columns.find(c => /lat/i.test(c));
            const lonCol = columns.find(c => /lon|lng/i.test(c));

            if (latCol && lonCol) {
                const chartData = data
                    .filter(d => d && d[latCol] != null && d[lonCol] != null && !isNaN(Number(d[latCol])) && !isNaN(Number(d[lonCol])))
                    .map((d, i) => ({
                        id: i,
                        x: Number(d[lonCol]),
                        y: Number(d[latCol]),
                        ...d
                    }));

                if (chartData.length === 0) return null;

                return (
                    <div style={{ height: 400, width: '100%', marginTop: 20 }}>
                        <h4 style={{ marginBottom: 10, color: '#444' }}>🗺️ Geospatial Distribution</h4>
                        <div style={{ background: '#f9f9f9', borderRadius: 12, padding: 10, height: '100%', border: '1px solid #eee' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis type="number" dataKey="x" name="Longitude" domain={['auto', 'auto']} fontSize={12} unit="°" />
                                    <YAxis type="number" dataKey="y" name="Latitude" domain={['auto', 'auto']} fontSize={12} unit="°" />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ borderRadius: 8 }} />
                                    <Legend />
                                    <Scatter name="Locations" data={chartData} fill="#ff7300" isAnimationActive={false} />
                                </ScatterChart>
                            </ResponsiveContainer>
                        </div>
                        <div style={{ textAlign: 'center', fontSize: '0.8rem', color: '#999', marginTop: 5 }}>
                            * Displaying {chartData.length} valid points
                        </div>
                    </div>
                );
            }

            // 3. Pie Chart (Aggregated Ratio/Share)
            // Trigger: No Date + Category + Number (Preferably small number of categories)
            if (!dateCol && catCol && numCol) {
                const colors = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

                return (
                    <div style={{ height: 350, width: '100%', marginTop: 20 }}>
                        <h4 style={{ marginBottom: 10, color: '#444' }}>🍩 Proportion Analysis ({catCol})</h4>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={data}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={120}
                                    innerRadius={60} // Donut style
                                    fill="#8884d8"
                                    dataKey={numCol}
                                    nameKey={catCol}
                                >
                                    {data.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ borderRadius: 8 }} itemStyle={{ color: '#333' }} />
                                <Legend layout="vertical" verticalAlign="middle" align="right" />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                );
            }

            // 4. Comparison (Bar Chart) - Fallback
            if (catCol && numCol) {
                return (
                    <div style={{ height: 300, width: '100%', marginTop: 20 }}>
                        <h4 style={{ marginBottom: 10, color: '#444' }}>📊 Comparison</h4>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey={catCol} fontSize={12} tickMargin={10} />
                                <YAxis fontSize={12} />
                                <Tooltip contentStyle={{ borderRadius: 8 }} />
                                <Legend />
                                <Bar dataKey={numCol} fill="#82ca9d" radius={[4, 4, 0, 0]} isAnimationActive={false} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                );
            }

            // 5. Sankey Chart (Flow: Source -> Target)
            // Ensure numCol exists (already defined above)

            if (sourceCol && targetCol && numCol && !dateCol) {
                // Transform flat data to { nodes: [], links: [] }
                const nodes = new Set<string>();
                data.forEach(d => {
                    nodes.add(d[sourceCol]);
                    nodes.add(d[targetCol]);
                });

                const nodeList = Array.from(nodes).map((n, i) => ({ name: n, index: i }));
                const nodeMap = new Map(nodeList.map(n => [n.name, n.index]));

                const links = data.map(d => ({
                    source: nodeMap.get(d[sourceCol]),
                    target: nodeMap.get(d[targetCol]),
                    value: Number(d[numCol])
                })).filter(l => l.source !== undefined && l.target !== undefined && l.value > 0);

                if (links.length > 0) {
                    const sankeyData = { nodes: nodeList, links };
                    return (
                        <div style={{ height: 400, width: '100%', marginTop: 20 }}>
                            <h4 style={{ marginBottom: 10, color: '#444' }}>🌊 Flow Analysis (Sankey)</h4>
                            <ResponsiveContainer width="100%" height="100%">
                                <Sankey
                                    data={sankeyData}
                                    node={{ stroke: '#77c878', strokeWidth: 2 }}
                                    link={{ stroke: '#77c878' }}
                                >
                                    <Tooltip />
                                </Sankey>
                            </ResponsiveContainer>
                        </div>
                    );
                }
            }

            return null;
        } catch (error) {
            console.error('Visualization error:', error);
            return (
                <div style={{ padding: 12, background: '#fff3cd', borderRadius: 8, marginTop: 12, color: '#856404' }}>
                    ⚠️ 차트 렌더링 중 오류가 발생했습니다.
                </div>
            );
        }
    };

    const renderTable = (data: any[]) => {
        // CRITICAL FIX: Validate data before rendering table
        if (!data || !Array.isArray(data) || data.length === 0 || !data[0]) {
            return (
                <div style={{ padding: 16, textAlign: 'center', color: '#888', background: '#f9f9f9', borderRadius: 8 }}>
                    데이터가 없습니다.
                </div>
            );
        }

        try {
            const columns = Object.keys(data[0]);
            if (columns.length === 0) return null;

            return (
                <div style={{ marginTop: 20, overflow: 'hidden', border: '1px solid #eee', borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
                    <div style={{ overflowX: 'auto', maxHeight: '400px' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', minWidth: 600 }}>
                            <thead style={{ position: 'sticky', top: 0, background: '#f9fafb' }}>
                                <tr>
                                    {columns.map(key => (
                                        <th key={key} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 600, color: '#555', borderBottom: '1px solid #eee' }}>{key}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {data.slice(0, 10).map((row, i) => (
                                    <tr key={i} style={{ borderBottom: '1px solid #f5f5f5', background: 'white' }}>
                                        {columns.map((col, j) => (
                                            <td key={j} style={{ padding: '10px 14px', color: '#333' }}>
                                                {row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {data.length > 10 && (
                        <div style={{ padding: '8px', textAlign: 'center', fontSize: '0.75rem', color: '#888', background: '#fafafa', borderTop: '1px solid #eee' }}>
                            Showing first 10 rows of {data.length}
                        </div>
                    )}
                </div>
            );
        } catch (error) {
            console.error('Table rendering error:', error);
            return (
                <div style={{ padding: 12, background: '#fff3cd', borderRadius: 8, marginTop: 12, color: '#856404' }}>
                    ⚠️ 테이블 렌더링 중 오류가 발생했습니다.
                </div>
            );
        }
    };

    return (
        <div style={{ maxWidth: '900px', margin: '0 auto', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
            <header style={{
                position: 'sticky', top: 0, background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)',
                padding: '16px 20px', borderBottom: '1px solid #eaeaea', zIndex: 100
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 24, height: 24, background: '#007AFF', borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: 14 }}>W</div>
                    <h1 style={{ margin: 0, fontSize: '1.1rem', color: '#111', fontWeight: 600 }}>Willog Intelligence Assistant</h1>
                </div>
            </header>

            <div style={{ padding: '20px 20px 100px 20px', minHeight: 'calc(100vh - 140px)' }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{
                        marginBottom: '24px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                    }}>
                        <div style={{
                            padding: '14px 18px',
                            borderRadius: '18px',
                            borderBottomRightRadius: msg.role === 'user' ? '4px' : '18px',
                            borderBottomLeftRadius: msg.role === 'user' ? '18px' : '4px',
                            background: msg.role === 'user' ? '#007AFF' : '#F2F2F7',
                            color: msg.role === 'user' ? '#fff' : '#111',
                            maxWidth: '85%',
                            lineHeight: '1.6',
                            whiteSpace: 'pre-wrap',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                            fontSize: '0.95rem'
                        }}>
                            {msg.content}
                        </div>

                        {msg.sql && (
                            <details style={{ marginTop: 8, maxWidth: '85%', width: '100%' }}>
                                <summary style={{ cursor: 'pointer', fontSize: '0.75rem', color: '#888', listStyle: 'none' }}>🛠️ Generated SQL</summary>
                                <pre style={{
                                    background: '#f8f9fa', padding: 12, borderRadius: 8, marginTop: 4,
                                    fontSize: '0.75rem', overflowX: 'auto', border: '1px solid #eee', color: '#333'
                                }}>
                                    {msg.sql}
                                </pre>
                            </details>
                        )}

                        {msg.data && (
                            <div style={{ width: '100%', marginTop: 12, maxWidth: '100%' }}>
                                {renderVisualization(msg.data)}
                                {renderTable(msg.data)}
                            </div>
                        )}
                    </div>
                ))}

                {loading && (
                    <div style={{ display: 'flex', justifyContent: 'center', margin: '20px 0' }}>
                        <div style={{ color: '#888', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                            <span className="spinner"></span> Thinking...
                        </div>
                        <style jsx>{`
              .spinner {
                width: 16px; height: 16px; border: 2px solid #ddd; border-top-color: #007AFF; 
                border-radius: 50%; animation: spin 0.8s linear infinite;
              }
              @keyframes spin { to { transform: rotate(360deg); } }
            `}</style>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            <div style={{
                position: 'fixed', bottom: 80, left: 0, right: 0,
                zIndex: 10, maxWidth: '900px', margin: '0 auto', pointerEvents: 'none'
            }}>
                <div style={{ padding: '0 20px', display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 10, pointerEvents: 'auto', scrollbarWidth: 'none' }}>
                    {SUGGESTIONS.map((s, i) => (
                        <button key={i} onClick={() => handleSend(s)} disabled={loading} style={{
                            background: 'white', border: '1px solid #e5e5e5', borderRadius: '20px',
                            padding: '8px 16px', fontSize: '0.85rem', color: '#333', cursor: 'pointer',
                            whiteSpace: 'nowrap', boxShadow: '0 2px 5px rgba(0,0,0,0.05)', transition: 'transform 0.1s',
                            opacity: loading ? 0.5 : 1
                        }}
                            onMouseEnter={(e) => e.currentTarget.style.borderColor = '#007AFF'}
                            onMouseLeave={(e) => e.currentTarget.style.borderColor = '#e5e5e5'}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            </div>

            <div style={{
                position: 'fixed', bottom: 0, left: 0, right: 0,
                background: '#fff', padding: '16px 20px', borderTop: '1px solid #eaeaea',
                display: 'flex', gap: 12, maxWidth: '900px', margin: '0 auto', zIndex: 20
            }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="데이터에 대해 질문해보세요..."
                    disabled={loading}
                    style={{
                        flex: 1, padding: '12px 18px', borderRadius: '24px',
                        border: '1px solid #e1e1e1', fontSize: '0.95rem', outline: 'none',
                        background: '#f9f9f9', transition: 'border-color 0.2s, background 0.2s'
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = '#007AFF'; e.currentTarget.style.background = 'white'; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = '#e1e1e1'; e.currentTarget.style.background = '#f9f9f9'; }}
                />
                <button
                    onClick={() => handleSend()}
                    disabled={loading || !input.trim()}
                    style={{
                        width: 46, height: 46, borderRadius: '50%', border: 'none',
                        background: '#007AFF', color: '#fff', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        opacity: loading || !input.trim() ? 0.5 : 1, transition: 'opacity 0.2s'
                    }}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                </button>
            </div>
        </div>
    );
}
