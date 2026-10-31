import React, { useState, useEffect } from 'react';
import {
  Brain,
  Zap,
  Activity,
  Layers,
  Sparkles,
  BarChart2,
  TrendingUp,
  Compass
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { analyticsApi, modelApi } from '../services/api';

const COLORS = ['#3b82f6', '#ef4444', '#10b981'];

export const BrainStateClassification: React.FC = () => {
  const [brainStates, setBrainStates] = useState<any[]>([]);
  const [modelMetrics, setModelMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.getBrainStates().catch(() => null),
      modelApi.getMetrics().catch(() => null),
    ]).then(([bs, mm]) => {
      if (bs && bs.data) setBrainStates(bs.data);
      if (mm) setModelMetrics(mm);
      setLoading(false);
    });
  }, []);

  const radarData = [
    { subject: 'Alpha Suppression (ERD)', left: 85, right: 88, rest: 20 },
    { subject: 'Beta Lateralization', left: 78, right: 82, rest: 15 },
    { subject: 'Mu Rhythm Power', left: 45, right: 48, rest: 90 },
    { subject: 'Frontocentral Power', left: 65, right: 60, rest: 35 },
    { subject: 'C3/C4 Asymmetry', left: 92, right: 89, rest: 10 },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Intro Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Brain size={20} className="text-blue-600" />
          <span>Motor Imagery Brain-State Classification &amp; Sensorimotor Dynamics</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1 leading-relaxed">
          Distinguishing between left-hand motor imagery, right-hand motor imagery, and resting baseline states. The classification leverages sensorimotor event-related desynchronization (ERD) in the mu (8–13 Hz) and beta (13–30 Hz) frequency bands over contralateral electrodes (C3 vs C4).
        </p>
      </div>

      {/* Sensorimotor Lateralization Explainer Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-xl border border-blue-200 border-t-4 border-t-blue-600 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-blue-700 uppercase tracking-wider">Class 1</span>
            <span className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-mono">T1 Annotation</span>
          </div>
          <h3 className="text-base font-bold text-slate-900 mt-2">Left-Hand Motor Imagery</h3>
          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            Imagined movement of the left fist triggers event-related desynchronization (ERD) in the contralateral motor cortex, decreasing mu/beta amplitude over electrode <strong className="text-blue-700">C4</strong> and <strong className="text-blue-700">Fc4</strong>.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Contralateral Electrode:</span>
            <span className="font-mono font-bold text-slate-800">C4 (Right Hemisphere)</span>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-rose-200 border-t-4 border-t-rose-600 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-700 uppercase tracking-wider">Class 2</span>
            <span className="text-[10px] bg-rose-50 text-rose-700 px-2 py-0.5 rounded font-mono">T2 Annotation</span>
          </div>
          <h3 className="text-base font-bold text-slate-900 mt-2">Right-Hand Motor Imagery</h3>
          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            Imagined movement of the right fist triggers contralateral ERD over the left motor cortex, decreasing mu/beta amplitude predominantly over electrode <strong className="text-rose-700">C3</strong> and <strong className="text-rose-700">Fc3</strong>.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Contralateral Electrode:</span>
            <span className="font-mono font-bold text-slate-800">C3 (Left Hemisphere)</span>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-emerald-200 border-t-4 border-t-emerald-600 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">Class 3</span>
            <span className="text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded font-mono">T0 Annotation</span>
          </div>
          <h3 className="text-base font-bold text-slate-900 mt-2">Resting Baseline</h3>
          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            During quiescent rest, sensorimotor rhythms remain synchronized (ERS), exhibiting prominent bilateral alpha/mu power with negligible inter-hemispheric lateralization.
          </p>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-500">Spectral State:</span>
            <span className="font-mono font-bold text-slate-800">Bilateral Mu Synchrony</span>
          </div>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Classification Distribution */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Predicted Class Totals &amp; Confidence</h3>
              <p className="text-xs text-slate-500">Aggregated directly from Hive Parquet table <code className="font-mono text-blue-600">eeg_classification_results</code></p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={brainStates.map((b) => ({
                  name: b.predicted_class.replace('_', ' ').toUpperCase(),
                  windows: b.count,
                  confidence: Math.round(b.avg_confidence * 100),
                }))}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val: number) => [`${val} windows`, 'Count']}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, borderColor: '#e2e8f0', fontSize: 12 }}
                />
                <Bar dataKey="windows" radius={[4, 4, 0, 0]}>
                  {brainStates.map((_, idx) => (
                    <Cell key={`bar-${idx}`} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Feature Radar Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Electrophysiological Profiles</h3>
              <p className="text-xs text-slate-500">Comparative radar of sensorimotor indicators across classes</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9 }} />
                <Radar name="Left Hand" dataKey="left" stroke="#2563eb" fill="#2563eb" fillOpacity={0.2} />
                <Radar name="Right Hand" dataKey="right" stroke="#dc2626" fill="#dc2626" fillOpacity={0.2} />
                <Radar name="Rest" dataKey="rest" stroke="#059669" fill="#059669" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

