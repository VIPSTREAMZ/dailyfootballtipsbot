import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { getPreMatchPredictions } from '../lib/api';
import type { Session } from '@supabase/supabase-js';

export default function Dashboard({ session }: { session: Session | null }) {
  const navigate = useNavigate();
  const [subscription, setSubscription] = useState<any>(null);
  const [loadingSub, setLoadingSub] = useState(true);

  useEffect(() => {
    if (!session) {
      navigate('/login?redirect=/dashboard');
      return;
    }

    const fetchSubscription = async () => {
      try {
        const { data, error } = await supabase
          .from('subscriptions')
          .select('*')
          .eq('user_id', session.user.id)
          .eq('status', 'active')
          .gte('valid_until', new Date().toISOString())
          .maybeSingle();

        if (!error && data) {
          setSubscription(data);
        }
      } catch (err) {
        console.error('Error fetching subscription:', err);
      } finally {
        setLoadingSub(false);
      }
    };

    fetchSubscription();
  }, [session, navigate]);

  const { data: predictionsData, isLoading: predictionsLoading } = useQuery({
    queryKey: ['predictions'],
    queryFn: () => getPreMatchPredictions(10),
    enabled: !!subscription,
  });

  if (!session) {
    return null;
  }

  if (loadingSub) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="dashboard-page">
        <div className="no-subscription">
          <h2>No Active Subscription</h2>
          <p>You need an active subscription to access the dashboard.</p>
          <button
            className="btn-primary"
            onClick={() => navigate('/subscribe')}
          >
            Subscribe Now
          </button>
        </div>
      </div>
    );
  }

  const validUntil = new Date(subscription.valid_until);
  const daysRemaining = Math.ceil(
    (validUntil.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="dashboard-page">
      <section className="dashboard-header">
        <div className="user-info">
          <h1>Welcome back!</h1>
          <p>{session.user.email}</p>
        </div>
        <div className="subscription-info">
          <div className="sub-badge">
            <span className="badge-label">Subscription</span>
            <span className="badge-value">{subscription.plan_type}</span>
          </div>
          <div className="sub-status">
            <span className="status-icon">✓</span>
            <span>{daysRemaining} days remaining</span>
          </div>
        </div>
      </section>

      <section className="dashboard-content">
        <div className="content-header">
          <h2>Today's Premium Tips</h2>
          <p>Value betting opportunities with positive edge</p>
        </div>

        {predictionsLoading ? (
          <div className="loading">Loading predictions...</div>
        ) : (
          <div className="predictions-grid">
            {predictionsData?.results?.map((pred: any) => (
              <div key={pred.match_id} className="prediction-card-full">
                <div className="card-header">
                  <div className="match-info">
                    <h3>
                      {pred.home} <span className="vs">vs</span> {pred.away}
                    </h3>
                    <p className="match-time">
                      {new Date(pred.start_time).toLocaleString()}
                    </p>
                  </div>
                  <div className="match-id">ID: {pred.match_id}</div>
                </div>

                <div className="card-body">
                  <div className="probabilities">
                    <div className="prob-item">
                      <span className="label">Home</span>
                      <span className="value">{(pred.model_probs.home * 100).toFixed(1)}%</span>
                      <span className="odds">{pred.odds.home}</span>
                    </div>
                    <div className="prob-item">
                      <span className="label">Draw</span>
                      <span className="value">{(pred.model_probs.draw * 100).toFixed(1)}%</span>
                      <span className="odds">{pred.odds.draw}</span>
                    </div>
                    <div className="prob-item">
                      <span className="label">Away</span>
                      <span className="value">{(pred.model_probs.away * 100).toFixed(1)}%</span>
                      <span className="odds">{pred.odds.away}</span>
                    </div>
                  </div>

                  <div className="recommendation">
                    <div className="rec-header">
                      <span className="icon">🎯</span>
                      <span className="title">Recommended Bet</span>
                    </div>
                    <div className="rec-details">
                      <span className="bet-side">{pred.best_market.side}</span>
                      <span className="bet-odds">@ {pred.best_market.book_odds}</span>
                      <span className="bet-edge positive">
                        Edge: +{(pred.best_market.edge * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="telegram-section">
        <div className="telegram-card">
          <h3>Get Instant Notifications</h3>
          <p>Connect with our Telegram bot for real-time updates and live match analysis</p>
          <a
            href="https://t.me/YourBotUsername"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
          >
            Open Telegram Bot
          </a>
        </div>
      </section>
    </div>
  );
}
