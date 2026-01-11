"use client";

import React, { useState } from 'react';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: '안녕하세요! Willog AI Assistant입니다. 무엇을 도와드릴까요?' }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage = input;
        setInput('');
        const newMessages: Message[] = [...messages, { role: 'user', content: userMessage }];
        setMessages(newMessages);
        setLoading(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: newMessages }),
            });

            if (!response.ok) throw new Error('Failed');

            const data = await response.json();
            setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
        } catch {
            setMessages(prev => [...prev, { role: 'assistant', content: '서버 연결에 실패했습니다.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px', fontFamily: 'system-ui' }}>
            <h1 style={{ textAlign: 'center', color: '#1a1a1a' }}>Willog AI Assistant</h1>

            <div style={{ border: '1px solid #e5e5e5', borderRadius: '12px', padding: '20px', minHeight: '400px', marginBottom: '20px', background: '#fafafa' }}>
                {messages.map((msg, idx) => (
                    <div key={idx} style={{
                        padding: '12px 16px',
                        margin: '8px 0',
                        borderRadius: '12px',
                        background: msg.role === 'user' ? '#0066ff' : '#ffffff',
                        color: msg.role === 'user' ? '#ffffff' : '#1a1a1a',
                        marginLeft: msg.role === 'user' ? '20%' : '0',
                        marginRight: msg.role === 'user' ? '0' : '20%',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                    }}>
                        {msg.content}
                    </div>
                ))}
                {loading && <div style={{ padding: '12px', color: '#666' }}>응답 생성 중...</div>}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="메시지를 입력하세요..."
                    disabled={loading}
                    style={{
                        flex: 1,
                        padding: '14px 18px',
                        borderRadius: '12px',
                        border: '1px solid #e5e5e5',
                        fontSize: '16px',
                        outline: 'none'
                    }}
                />
                <button
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    style={{
                        padding: '14px 24px',
                        borderRadius: '12px',
                        border: 'none',
                        background: '#0066ff',
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: '16px',
                        opacity: loading || !input.trim() ? 0.5 : 1
                    }}
                >
                    전송
                </button>
            </div>
        </div>
    );
}
