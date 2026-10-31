import React from 'react';
import {
  Settings as SettingsIcon,
  ShieldAlert,
  BookOpen,
  Sliders,
  Database,
  ExternalLink,
  Info
} from 'lucide-react';

export const Settings: React.FC = () => {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <SettingsIcon size={20} className="text-blue-600" />
          <span>NeuroStream Platform Settings &amp; Academic Manifest</span>
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          System parameters, distributed cluster configurations, and dataset references
        </p>
      </div>

      {/* Clinical Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl text-xs text-amber-800 space-y-1">
        <div className="flex items-center space-x-2 font-bold text-amber-900">
          <ShieldAlert size={16} className="text-amber-600" />
          <span>Research &amp; Academic Demonstration Notice</span>
        </div>
        <p className="leading-relaxed text-amber-800">
          NeuroStream is an educational distributed systems microproject developed to demonstrate real-time big data pipelines (Kafka KRaft, Apache Spark, Hadoop HDFS, and Apache Hive). 
          <strong> It is not certified for clinical, medical, or diagnostic usage.</strong>
        </p>
      </div>

      {/* Pipeline Configuration Parameters */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <h3 className="font-semibold text-slate-900 text-sm">Streaming &amp; Extraction Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
            <span className="text-slate-500 font-medium">Sampling Rate (PhysioNet)</span>
            <div className="font-mono font-bold text-slate-900 text-sm">160 Hz (6.25 ms period)</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
            <span className="text-slate-500 font-medium">Sliding Window Duration</span>
            <div className="font-mono font-bold text-slate-900 text-sm">2.0 seconds (320 samples)</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
            <span className="text-slate-500 font-medium">Window Overlap Ratio</span>
            <div className="font-mono font-bold text-slate-900 text-sm">50% (1.0s step size = 160 samples)</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-1">
            <span className="text-slate-500 font-medium">Digital Filtering</span>
            <div className="font-mono font-bold text-slate-900 text-sm">Butterworth 0.5–45 Hz Bandpass + 60 Hz Notch</div>
          </div>
        </div>
      </div>

      {/* Dataset Attribution */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
        <h3 className="font-semibold text-slate-900 text-sm flex items-center gap-2">
          <BookOpen size={16} className="text-blue-600" />
          <span>PhysioNet EEGMMIDB Dataset Citation</span>
        </h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          Schalk, G., McFarland, D.J., Hinterberger, T., Birbaumer, N., Wolpaw, J.R. BCI2000: A General-Purpose Brain-Computer Interface (BCI) System. IEEE Transactions on Biomedical Engineering 51(6):1034-1043, 2004.
        </p>
        <p className="text-xs text-slate-600 leading-relaxed">
          Goldberger, A., Amaral, L., Glass, L., Hausdorff, J., Ivanov, P. C., Mark, R., ... &amp; Stanley, H. E. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. Circulation 101 (23), pp. e215–e220.
        </p>
        <a
          href="https://physionet.org/content/eegmmidb/1.0.0/"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center space-x-1.5 text-xs text-blue-600 hover:text-blue-700 font-medium"
        >
          <span>Official PhysioNet EEGMMIDB Repository</span>
          <ExternalLink size={12} />
        </a>
      </div>
    </div>
  );
};

