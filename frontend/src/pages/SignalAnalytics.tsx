import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  Activity,
  Layers,
  Sparkles,
  Info,
  Sliders,
  Filter
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, LineChart, Line, CartesianGrid } from 'recharts';
import { analyticsApi } from '../services/api';

export const SignalAnalytics: React.FC = () => {
  const [bandPowerData, setBandPowerData] = useState<any[]>([]);
  const [channelActivity, setChannelActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.getBandPower().catch(() => null),
      analyticsApi.getChannelActivity(15).catch(() => null),
    ]).then(([bp, ca]) => {
      if (bp && bp.data) setBandPowerData(bp.data);
      if (ca && ca.data) setChannelActivity(ca.data);
      setLoading(false);
    });
  }, []);

  const formattedBandData = bandPowerData.map((d) => ({
    state: d.predicted_class.replace('_', ' ').toUpperCase(),
    Delta: Math.round(d.delta_power),
    Theta: Math.round(d.theta_power),
    Alpha: Math.round(d.alpha_power),
    Beta: Math.round(d.beta_power),
    Gamma: Math.round(d.gamma_power),
  }));

  // Synthetic PSD curve for demonstration of Welch's PSD across 0-45 Hz
  const psdFrequencies = Array.from({ length: 45 }, (_, i) => {
    const f = i + 1;
    // 1/f spectral slope with 10Hz alpha peak and 20Hz beta peak
    const baseline = 200 / (f + 1);
    const alphaPeak = 40 * Math.exp(-0.5 * Math.pow((f - 10) / 1.5, 2));
    const betaPeak = 20 * Math.exp(-0.5 * Math.pow((f - 20) / 2.5, 2));
    return {
      freq: `${f} Hz`,
      rest: Math.round(baseline + alphaPeak * 1.5 + betaPeak),
      motorImagery: Math.round(baseline + alphaPeak * 0.6 + betaPeak * 0.8),
    };
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <BarChart3 size={20} className="text-blue-600" />
          <span>EEG Spectral Analytics &amp; Frequency Band Decomposition</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Time-frequency signal analytics computed via Welch's Power Spectral Density (PSD) and bandpass filters
        </p>
      </div>

      {/* Frequency Bands Explainer Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {[
          { name: 'Delta (δ)', range: '0.5 – 4 Hz', role: 'Slow wave activity, deep rest', color: 'border-l-blue-500' },
          { name: 'Theta (θ)', range: '4 – 8 Hz', role: 'Sensorimotor integration, drowsiness', color: 'border-l-cyan-500' },
          { name: 'Alpha / Mu (α/μ)', range: '8 – 13 Hz', role: 'Motor idle, ERD during imagery', color: 'border-l-indigo-500' },
          { name: 'Beta (β)', range: '13 – 30 Hz', role: 'Active motor planning & execution', color: 'border-l-amber-500' },
          { name: 'Gamma (γ)', range: '30 – 45 Hz', role: 'High-frequency cortical processing', color: 'border-l-purple-500' },
        ].map((band) => (
          <div key={band.name} className={`bg-white p-3.5 rounded-lg border border-slate-200 border-l-4 ${band.color} shadow-xs`}>
            <div className="font-bold text-slate-900 text-xs">{band.name}</div>
            <div className="text-[11px] font-mono text-slate-500 font-semibold mt-0.5">{band.range}</div>
            <div className="text-[11px] text-slate-600 mt-1 leading-tight">{band.role}</div>
          </div>
        ))}
      </div>

      {/* Spectral Band Power by State Bar Chart */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-slate-900 text-sm">Average Band Power (&mu;V&sup2;/Hz) Across Brain States</h3>
            <p className="text-xs text-slate-500">Extracted from PySpark Welch PSD and queried from Hive <code className="font-mono text-blue-600">eeg_window_features</code></p>
          </div>
        </div>

        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={formattedBandData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="state" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, borderColor: '#e2e8f0', fontSize: 12 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Delta" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Theta" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Alpha" fill="#6366f1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Beta" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Gamma" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Welch PSD Frequency Curve & Channel Activity Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Welch PSD Spectral Line Chart */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Welch Power Spectral Density (PSD)</h3>
              <p className="text-xs text-slate-500">Logarithmic power decay with Mu (10Hz) &amp; Beta (20Hz) peaks</p>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={psdFrequencies} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f8fafc" />
                <XAxis dataKey="freq" tick={{ fontSize: 9 }} interval={4} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: 8, borderColor: '#e2e8f0', fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="rest" stroke="#10b981" strokeWidth={2} dot={false} name="Resting State" />
                <Line type="monotone" dataKey="motorImagery" stroke="#2563eb" strokeWidth={2} dot={false} name="Motor Imagery (ERD)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Channel Activity Ranking */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Top Active Channels by Beta Power</h3>
              <p className="text-xs text-slate-500">Queried from Hive <code className="font-mono text-blue-600">eeg_channel_statistics</code></p>
            </div>
          </div>

          <div className="overflow-y-auto max-h-64 border border-slate-100 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 border-b border-slate-100 sticky top-0">
                <tr>
                  <th className="px-3 py-2 font-semibold">Channel</th>
                  <th className="px-3 py-2 font-semibold">Avg Mean (&mu;V)</th>
                  <th className="px-3 py-2 font-semibold">Avg Variance</th>
                  <th className="px-3 py-2 font-semibold">Avg Alpha</th>
                  <th className="px-3 py-2 font-semibold">Avg Beta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {channelActivity.map((ch, idx) => (
                  <tr key={ch.channel_name || idx} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-bold text-blue-600">{ch.channel_name}</td>
                    <td className="px-3 py-2 text-slate-700">{ch.avg_mean}</td>
                    <td className="px-3 py-2 text-slate-700">{ch.avg_variance}</td>
                    <td className="px-3 py-2 text-slate-700">{ch.avg_alpha}</td>
                    <td className="px-3 py-2 text-slate-900 font-semibold">{ch.avg_beta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

