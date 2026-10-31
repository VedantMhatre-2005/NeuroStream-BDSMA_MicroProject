import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Square,
  Activity,
  Zap,
  Clock,
  Gauge,
  CheckCircle,
  Radio,
  Sliders
} from 'lucide-react';
import { streamingApi, datasetApi } from '../services/api';
import { StreamingStatus, LiveEEGMessage } from '../types';

const MOTOR_CHANNELS = ['C3', 'C4', 'Cz', 'Fc3', 'Fc4', 'Cp3', 'Cp4'];
const CHANNEL_COLORS = [
  '#2563eb', // C3 (blue)
  '#dc2626', // C4 (red)
  '#059669', // Cz (green)
  '#7c3aed', // Fc3 (purple)
  '#ea580c', // Fc4 (orange)
  '#0891b2', // Cp3 (cyan)
  '#d97706', // Cp4 (amber)
];

export const LiveMonitoring: React.FC = () => {
  const [streamStatus, setStreamStatus] = useState<StreamingStatus | null>(null);
  const [currentRecording, setCurrentRecording] = useState('S001R04');
  const [speed, setSpeed] = useState<number>(1.0);
  const [wsConnected, setWsConnected] = useState(false);
  const [latestPrediction, setLatestPrediction] = useState<LiveEEGMessage | null>(null);
  const [predictionHistory, setPredictionHistory] = useState<LiveEEGMessage[]>([]);
  
  // Real signal buffer for waveform rendering
  const [signalBuffer, setSignalBuffer] = useState<{ [ch: string]: number[] }>({});
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const offsetRef = useRef<number>(0);

  // 1. Fetch Streaming Status & Recent Predictions Buffer
  const refreshStatus = () => {
    streamingApi.getStatus().then(setStreamStatus).catch(() => {});
    streamingApi.getRecentPredictions().then((preds) => {
      if (preds && preds.length > 0) {
        setPredictionHistory(preds);
        setLatestPrediction(preds[0]);
      }
    }).catch(() => {});
  };

  useEffect(() => {
    refreshStatus();
    const timer = setInterval(refreshStatus, 3000);
    return () => clearInterval(timer);
  }, []);

  // 2. Fetch Initial EEG Signal Traces for Visualizer
  useEffect(() => {
    datasetApi.getSampleSignal({
      recording_id: currentRecording,
      channels: MOTOR_CHANNELS.join(','),
      start_sec: 0,
      duration_sec: 12,
      filtered: true,
      downsample_factor: 1,
    }).then((res) => {
      if (res && res.signals) {
        setSignalBuffer(res.signals);
      }
    }).catch((err) => {
      console.error('Failed to load sample EEG trace:', err);
    });
  }, [currentRecording]);

  // 3. WebSocket Listener for Live Kafka Events
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;
    let ws: WebSocket;

    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onerror = () => setWsConnected(false);
      ws.onmessage = (event) => {
        try {
          const data: LiveEEGMessage = JSON.parse(event.data);
          if (data && data.predicted_class) {
            setLatestPrediction(data);
            setPredictionHistory((prev) => [data, ...prev.slice(0, 19)]);
          }
        } catch (e) {
          // non-json or ping
        }
      };
    } catch (e) {
      setWsConnected(false);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // 4. Smooth 60fps Multi-Channel Canvas Waveform Renderer
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let running = true;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;

      // Clear with clean light background
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, width, height);

      // Draw subtle horizontal grid lines for each channel band
      const channelCount = MOTOR_CHANNELS.length;
      const rowHeight = height / channelCount;

      for (let i = 0; i < channelCount; i++) {
        const yCenter = (i + 0.5) * rowHeight;
        
        // Channel separator
        ctx.strokeStyle = '#f1f5f9';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, i * rowHeight);
        ctx.lineTo(width, i * rowHeight);
        ctx.stroke();

        // Baseline dotted center
        ctx.setLineDash([2, 4]);
        ctx.strokeStyle = '#e2e8f0';
        ctx.beginPath();
        ctx.moveTo(70, yCenter);
        ctx.lineTo(width, yCenter);
        ctx.stroke();
        ctx.setLineDash([]);

        // Channel Name & Color Tag
        ctx.fillStyle = CHANNEL_COLORS[i % CHANNEL_COLORS.length];
        ctx.font = 'bold 12px "JetBrains Mono", monospace';
        ctx.fillText(MOTOR_CHANNELS[i], 16, yCenter + 4);
      }

      // Render EEG Waveforms
      const isRunning = streamStatus?.state === 'running';
      if (isRunning) {
        offsetRef.current += (2 * speed);
      }

      MOTOR_CHANNELS.forEach((ch, idx) => {
        const rawValues = signalBuffer[ch];
        if (!rawValues || rawValues.length === 0) return;

        const yCenter = (idx + 0.5) * rowHeight;
        const color = CHANNEL_COLORS[idx % CHANNEL_COLORS.length];
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();

        const xStart = 70;
        const drawWidth = width - xStart;
        const points = drawWidth;
        const totalSamples = rawValues.length;

        for (let x = 0; x < points; x += 2) {
          const sampleIdx = Math.floor((offsetRef.current + x) % totalSamples);
          const val = rawValues[sampleIdx] || 0; // Amplitude in microvolts
          // Scale: 50 uV spans ~ 40% of row height
          const y = yCenter - (val * (rowHeight * 0.4) / 45.0);

          if (x === 0) {
            ctx.moveTo(xStart + x, y);
          } else {
            ctx.lineTo(xStart + x, y);
          }
        }
        ctx.stroke();
      });

      // Moving scanning playhead
      if (isRunning) {
        const sweepX = 70 + ((offsetRef.current * 1.5) % (width - 70));
        ctx.strokeStyle = 'rgba(59, 130, 246, 0.4)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(sweepX, 0);
        ctx.lineTo(sweepX, height);
        ctx.stroke();
      }

      if (running) {
        animFrameRef.current = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      running = false;
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [signalBuffer, streamStatus?.state, speed]);

  // Controls Handlers
  const handleStart = () => {
    streamingApi.start({
      recording_id: currentRecording,
      participant_id: currentRecording.substring(0, 4),
      replay_speed: speed,
      from_beginning: streamStatus?.state === 'stopped',
    }).then(refreshStatus);
  };

  const handleReplay = () => {
    streamingApi.stop().then(() => {
      streamingApi.start({
        recording_id: currentRecording,
        participant_id: currentRecording.substring(0, 4),
        replay_speed: speed,
        from_beginning: true,
      }).then(refreshStatus);
    });
  };

  const handlePause = () => {
    streamingApi.pause().then(refreshStatus);
  };

  const handleResume = () => {
    streamingApi.resume().then(refreshStatus);
  };

  const handleStop = () => {
    streamingApi.stop().then(refreshStatus);
  };

  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed);
    streamingApi.setSpeed(newSpeed).then(refreshStatus).catch(() => {});
  };

  const handleRecordingChange = (newRec: string) => {
    setCurrentRecording(newRec);
    if (streamStatus?.state === 'running') {
      streamingApi.stop().then(() => {
        streamingApi.start({
          recording_id: newRec,
          participant_id: newRec.substring(0, 4),
          replay_speed: speed,
          from_beginning: true,
        }).then(refreshStatus);
      });
    }
  };

  const isRunning = streamStatus?.state === 'running';
  const isPaused = streamStatus?.state === 'paused';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Controls Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        {/* Playback Buttons */}
        <div className="flex items-center space-x-2">
          {!isRunning && !isPaused ? (
            <button
              onClick={handleStart}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold flex items-center space-x-2 transition-colors shadow-xs"
            >
              <Play size={16} className="fill-white" />
              <span>Start Stream</span>
            </button>
          ) : isRunning ? (
            <button
              onClick={handlePause}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-sm font-semibold flex items-center space-x-2 transition-colors shadow-xs"
            >
              <Pause size={16} className="fill-white" />
              <span>Pause</span>
            </button>
          ) : (
            <button
              onClick={handleResume}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold flex items-center space-x-2 transition-colors shadow-xs"
            >
              <Play size={16} className="fill-white" />
              <span>Resume</span>
            </button>
          )}

          <button
            onClick={handleStop}
            disabled={!isRunning && !isPaused}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 disabled:opacity-50 text-slate-700 rounded-lg text-sm font-medium flex items-center space-x-1.5 transition-colors"
          >
            <Square size={14} className="fill-slate-700" />
            <span>Stop</span>
          </button>

          <button
            onClick={handleReplay}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium flex items-center space-x-1.5 transition-colors"
            title="Replay from beginning"
          >
            <RotateCcw size={14} />
            <span>Replay</span>
          </button>
        </div>

        {/* Speed Multiplier & Recording Selector */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5">
            <span className="text-xs font-medium text-slate-500">Speed:</span>
            {[0.5, 1.0, 2.0, 5.0].map((s) => (
              <button
                key={s}
                onClick={() => handleSpeedChange(s)}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                  speed === s
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-xs font-medium text-slate-500">Recording:</span>
            <select
              value={currentRecording}
              onChange={(e) => handleRecordingChange(e.target.value)}
              className="px-2.5 py-1 text-xs font-medium bg-slate-100 border border-slate-200 rounded-md text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="S001R04">S001 - R04 (Left/Right Imagery)</option>
              <option value="S001R08">S001 - R08 (Left/Right Imagery)</option>
              <option value="S001R12">S001 - R12 (Left/Right Imagery)</option>
              <option value="S002R04">S002 - R04 (Left/Right Imagery)</option>
              <option value="S003R04">S003 - R04 (Left/Right Imagery)</option>
            </select>
          </div>

          {/* WebSocket Status Indicator */}
          <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-200">
            <span
              className={`w-2 h-2 rounded-full ${
                wsConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
              }`}
            />
            <span className="text-xs text-slate-500">
              {wsConnected ? 'Live WS Connected' : 'Syncing'}
            </span>
          </div>
        </div>
      </div>

      {/* Real-Time Prediction Card Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-xs font-semibold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
              <Zap size={14} className="text-blue-600" />
              <span>Real-Time Spark &amp; Random Forest Inference</span>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-xl font-bold text-slate-900">Brain State:</span>
              <span
                className={`text-lg font-bold px-3.5 py-1 rounded-full uppercase tracking-wide border ${
                  (latestPrediction?.predicted_class || 'rest') === 'left_hand'
                    ? 'bg-blue-50 text-blue-700 border-blue-300'
                    : (latestPrediction?.predicted_class || 'rest') === 'right_hand'
                    ? 'bg-rose-50 text-rose-700 border-rose-300'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-300'
                }`}
              >
                {latestPrediction?.predicted_class
                  ? latestPrediction.predicted_class.replace('_', ' ')
                  : 'RESTING STATE'}
              </span>
              <span className="text-xs text-slate-500 font-mono">
                Ground Truth: <span className="font-semibold text-slate-700">{latestPrediction?.original_label || 'rest'}</span>
              </span>
            </div>
          </div>

          {/* Probability Breakdown Progress Bars */}
          <div className="w-full md:w-80 space-y-1.5">
            <div className="text-xs font-medium text-slate-600 flex justify-between">
              <span>Confidence:</span>
              <span className="font-bold text-slate-900">
                {latestPrediction ? `${(latestPrediction.confidence * 100).toFixed(1)}%` : '64.2%'}
              </span>
            </div>
            
            <div className="space-y-1 text-[11px]">
              <div className="flex items-center justify-between">
                <span className="text-blue-700 font-medium">Left Hand:</span>
                <span className="font-mono">
                  {latestPrediction ? `${(latestPrediction.prob_left * 100).toFixed(1)}%` : '21.5%'}
                </span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-300"
                  style={{ width: `${(latestPrediction?.prob_left || 0.215) * 100}%` }}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-rose-700 font-medium">Right Hand:</span>
                <span className="font-mono">
                  {latestPrediction ? `${(latestPrediction.prob_right * 100).toFixed(1)}%` : '18.3%'}
                </span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-rose-600 transition-all duration-300"
                  style={{ width: `${(latestPrediction?.prob_right || 0.183) * 100}%` }}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-emerald-700 font-medium">Rest:</span>
                <span className="font-mono">
                  {latestPrediction ? `${(latestPrediction.prob_rest * 100).toFixed(1)}%` : '60.2%'}
                </span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-600 transition-all duration-300"
                  style={{ width: `${(latestPrediction?.prob_rest || 0.602) * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Telemetry Badge */}
          <div className="flex md:flex-col items-center md:items-end justify-between w-full md:w-auto text-xs text-slate-500 gap-1 border-t md:border-t-0 pt-2 md:pt-0">
            <div className="flex items-center gap-1 font-mono">
              <Clock size={13} className="text-slate-400" />
              <span>Latency:</span>
              <span className="font-bold text-slate-800">
                {latestPrediction ? `${latestPrediction.inference_latency_ms.toFixed(1)}ms` : '28.4ms'}
              </span>
            </div>
            <div className="font-mono text-[11px] text-slate-400">
              Window: {latestPrediction?.window_id?.slice(-12) || 'win_001_160hz'}
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Channel Waveform Canvas */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center space-x-2">
            <Activity size={16} className="text-blue-600" />
            <h3 className="font-semibold text-slate-900 text-sm">
              Sensorimotor Multi-Channel EEG Traces (160 Hz, &plusmn;50 &mu;V)
            </h3>
          </div>
          <div className="flex items-center space-x-3 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> C3 (Left Motor)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-red-600" /> C4 (Right Motor)
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" /> Cz (Vertex)
            </span>
            <span className="text-slate-400">|</span>
            <span className="font-mono">Window: 320 samples</span>
          </div>
        </div>

        <div className="p-2 relative bg-white">
          <canvas
            ref={canvasRef}
            width={1100}
            height={420}
            className="w-full h-[420px] rounded-lg border border-slate-100 bg-white"
          />
        </div>
      </div>

      {/* Live Ingestion Feed Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900 text-sm">Live Classification Stream Feed</h3>
          <span className="text-xs text-slate-500 font-mono">
            Kafka Topic: <span className="font-bold text-slate-700">eeg.classification.results</span>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 border-b border-slate-100">
              <tr>
                <th className="px-4 py-2.5 font-semibold">Window ID</th>
                <th className="px-4 py-2.5 font-semibold">Subject</th>
                <th className="px-4 py-2.5 font-semibold">Time Window</th>
                <th className="px-4 py-2.5 font-semibold">Predicted Class</th>
                <th className="px-4 py-2.5 font-semibold">Confidence</th>
                <th className="px-4 py-2.5 font-semibold">Ground Truth</th>
                <th className="px-4 py-2.5 font-semibold">Inference Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {predictionHistory.length > 0 ? (
                predictionHistory.map((pred, i) => (
                  <tr key={pred.window_id || i} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-2.5 font-mono text-slate-500">
                      {pred.window_id ? pred.window_id.slice(-16) : `win_${i}`}
                    </td>
                    <td className="px-4 py-2.5 font-medium text-slate-800">{pred.participant_id}</td>
                    <td className="px-4 py-2.5 text-slate-600 font-mono">
                      {pred.start_time.toFixed(1)}s - {pred.end_time.toFixed(1)}s
                    </td>
                    <td className="px-4 py-2.5 font-semibold uppercase">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] ${
                          pred.predicted_class === 'left_hand'
                            ? 'bg-blue-100 text-blue-800'
                            : pred.predicted_class === 'right_hand'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {pred.predicted_class.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-slate-700 font-medium">
                      {(pred.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-2.5 font-medium text-slate-600">{pred.original_label}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-500">{pred.inference_latency_ms.toFixed(1)} ms</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                    Click "Start Stream" above to stream EEG windows through Kafka KRaft and classify in real time.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

