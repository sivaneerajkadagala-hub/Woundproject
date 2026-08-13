import React, { useState, useEffect } from 'react';
import { Bot, Send, User as UserIcon, Sparkles, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Patient, WoundCase } from '../types';
import api from '../services/api';

interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
}

export const AssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'assistant',
      text: 'Hello Dr. Rivera. I am your Wound AI Decision Support Assistant. I can summarize visit history, structure assessment notes, and explain area changes. How can I assist with your wound monitoring today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const [patients, setPatients] = useState<Patient[]>([]);
  const [wounds, setWounds] = useState<WoundCase[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [selectedWoundId, setSelectedWoundId] = useState<string>('');

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await api.get('/patients');
        setPatients(res.data);
        if (res.data.length > 0) setSelectedPatientId(res.data[0].id.toString());
      } catch (err) {
        console.error('Error fetching patients:', err);
      }
    };
    fetchPatients();
  }, []);

  useEffect(() => {
    const fetchWounds = async () => {
      if (!selectedPatientId) return;
      try {
        const res = await api.get('/wounds', { params: { patient_id: selectedPatientId } });
        setWounds(res.data);
        if (res.data.length > 0) setSelectedWoundId(res.data[0].id.toString());
      } catch (err) {
        console.error('Error fetching wounds:', err);
      }
    };
    fetchWounds();
  }, [selectedPatientId]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMsg.trim() || loading) return;

    const userText = inputMsg.trim();
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    setMessages((prev) => [...prev, { sender: 'user', text: userText, timestamp: timeStr }]);
    setInputMsg('');
    setLoading(true);

    try {
      const res = await api.post('/assistant/chat', {
        message: userText,
        wound_id: selectedWoundId ? Number(selectedWoundId) : null,
        patient_id: selectedPatientId ? Number(selectedPatientId) : null
      });

      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: res.data.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } catch (err) {
      console.error('Assistant error:', err);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'I encountered an error processing your query. Please check network connections or backend service status.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    "Summarize this wound's measurement history across recorded visits.",
    "What is the percentage reduction in surface area from baseline?",
    "Format clinical notes for today's wound evaluation."
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* Title */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <Bot className="w-6 h-6 text-cyan-600" />
            <span>AI Clinical Decision Assistant</span>
          </h2>
          <p className="text-xs text-slate-500">Local / AI Mesh modular assistant for visit summaries & structured notes</p>
        </div>

        {/* Case Context Selector */}
        <div className="flex items-center gap-2 bg-slate-900 text-white p-2 rounded-xl border border-slate-800 text-xs">
          <span className="text-slate-400 font-semibold">Context:</span>
          <select
            value={selectedWoundId}
            onChange={(e) => setSelectedWoundId(e.target.value)}
            className="bg-slate-950 text-white border border-slate-700 rounded-lg px-2.5 py-1 text-xs focus:ring-1 focus:ring-cyan-500"
          >
            {wounds.map((w) => (
              <option key={w.id} value={w.id}>{w.case_code} - {w.location}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Chat Messages Window */}
      <Card className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4 flex flex-col bg-slate-50/50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 max-w-2xl ${msg.sender === 'user' ? 'ml-auto flex-row-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white font-bold text-xs ${
                msg.sender === 'user'
                  ? 'bg-slate-900'
                  : 'bg-gradient-to-tr from-cyan-600 to-teal-500 shadow'
              }`}
            >
              {msg.sender === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`p-4 rounded-2xl text-xs leading-relaxed space-y-1 shadow-sm ${
                msg.sender === 'user'
                  ? 'bg-slate-900 text-white rounded-tr-none'
                  : 'bg-white text-slate-800 border border-slate-200 rounded-tl-none'
              }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>
              <span className="text-[10px] text-slate-400 block text-right font-mono">{msg.timestamp}</span>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3 max-w-2xl">
            <div className="w-8 h-8 rounded-full bg-cyan-600 text-white flex items-center justify-center text-xs">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="p-3 bg-white border border-slate-200 rounded-2xl text-xs text-slate-400 italic">
              Synthesizing clinical response...
            </div>
          </div>
        )}
      </Card>

      {/* Quick Prompts */}
      <div className="flex flex-wrap gap-2 shrink-0">
        {quickPrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => setInputMsg(p)}
            className="text-[11px] bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 px-3 py-1.5 rounded-full font-medium transition-colors"
          >
            "{p}"
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} className="flex gap-3 shrink-0">
        <input
          type="text"
          value={inputMsg}
          onChange={(e) => setInputMsg(e.target.value)}
          placeholder="Ask AI Assistant about wound history or visit metrics..."
          className="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-2xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-cyan-500 shadow-sm"
        />
        <button
          type="submit"
          disabled={loading || !inputMsg.trim()}
          className="px-5 py-3 bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-bold text-xs rounded-2xl shadow-md transition-all flex items-center gap-1.5"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
};
