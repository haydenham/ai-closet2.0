import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { HomePage, FeatureExtractionPage, LoginPage, RecommendationsPage, ClosetPage, AddItemPage } from './pages'
import { RegisterPage } from './pages/RegisterPage'
import { QuizPage } from './pages/QuizPage'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/features" element={<FeatureExtractionPage />} />
            <Route path="/quiz" element={<ProtectedRoute><QuizPage /></ProtectedRoute>} />
            <Route path="/recommendations" element={<ProtectedRoute><RecommendationsPage /></ProtectedRoute>} />
            <Route path="/closet" element={<ProtectedRoute><ClosetPage /></ProtectedRoute>} />
            <Route path="/closet/add" element={<ProtectedRoute><AddItemPage /></ProtectedRoute>} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App