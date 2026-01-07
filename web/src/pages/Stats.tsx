import { useQuery } from '@tanstack/react-query';
import { getPredictionHistory } from '../lib/api';
import { useState } from 'react';

export default function Stats() {
  const [days, setDays] = useState(7);

  const { data, isLoading } = useQuery({
    queryKey: ['prediction-history', days],
    queryFn: () => getPredictionHistory(days),
  });

  const predictions = data?.predictions || [];

  const stats = predictions.reduce(
    (acc: any, pred: any) => {
      if (pred.is_settled) {
        acc.total++;
        if (pred.actual_result === pred.recommended_bet.toLowerCase()) {
          acc.won++;
        } else {
          acc.lost++;
        }
      }
      return acc;
    },
    { total: 0, won: 0, lost: 0 }
  );

  const winRate = stats.total > 0 ? ((stats.won / stats.total) * 100).toFixed(1) : '0.0';

  return (
    <div className="stats-page">
      <section className="stats-header">
        <h1>Performance Statistics</h1>
        <p>Track our prediction accuracy and results</p>
      </section>

      <section className="stats-controls">
        <div className="time-selector">
          <button
            className={days === 7 ? 'active' : ''}
            onClick={() => setDays(7)}
          >
            Last 7 Days
          </button>
          <button
            className={days === 30 ? 'active' : ''}
            onClick={() => setDays(30)}
          >
            Last 30 Days
          </button>
          <button
            className={days === 90 ? 'active' : ''}
            onClick={() => setDays(90)}
          >
            Last 90 Days
          </button>
        </div>
      </section>

      <section className="stats-summary">
        <div className="stats-cards">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Predictions</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{stats.won}</div>
            <div className="stat-label">Winning Tips</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-value">{stats.lost}</div>
            <div className="stat-label">Losing Tips</div>
          </div>
          <div className="stat-card primary">
            <div className="stat-value">{winRate}%</div>
            <div className="stat-label">Win Rate</div>
          </div>
        </div>
      </section>

      <section className="recent-predictions">
        <div className="container">
          <h2>Recent Predictions</h2>
          {isLoading ? (
            <div className="loading">Loading...</div>
          ) : (
            <div className="predictions-table">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Match</th>
                    <th>Tip</th>
                    <th>Odds</th>
                    <th>Edge</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {predictions.slice(0, 20).map((pred: any) => (
                    <tr key={pred.id}>
                      <td>{new Date(pred.match_time).toLocaleDateString()}</td>
                      <td>
                        {pred.home_team} vs {pred.away_team}
                      </td>
                      <td>{pred.recommended_bet}</td>
                      <td>
                        {pred.recommended_bet === 'Home' && pred.odds_home}
                        {pred.recommended_bet === 'Draw' && pred.odds_draw}
                        {pred.recommended_bet === 'Away' && pred.odds_away}
                      </td>
                      <td className="positive">+{(pred.edge * 100).toFixed(1)}%</td>
                      <td>
                        {pred.is_settled ? (
                          <span
                            className={`result-badge ${
                              pred.actual_result === pred.recommended_bet.toLowerCase()
                                ? 'won'
                                : 'lost'
                            }`}
                          >
                            {pred.actual_result === pred.recommended_bet.toLowerCase()
                              ? 'Won'
                              : 'Lost'}
                          </span>
                        ) : (
                          <span className="result-badge pending">Pending</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
