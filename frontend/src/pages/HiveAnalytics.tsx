import React, { useState, useEffect } from 'react';
import {
  Database,
  Play,
  RotateCcw,
  Download,
  Table,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  ChevronRight,
  ChevronDown,
  Terminal
} from 'lucide-react';
import { hiveApi } from '../services/api';
import { HiveQueryResult } from '../types';

const SAMPLE_QUERIES = [
  {
    title: 'Q1: Total Windows per Subject',
    sql: `SELECT participant_id, COUNT(*) AS total_windows
FROM eeg_window_features
GROUP BY participant_id
ORDER BY total_windows DESC`
  },
  {
    title: 'Q2: Predicted Brain States',
    sql: `SELECT predicted_class, COUNT(*) AS count, ROUND(AVG(confidence), 4) AS avg_confidence
FROM eeg_classification_results
GROUP BY predicted_class`
  },
  {
    title: 'Q3: Band Power by Brain State',
    sql: `SELECT 
    c.predicted_class,
    ROUND(AVG(f.delta_power), 2) AS avg_delta,
    ROUND(AVG(f.theta_power), 2) AS avg_theta,
    ROUND(AVG(f.alpha_power), 2) AS avg_alpha,
    ROUND(AVG(f.beta_power), 2) AS avg_beta,
    ROUND(AVG(f.gamma_power), 2) AS avg_gamma
FROM eeg_window_features f
JOIN eeg_classification_results c ON f.window_id = c.window_id
GROUP BY c.predicted_class`
  },
  {
    title: 'Q4: Channel Activity Rankings',
    sql: `SELECT 
    channel_name,
    ROUND(AVG(mean), 3) AS avg_mean,
    ROUND(AVG(variance), 2) AS avg_variance,
    ROUND(AVG(alpha_power), 2) AS avg_alpha,
    ROUND(AVG(beta_power), 2) AS avg_beta
FROM eeg_channel_statistics
GROUP BY channel_name
ORDER BY avg_beta DESC
LIMIT 15`
  },
  {
    title: 'Q5: Subject Prediction Distribution',
    sql: `SELECT 
    participant_id,
    predicted_class,
    COUNT(*) AS prediction_count
FROM eeg_classification_results
GROUP BY participant_id, predicted_class
ORDER BY participant_id, prediction_count DESC`
  },
  {
    title: 'Q6: Task-wise Beta/Alpha Ratio',
    sql: `SELECT 
    original_label,
    COUNT(*) AS window_count,
    ROUND(AVG(alpha_power), 2) AS avg_alpha,
    ROUND(AVG(beta_power), 2) AS avg_beta,
    ROUND(AVG(beta_power / NULLIF(alpha_power, 0)), 3) AS beta_alpha_ratio
FROM eeg_window_features
GROUP BY original_label`
  },
  {
    title: 'Q7: Temporal Prediction Rates',
    sql: `SELECT 
    SUBSTR(classification_timestamp, 1, 16) AS time_minute,
    COUNT(*) AS predictions_per_minute,
    ROUND(AVG(inference_latency_ms), 2) AS avg_latency_ms
FROM eeg_classification_results
GROUP BY SUBSTR(classification_timestamp, 1, 16)
ORDER BY time_minute DESC
LIMIT 20`
  },
  {
    title: 'Q8: Predictions by Recording',
    sql: `SELECT 
    recording_id,
    COUNT(*) AS total_predictions,
    SUM(CASE WHEN predicted_class = 'left_hand' THEN 1 ELSE 0 END) AS left_hand_count,
    SUM(CASE WHEN predicted_class = 'right_hand' THEN 1 ELSE 0 END) AS right_hand_count,
    SUM(CASE WHEN predicted_class = 'rest' THEN 1 ELSE 0 END) AS rest_count
FROM eeg_classification_results
GROUP BY recording_id
ORDER BY total_predictions DESC`
  }
];

