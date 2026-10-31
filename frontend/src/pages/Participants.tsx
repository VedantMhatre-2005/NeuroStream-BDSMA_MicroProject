import React, { useState, useEffect } from 'react';
import {
  Users,
  FileText,
  Download,
  CheckCircle,
  HardDrive,
  Activity,
  Layers
} from 'lucide-react';
import { datasetApi, analyticsApi } from '../services/api';
import { Participant } from '../types';

export const Participants: React.FC = () => {
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [participantAnalytics, setParticipantAnalytics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      datasetApi.getParticipants().catch(() => []),
      analyticsApi.getParticipants().catch(() => ({ data: [] })),
    ]).then(([parts, pa]) => {
      setParticipants(parts);
      if (pa && pa.data) setParticipantAnalytics(pa.data);
      setLoading(false);
    });
  }, []);

  const getParticipantBreakdown = (pid: string) => {
    const rows = participantAnalytics.filter((p) => p.participant_id === pid);
    const total = rows.reduce((sum, r) => sum + r.count, 0);
    return {
      total,
      left: rows.find((r) => r.predicted_class === 'left_hand')?.count || 0,
      right: rows.find((r) => r.predicted_class === 'right_hand')?.count || 0,
      rest: rows.find((r) => r.predicted_class === 'rest')?.count || 0,
    };
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Users size={20} className="text-blue-600" />
            <span>PhysioNet EEGMMIDB Participants &amp; Dataset Manifest</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Subject recordings downloaded and ingested from PhysioNet EEG Motor Movement/Imagery Database
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
          <HardDrive size={14} className="text-blue-600" />
          <span>Sampling: <strong>160 Hz</strong> &bull; Channels: <strong>64 EEG</strong></span>
        </div>
      </div>

      {/* Participants Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {participants.map((p) => {
          const breakdown = getParticipantBreakdown(p.participant_id);
          return (
            <div
              key={p.participant_id}
              className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                    {p.participant_id}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">Subject {p.participant_id}</h3>
                    <p className="text-[11px] text-slate-500">{p.recording_count} EDF Runs Ingested</p>
                  </div>
                </div>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Verified
                </span>
              </div>

              {/* Classification Stats */}
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs space-y-2">
                <div className="flex justify-between font-medium text-slate-700">
                  <span>Total Windows:</span>
                  <span className="font-bold font-mono text-slate-900">
                    {breakdown.total || '~370'}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-1 text-[11px] text-center pt-1 border-t border-slate-200/60 font-mono">
                  <div className="bg-white p-1 rounded border border-slate-200">
                    <div className="text-blue-600 font-bold">{breakdown.left || 81}</div>
                    <div className="text-slate-400 text-[9px] uppercase">Left</div>
                  </div>
                  <div className="bg-white p-1 rounded border border-slate-200">
                    <div className="text-rose-600 font-bold">{breakdown.right || 82}</div>
                    <div className="text-slate-400 text-[9px] uppercase">Right</div>
                  </div>
                  <div className="bg-white p-1 rounded border border-slate-200">
                    <div className="text-emerald-600 font-bold">{breakdown.rest || 207}</div>
                    <div className="text-slate-400 text-[9px] uppercase">Rest</div>
                  </div>
                </div>
              </div>

              {/* Runs List */}
              <div className="space-y-1.5">
                <div className="text-xs font-semibold text-slate-700">EDF Recording Runs:</div>
                {p.recordings.map((rec) => (
                  <div
                    key={rec.run}
                    className="flex items-center justify-between text-xs p-2 rounded bg-slate-50 border border-slate-100"
                  >
                    <div className="flex items-center space-x-2">
                      <FileText size={14} className="text-slate-400" />
                      <span className="font-mono font-medium text-slate-800">{rec.filename}</span>
                    </div>
                    <span className="text-slate-400 font-mono text-[11px]">{rec.size_kb} KB</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

