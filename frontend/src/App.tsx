import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { Overview } from './pages/Overview';
import { LiveMonitoring } from './pages/LiveMonitoring';
import { EEGExplorer } from './pages/EEGExplorer';
import { BrainStateClassification } from './pages/BrainStateClassification';
import { SignalAnalytics } from './pages/SignalAnalytics';
import { Participants } from './pages/Participants';
import { HiveAnalytics } from './pages/HiveAnalytics';
import { ModelEvaluation } from './pages/ModelEvaluation';
import { SystemMonitoring } from './pages/SystemMonitoring';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Overview />} />
          <Route path="live" element={<LiveMonitoring />} />
          <Route path="explorer" element={<EEGExplorer />} />
          <Route path="classification" element={<BrainStateClassification />} />
          <Route path="analytics" element={<SignalAnalytics />} />
          <Route path="participants" element={<Participants />} />
          <Route path="hive" element={<HiveAnalytics />} />
          <Route path="model" element={<ModelEvaluation />} />
          <Route path="system" element={<SystemMonitoring />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;