export const HiveAnalytics: React.FC = () => {
  const [query, setQuery] = useState(SAMPLE_QUERIES[0].sql);
  const [result, setResult] = useState<HiveQueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [tableSchema, setTableSchema] = useState<any[]>([]);

  useEffect(() => {
    hiveApi.getTables().then((res) => {
      if (res && res.tables) setTables(res.tables);
    }).catch(() => {});
  }, []);

  const handleExecute = () => {
    const cleanQuery = query.trim().replace(/;+\s*$/, '');
    if (!cleanQuery) return;
    setLoading(true);
    hiveApi.executeQuery(cleanQuery)
      .then((res) => {
        setResult(res);
        setLoading(false);
      })
      .catch((err) => {
        setResult({
          success: false,
          columns: [],
          rows: [],
          row_count: 0,
          execution_time_ms: 0,
          query: query,
          error: err.response?.data?.detail || err.message || 'Execution error'
        });
        setLoading(false);
      });
  };

  const handleSelectTable = (tbl: string) => {
    if (selectedTable === tbl) {
      setSelectedTable(null);
    } else {
      setSelectedTable(tbl);
      hiveApi.getSchema(tbl).then((s) => {
        if (s && s.schema) setTableSchema(s.schema);
      }).catch(() => setTableSchema([]));
    }
  };

  const exportCSV = () => {
    if (!result || !result.rows.length) return;
    const header = result.columns.join(',');
    const rows = result.rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([`${header}\n${rows}`], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hive_query_result_${Date.now()}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Database size={20} className="text-blue-600" />
            <span>Apache Hive SQL Analytics Console</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Execute SQL queries against Apache Hive external tables stored as Parquet in Hadoop HDFS
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 font-mono">
          <span>Database: <strong>neurostream_db</strong></span>
          <span>&bull;</span>
          <span>Format: <strong>Parquet</strong></span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Column: Sample Queries & Schema Explorer */}
        <div className="lg:col-span-1 space-y-5">
          {/* Preset Queries */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Sample Analytical Queries
            </h3>
            <div className="space-y-1">
              {SAMPLE_QUERIES.map((sq, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(sq.sql)}
                  className="w-full text-left px-2.5 py-1.5 rounded text-xs font-medium text-slate-700 hover:bg-blue-50 hover:text-blue-700 transition-colors truncate"
                  title={sq.title}
                >
                  {sq.title}
                </button>
              ))}
            </div>
          </div>

          {/* Tables Schema Explorer */}
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Hive Tables Explorer
            </h3>
            <div className="space-y-1.5 text-xs font-mono">
              {tables.map((t) => (
                <div key={t} className="border border-slate-100 rounded-lg overflow-hidden">
                  <button
                    onClick={() => handleSelectTable(t)}
                    className="w-full px-2.5 py-2 bg-slate-50 hover:bg-slate-100 flex items-center justify-between text-left font-semibold text-slate-800"
                  >
                    <span className="truncate">{t}</span>
                    {selectedTable === t ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>
                  {selectedTable === t && (
                    <div className="p-2 bg-white divide-y divide-slate-100 text-[11px] max-h-48 overflow-y-auto">
                      {tableSchema.map((col, idx) => (
                        <div key={idx} className="py-1 flex justify-between">
                          <span className="text-blue-600 font-medium">{col.column}</span>
                          <span className="text-slate-400">{col.type}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: SQL Editor & Results View */}
        <div className="lg:col-span-3 space-y-5">
          {/* SQL Editor */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-700">
                <Terminal size={14} className="text-blue-600" />
                <span>HiveServer2 Query Editor</span>
              </div>
              <button
                onClick={handleExecute}
                disabled={loading}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-xs font-bold flex items-center space-x-1.5 transition-colors shadow-xs"
              >
                <Play size={13} className="fill-white" />
                <span>{loading ? 'Executing...' : 'Run Query'}</span>
              </button>
            </div>

            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={6}
              className="w-full p-4 font-mono text-xs text-slate-800 bg-white focus:outline-none resize-none"
              placeholder="SELECT * FROM eeg_window_features LIMIT 10;"
            />
          </div>

          {/* Results Area */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center space-x-3 text-xs">
                <span className="font-bold text-slate-900">Query Results</span>
                {result && (
                  <span className="text-slate-500 font-mono">
                    {result.row_count} rows &bull; {result.execution_time_ms} ms
                  </span>
                )}
              </div>
              {result && result.rows.length > 0 && (
                <button
                  onClick={exportCSV}
                  className="px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded flex items-center space-x-1.5 transition-colors"
                >
                  <Download size={13} />
                  <span>Export CSV</span>
                </button>
              )}
            </div>

            {loading ? (
              <div className="h-64 flex flex-col items-center justify-center text-slate-400 text-xs space-y-2">
                <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                <span>Submitting MapReduce / Tez execution plan to HiveServer2...</span>
              </div>
            ) : result?.error ? (
              <div className="p-5 text-xs text-rose-600 bg-rose-50 border-t border-rose-100 font-mono whitespace-pre-wrap">
                {result.error}
              </div>
            ) : result && result.rows.length > 0 ? (
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 sticky top-0">
                    <tr>
                      {result.columns.map((col, idx) => (
                        <th key={idx} className="px-4 py-2.5 font-bold uppercase text-[11px]">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {result.rows.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-50">
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="px-4 py-2 text-slate-800">
                            {cell !== null && cell !== undefined ? String(cell) : 'NULL'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-400 text-xs">
                No query executed yet. Select a query and click "Run Query".
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

