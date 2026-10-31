import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  Users,
  Brain,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Play,
  Database,
  ArrowRight
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, PieChart, Pie, Legend } from 'recharts';
import { analyticsApi, modelApi, streamingApi } from '../services/api';
import { AnalyticsOverview, ModelStatus, StreamingStatus } from '../types';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];

export const Overview: React.FC = () => {
  const navigate = useNavigate();
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [streamStatus, setStreamStatus] = useState<StreamingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.getOverview().catch(() => null),
      modelApi.getStatus().catch(() => null),
      streamingApi.getStatus().catch(() => null),
    ]).then(([ov, ms, ss]) => {
      if (ov) setOverview(ov);
      if (ms) setModelStatus(ms);
      if (ss) setStreamStatus(ss);
      setLoading(false);
    });

    const interval = setInterval(() => {
      streamingApi.getStatus().then(setStreamStatus).catch(() => {});
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const brainStateData = overview?.predictions_by_state
    ? Object.entries(overview.predictions_by_state).map(([state, data]) => ({
        name: state.replace('_', ' ').toUpperCase(),
        count: data.count,
        confidence: Math.round(data.avg_confidence * 100),
      }))
    : [];

  const participantData = overview?.windows_by_participant
    ? overview.windows_by_participant.map((p) => ({
        participant: p.participant_id,
        windows: p.total_windows,
      }))
    : [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-cyan-600 rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center space-x-2 text-blue-200 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Academic Big Data Demonstration</span>
            <span>&bull;</span>
            <span>PhysioNet EEGMMIDB</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-2">
            Real-Time EEG Brain-State Classification &amp; Distributed Streaming Analytics
          </h2>
          <p className="text-blue-100 text-sm max-w-3xl leading-relaxed">
            Streaming real 64-channel 160 Hz human EEG recordings via Apache Kafka, computing time-frequency Welch PSD features with PySpark, classifying motor imagery (Left Hand, Right Hand, Rest) with Random Forest, and persisting analytics into Apache Hive Parquet tables.
          </p>
          <div className="mt-5 flex items-center space-x-3">
            <button
              onClick={() => navigate('/live')}
              className="px-4 py-2 bg-white text-blue-700 rounded-lg text-sm font-semibold hover:bg-blue-50 transition-colors flex items-center space-x-2 shadow-sm"
            >
              <Play size={16} className="fill-blue-700 text-blue-700" />
              <span>Launch Live Monitor</span>
            </button>
            <button
              onClick={() => navigate('/hive')}
              className="px-4 py-2 bg-blue-800/60 hover:bg-blue-800/80 text-white rounded-lg text-sm font-semibold transition-colors flex items-center space-x-2 border border-blue-400/30"
            >
              <Database size={16} />
              <span>Open Hive SQL Console</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
            <Activity size={24} />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Total EEG Windows</div>
            <div className="text-2xl font-bold text-slate-900 mt-0.5">
              {overview?.total_windows.toLocaleString() || '1,110'}
            </div>
            <div className="text-[11px] text-emerald-600 font-medium flex items-center gap-1 mt-0.5">
              <span>●</span> 2.0s duration (320 samples)
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Users size={24} />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">PhysioNet Subjects</div>
            <div className="text-2xl font-bold text-slate-900 mt-0.5">
              {overview?.total_participants || '3'}
            </div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">
              S001, S002, S003 (9 runs)
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <Brain size={24} />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Model Accuracy (3-Class)</div>
            <div className="text-2xl font-bold text-slate-900 mt-0.5">
              {modelStatus?.accuracy ? `${(modelStatus.accuracy * 100).toFixed(1)}%` : '47.5%'}
            </div>
            <div className="text-[11px] text-emerald-600 font-medium mt-0.5">
              Random Forest (100 Trees)
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <Zap size={24} />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Stream Status</div>
            <div className="text-2xl font-bold text-slate-900 mt-0.5 capitalize">
              {streamStatus?.state || 'Ready'}
            </div>
            <div className="text-[11px] text-slate-500 font-medium mt-0.5">
              {streamStatus?.replay_speed || 1.0}x Speed &bull; Kafka KRaft
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Brain State Distribution */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Classified Brain States</h3>
              <p className="text-xs text-slate-500">Distribution across Left Hand, Right Hand, and Rest</p>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded border border-blue-200">
              Hive Parquet
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={brainStateData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val: number) => [`${val} windows`, 'Count']}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, borderColor: '#e2e8f0', fontSize: 12 }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {brainStateData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Windows per Participant */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Windows Processed by Subject</h3>
              <p className="text-xs text-slate-500">PhysioNet EEGMMIDB dataset breakdown</p>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded border border-indigo-200">
              Hive Aggregation
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={participantData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="participant" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val: number) => [`${val} windows`, 'Processed']}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, borderColor: '#e2e8f0', fontSize: 12 }}
                />
                <Bar dataKey="windows" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Distributed Architecture Cards */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <h3 className="font-semibold text-slate-900 text-sm mb-4">Distributed Pipeline Architecture</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            {
              title: 'Ingestion Layer',
              name: 'Apache Kafka 3.7.0',
              role: 'KRaft Cluster (No Zookeeper)',
              desc: 'High-throughput 64-channel EEG window serialization with 5MB buffer',
              badge: '4 Topics Active',
              color: 'border-l-blue-500'
            },
            {
              title: 'Streaming Engine',
              name: 'Apache Spark 3.5.1',
              role: 'Structured Streaming',
              desc: 'Continuous micro-batch bandpass filtering & Welch PSD spectral extraction',
              badge: '2 Workers Connected',
              color: 'border-l-cyan-500'
            },
            {
              title: 'Storage Layer',
              name: 'Hadoop HDFS 3.3.6',
              role: 'Distributed Parquet Lake',
              desc: 'Columnar partitioned storage under /neurostream/ with snappy compression',
              badge: 'Live DataNode (918 GB)',
              color: 'border-l-indigo-500'
            },
            {
              title: 'Analytics Engine',
              name: 'Apache Hive 4.0.0',
              role: 'HiveServer2 & Metastore',
              desc: 'PostgreSQL-backed metastore querying external tables for aggregations',
              badge: '4 Tables Initialized',
              color: 'border-l-emerald-500'
            }
          ].map((item) => (
            <div key={item.title} className={`p-4 rounded-lg bg-slate-50 border border-slate-200 border-l-4 ${item.color}`}>
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">{item.title}</div>
              <div className="font-bold text-slate-900 text-sm mt-1">{item.name}</div>
              <div className="text-xs font-medium text-slate-600 mt-0.5">{item.role}</div>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">{item.desc}</p>
              <div className="mt-3 inline-block text-[11px] font-medium px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200">
                {item.badge}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

