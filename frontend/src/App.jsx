import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import EvaluationDetails from './pages/EvaluationDetails';
import EvaluationHistory from './pages/EvaluationHistory';
import NewEvaluation from './pages/NewEvaluation';

export default function App() {
  return <AppLayout><Routes><Route path="/" element={<Dashboard />} /><Route path="/evaluate" element={<NewEvaluation />} /><Route path="/evaluations" element={<EvaluationHistory />} /><Route path="/evaluations/:evaluationId" element={<EvaluationDetails />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></AppLayout>;
}
