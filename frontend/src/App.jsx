import { Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import EvaluationDetails from './pages/EvaluationDetails';
import EvaluationHistory from './pages/EvaluationHistory';
import HelpSupport from './pages/HelpSupport';
import Home from './pages/Home';
import Reports from './pages/Reports';
import NewEvaluation from './pages/NewEvaluation';

export default function App() {
  return <AppLayout><Routes><Route path="/" element={<Home />} /><Route path="/evaluate" element={<NewEvaluation />} /><Route path="/evaluations" element={<EvaluationHistory />} /><Route path="/evaluations/:evaluationId" element={<EvaluationDetails />} /><Route path="/reports" element={<Reports />} /><Route path="/help" element={<HelpSupport />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></AppLayout>;
}
