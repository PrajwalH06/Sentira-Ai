import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import SubmitFeedback from './pages/SubmitFeedback';
import FeedbackList from './pages/FeedbackList';
import Trends from './pages/Trends';
import Insights from './pages/Insights';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/submit" element={<SubmitFeedback />} />
            <Route path="/feedbacks" element={<FeedbackList />} />
            <Route path="/trends" element={<Trends />} />
            <Route path="/insights" element={<Insights />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
