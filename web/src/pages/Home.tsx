import { useQuery } from '@tanstack/react-query';
import { getTopPredictions } from '../lib/api';
import { Link } from 'react-router-dom';

export default function Home() {
  const { data, isLoading } = useQuery({
    queryKey: ['top-predictions'],
    queryFn: () => getTopPredictions(5),
  });

  return (
    <div className="home-page">
      <section className="hero">
        <div className="hero-content">
          <h1>Premium Football Betting Tips</h1>
          <p className="hero-subtitle">
            AI-powered predictions with proven track record. Get daily tips with the best value bets.
          </p>
          <div className="hero-cta">
            <Link to="/subscribe" className="btn-primary btn-large">
              Start Subscription
            </Link>
            <Link to="/stats" className="btn-secondary btn-large">
              View Statistics
            </Link>
          </div>
        </div>
      </section>

      <section className="features">
        <div className="container">
          <h2>Why Choose Our Tips?</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Data-Driven</h3>
              <p>Advanced machine learning models analyze thousands of matches</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3>Real-Time Updates</h3>
              <p>Live match analysis and in-play betting opportunities</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>Value Betting</h3>
              <p>Find the best edges against bookmaker odds</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📱</div>
              <h3>Telegram Bot</h3>
              <p>Get instant notifications via our Telegram bot</p>
            </div>
          </div>
        </div>
      </section>

      <section className="today-tips">
        <div className="container">
          <h2>Today's Top Value Bets</h2>
          {isLoading ? (
            <div className="loading">Loading predictions...</div>
          ) : (
            <div className="predictions-list">
              {data?.predictions?.slice(0, 3).map((pred: any) => (
                <div key={pred.id} className="prediction-card">
                  <div className="match-teams">
                    <span className="team">{pred.home_team}</span>
                    <span className="vs">vs</span>
                    <span className="team">{pred.away_team}</span>
                  </div>
                  <div className="prediction-details">
                    <div className="bet-recommendation">
                      <span className="label">Recommended:</span>
                      <span className="value">{pred.recommended_bet}</span>
                    </div>
                    <div className="odds">
                      <span className="label">Odds:</span>
                      <span className="value">
                        {pred.recommended_bet === 'Home' && pred.odds_home}
                        {pred.recommended_bet === 'Draw' && pred.odds_draw}
                        {pred.recommended_bet === 'Away' && pred.odds_away}
                      </span>
                    </div>
                    <div className="edge">
                      <span className="label">Edge:</span>
                      <span className="value positive">+{(pred.edge * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              ))}
              <div className="blur-overlay">
                <div className="unlock-message">
                  <Link to="/subscribe" className="btn-primary">
                    Subscribe to See All Predictions
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Start Winning?</h2>
          <p>Join hundreds of successful bettors using our premium tips</p>
          <Link to="/subscribe" className="btn-primary btn-large">
            Get Started Now
          </Link>
        </div>
      </section>
    </div>
  );
}
