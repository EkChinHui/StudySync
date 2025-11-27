import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './components/Toast'
import Landing from './pages/Landing'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Session from './pages/Session'
import Quiz from './pages/Quiz'

function App() {
  return (
    <ToastProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/dashboard/:id" element={<Dashboard />} />
          <Route path="/session/:id" element={<Session />} />
          <Route path="/quiz/:moduleId" element={<Quiz />} />
        </Routes>
      </Router>
    </ToastProvider>
  )
}

export default App
