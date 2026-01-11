"use client";

import React, { useState, useEffect, useRef } from 'react';
import { ChatMessage } from './components/chat-message';
import { ChatInput } from './components/chat-input';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: '안녕하세요! Willog AI Assistant입니다. 무엇을 도와드릴까요?' }
    ]);
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSend = async (content: string) => {
        const newMessages = [...messages, { role: 'user', content } as Message];
        setMessages(newMessages);
        setLoading(true);

        try {
            // In production, this should be an env var. For now assuming localhost default.
            const API_URL = 'http://localhost:8000/api';

            const response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: newMessages }),
            });

            if (!response.ok) throw new Error('Failed to fetch response');

            const data = await response.json();
            setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: 'assistant', content: '죄송합니다. 서버 연결에 실패했습니다. (Backend가 실행 중인지 확인해주세요)' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="flex min-h-screen flex-col bg-white text-gray-900">
            {/* Header */}
            <header className="sticky top-0 z-40 w-full border-b bg-white/80 backdrop-blur-md px-6 py-4">
                <div className="mx-auto max-w-3xl flex items-center gap-2">
                    <div className="h-6 w-6 bg-blue-600 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold text-xs">W</span>
                    </div>
                    <h1 className="text-lg font-semibold tracking-tight">Willog AI Assistant</h1>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 w-full">
                <div className="mx-auto max-w-3xl flex flex-col pb-36 pt-4">
                    {messages.map((msg, idx) => (
                        <ChatMessage key={idx} role={msg.role} content={msg.content} />
                    ))}
                    <div ref={bottomRef} />
                </div>
            </div>

            {/* Input Area */}
            <ChatInput onSend={handleSend} disabled={loading} />
        </main>
    );
}
