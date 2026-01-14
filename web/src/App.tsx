import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { supabase } from './lib/supabase';
import type { Session } from '@supabase/supabase-js';
import Home from './pages/Home';
import Subscribe from './pages/Subscribe';
import Stats from './pages/Stats';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import './App.css';

const queryClient = new QueryClient();

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }: { data: { session: Session | null } }) => {
      setSession(session);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event: string, session: Session | null) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app">
          <nav className="navbar">
            <div className="nav-container">
              <Link to="/" className="logo">
                <span className="logo-icon">⚽</span>
                Football Tips
              </Link>
              <div className="nav-links">
                <Link to="/">Home</Link>
                <Link to="/stats">Stats</Link>
                {session ? (
                  <>
                    <Link to="/dashboard">Dashboard</Link>
                    <button
                      onClick={() => supabase.auth.signOut()}
                      className="btn-secondary"
                    >
                      Sign Out
                    </button>
                  </>
                ) : (
                  <>
                    <Link to="/login" className="btn-secondary">
                      Sign In
                    </Link>
                    <Link to="/subscribe" className="btn-primary">
                      Subscribe
                    </Link>
                  </>
                )}
              </div>
            </div>
          </nav>

          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/subscribe" element={<Subscribe session={session} />} />
              <Route path="/stats" element={<Stats />} />
              <Route path="/login" element={<Login />} />
              <Route path="/dashboard" element={<Dashboard session={session} />} />
            </Routes>
          </main>

          <footer className="footer">
            <div className="footer-container">
              <p>&copy; 2024 Football Tips Bot. Premium betting predictions.</p>
              <div className="footer-links">
                <a href="#">Terms</a>
                <a href="#">Privacy</a>
                <a href="#">Contact</a>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
