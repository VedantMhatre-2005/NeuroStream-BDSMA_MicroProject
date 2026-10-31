import React, { useState, useEffect } from 'react';
import {
  Radio,
  Sliders,
  Filter,
  Layers,
  Clock,
  Info,
  CheckSquare,
  Square,
  Download,
  Search
} from 'lucide-react';
import { datasetApi } from '../services/api';

const DEFAULT_CHANNELS = ['C3', 'C4', 'Cz', 'Fc3', 'Fc4', 'Cp3', 'Cp4', 'F3', 'F4', 'P3', 'P4', 'O1', 'O2'];
const CHANNEL_PALETTE = ['#2563eb', '#dc2626', '#059669', '#7c3aed', '#ea580c', '#0891b2', '#d97706', '#4f46e5', '#0284c7', '#16a34a', '#ca8a04', '#9333ea', '#e11d48'];

export const EEGExplorer: React.FC = () => {
  const [recordingId, setRecordingId] = useState('S001R04');
  const [selectedChannels, setSelectedChannels] = useState<string[]>(['C3', 'C4', 'Cz', 'Fc3', 'Fc4']);
  const [startSec, setStartSec] = useState<number>(10.0);
  const [durationSec, setDurationSec] = useState<number>(10.0);
  const [filtered, setFiltered] = useState<boolean>(true);
  
  const [signalData, setSignalData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSignals = () => {
    setLoading(true);
    setError(null);
    datasetApi.getSampleSignal({
      recording_id: recordingId,
      channels: selectedChannels.join(','),
      start_sec: startSec,
      duration_sec: durationSec,
      filtered: filtered,
      downsample_factor: 1,
    })
      .then((data) => {
        setSignalData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load EEG signals');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchSignals();
  }, [recordingId, selectedChannels, startSec, durationSec, filtered]);

  const toggleChannel = (ch: string) => {
    if (selectedChannels.includes(ch)) {
      if (selectedChannels.length > 1) {
        setSelectedChannels(selectedChannels.filter((c) => c !== ch));
      }
    } else {
      setSelectedChannels([...selectedChannels, ch]);
    }
  };

  const selectAll = () => setSelectedChannels(DEFAULT_CHANNELS);
  const selectMotor = () => setSelectedChannels(['C3', 'C4', 'Cz', 'Fc3', 'Fc4', 'Cp3', 'Cp4']);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header and Controls Card */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Radio size={20} className="text-blue-600" />
              <span>Multi-Channel EEG Explorer &amp; Annotation Inspector</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Interactive high-resolution exploration of continuous PhysioNet recordings with event markers
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 text-xs font-semibold text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={filtered}
                onChange={(e) => setFiltered(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
              />
              <span className="flex items-center gap-1">
                <Filter size={13} className="text-blue-600" />
                <span>0.5–45 Hz Bandpass &amp; 60Hz Notch</span>
              </span>
            </label>
          </div>
        </div>

        {/* Query Parameter Sliders */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block font-medium text-slate-700 mb-1">Recording Dataset:</label>
            <select
              value={recordingId}
              onChange={(e) => setRecordingId(e.target.value)}
              className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:ring-1 focus:ring-blue-500"
            >
              <option value="S001R04">S001 - R04 (Motor Imagery: Left/Right)</option>
              <option value="S001R08">S001 - R08 (Motor Imagery: Left/Right)</option>
              <option value="S001R12">S001 - R12 (Motor Imagery: Left/Right)</option>
              <option value="S002R04">S002 - R04 (Motor Imagery: Left/Right)</option>
              <option value="S002R08">S002 - R08 (Motor Imagery: Left/Right)</option>
              <option value="S003R04">S003 - R04 (Motor Imagery: Left/Right)</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between font-medium text-slate-700 mb-1">
              <span>Time Offset:</span>
              <span className="font-mono text-blue-600 font-bold">{startSec.toFixed(1)}s</span>
            </div>
            <input
              type="range"
              min={0}
              max={110}
              step={1}
              value={startSec}
              onChange={(e) => setStartSec(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between font-medium text-slate-700 mb-1">
              <span>Window Duration:</span>
              <span className="font-mono text-blue-600 font-bold">{durationSec.toFixed(1)}s</span>
            </div>
            <input
              type="range"
              min={2}
              max={30}
              step={2}
              value={durationSec}
              onChange={(e) => setDurationSec(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>
        </div>

        {/* Channel Selection Chips */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-700">Display Channels:</span>
            <div className="space-x-2">
              <button
                onClick={selectMotor}
                className="text-[11px] font-medium text-blue-600 hover:underline"
              >
                Sensorimotor Only (C3, C4, Cz, etc.)
              </button>
              <span className="text-slate-300">|</span>
              <button
                onClick={selectAll}
                className="text-[11px] font-medium text-blue-600 hover:underline"
              >
                Select All
              </button>
            </div>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {DEFAULT_CHANNELS.map((ch, idx) => {
              const isSelected = selectedChannels.includes(ch);
              return (
                <button
                  key={ch}
                  onClick={() => toggleChannel(ch)}
                  className={`px-2.5 py-1 rounded-md text-xs font-mono font-medium transition-colors border ${
                    isSelected
                      ? 'bg-blue-50 text-blue-700 border-blue-300 shadow-xs'
                      : 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {ch}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* SVG Waveform Stack & Timeline */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
        {/* Annotation Markers Banner */}
        <div className="flex items-center justify-between text-xs bg-slate-50 p-3 rounded-lg border border-slate-100">
          <div className="flex items-center space-x-2">
            <Clock size={15} className="text-slate-500" />
            <span className="font-semibold text-slate-700">PhysioNet Event Annotations:</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-emerald-500 text-white flex items-center justify-center text-[9px] font-bold">
                T0
              </span>
              <span>Resting State</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-blue-500 text-white flex items-center justify-center text-[9px] font-bold">
                T1
              </span>
              <span>Left Fist Motion / Imagery</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-rose-500 text-white flex items-center justify-center text-[9px] font-bold">
                T2
              </span>
              <span>Right Fist Motion / Imagery</span>
            </span>
          </div>
        </div>

        {/* Multi-Channel Waveforms Container */}
        {loading ? (
          <div className="h-96 flex items-center justify-center text-slate-400 text-sm">
            Loading EEG waveform slices from EDF...
          </div>
        ) : error ? (
          <div className="h-96 flex items-center justify-center text-rose-500 text-sm">
            {error}
          </div>
        ) : signalData && signalData.signals ? (
          <div className="space-y-3">
            {selectedChannels.map((ch, idx) => {
              const vals = signalData.signals[ch] || [];
              const color = CHANNEL_PALETTE[idx % CHANNEL_PALETTE.length];
              
              // Calculate basic channel stats
              const minVal = vals.length ? Math.min(...vals) : 0;
              const maxVal = vals.length ? Math.max(...vals) : 0;
              const pk2pk = (maxVal - minVal).toFixed(1);

              return (
                <div key={ch} className="border border-slate-100 rounded-lg p-2.5 bg-slate-50/40">
                  <div className="flex items-center justify-between text-xs mb-1 px-1">
                    <span className="font-bold font-mono" style={{ color }}>
                      {ch}
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      Peak-to-Peak: <span className="font-semibold text-slate-700">{pk2pk} &mu;V</span> &bull; Samples: {vals.length}
                    </span>
                  </div>

                  {/* SVG Waveform Line */}
                  <div className="h-16 w-full bg-white rounded border border-slate-200 overflow-hidden relative">
                    <svg className="w-full h-full" viewBox={`0 0 ${vals.length} 100`} preserveAspectRatio="none">
                      <line x1="0" y1="50" x2={vals.length} y2="50" stroke="#f1f5f9" strokeWidth="1" strokeDasharray="3,3" />
                      {vals.length > 1 && (
                        <polyline
                          fill="none"
                          stroke={color}
                          strokeWidth="1.2"
                          points={vals
                            .map((v: number, i: number) => {
                              // map -50uV to 90, +50uV to 10
                              const y = 50 - (v * 40 / 50.0);
                              return `${i},${Math.max(5, Math.min(95, y))}`;
                            })
                            .join(' ')}
                        />
                      )}
                    </svg>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
            No signal data available for this range.
          </div>
        )}
      </div>
    </div>
  );
};
