import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { AppShell } from './components/layout/AppShell';

// Pages
import { LoginPage } from './pages/Login/LoginPage';
import { CommandCenterPage } from './pages/CommandCenter/CommandCenterPage';
import { DataEnginePage } from './pages/DataEngine/DataEnginePage';
import { DatasetDetailPage } from './pages/DataEngine/DatasetDetailPage';
import { MarineMapPage } from './pages/MarineMap/MarineMapPage';
import { OceanExplorerPage } from './pages/OceanExplorer/OceanExplorerPage';
import { FisheriesExplorerPage } from './pages/FisheriesExplorer/FisheriesExplorerPage';
import { SpeciesExplorerPage } from './pages/SpeciesExplorer/SpeciesExplorerPage';
import { EDNAExplorerPage } from './pages/EDNAExplorer/EDNAExplorerPage';
import { ScientificAnalysisPage } from './pages/ScientificAnalysis/ScientificAnalysisPage';
import { AIInsightsPage } from './pages/AIInsights/AIInsightsPage';
import { AlertsPage } from './pages/Alerts/AlertsPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Login Route */}
            <Route path="/login" element={<LoginPage />} />

            {/* Authenticated Application Shell */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                {/* 1. Command Center (Root) */}
                <Route path="/" element={<CommandCenterPage />} />

                {/* 2. Data Engine (Upload & Explorer) */}
                <Route path="/data" element={<DataEnginePage />} />
                <Route path="/data/upload" element={<DataEnginePage />} />
                <Route path="/data/datasets" element={<DataEnginePage />} />
                <Route path="/data/datasets/:datasetId" element={<DatasetDetailPage />} />

                {/* 3. Marine Research Map (2D Spatial Workspace) */}
                <Route path="/map" element={<MarineMapPage />} />

                {/* 4. Domain Explorers */}
                <Route path="/ocean" element={<OceanExplorerPage />} />
                <Route path="/fisheries" element={<FisheriesExplorerPage />} />
                <Route path="/species" element={<SpeciesExplorerPage />} />
                <Route path="/edna" element={<EDNAExplorerPage />} />

                {/* 5. Scientific Analysis Workspace */}
                <Route path="/analysis" element={<ScientificAnalysisPage />} />

                {/* 6. AI Insights & Decision Support */}
                <Route path="/ai-insights" element={<AIInsightsPage />} />

                {/* 7. Alerts & Hazards */}
                <Route path="/alerts" element={<AlertsPage />} />
              </Route>
            </Route>

            {/* Fallback Redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
};

export default App;
