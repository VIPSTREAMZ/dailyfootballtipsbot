import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPlans, createCheckoutSession } from '../lib/api';
import { useNavigate } from 'react-router-dom';

export default function Subscribe({ session }: { session: any }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState<string | null>(null);

  const { data: plansData } = useQuery({
    queryKey: ['plans'],
    queryFn: getPlans,
  });

  const handleSubscribe = async (planId: string) => {
    if (!session) {
      navigate('/login?redirect=/subscribe');
      return;
    }

    setLoading(planId);

    try {
      const result = await createCheckoutSession(
        planId,
        session.user.id,
        `${window.location.origin}/dashboard?success=true`,
        `${window.location.origin}/subscribe?cancelled=true`
      );

      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      alert('Failed to start checkout. Please try again.');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="subscribe-page">
      <section className="pricing-hero">
        <h1>Choose Your Plan</h1>
        <p>Get access to premium betting tips and analysis</p>
      </section>

      <section className="pricing-plans">
        <div className="plans-container">
          {plansData?.plans?.map((plan: any) => (
            <div
              key={plan.id}
              className={`plan-card ${plan.id === 'yearly' ? 'featured' : ''}`}
            >
              {plan.discount && <div className="plan-badge">{plan.discount}</div>}
              <h3>{plan.name}</h3>
              <div className="plan-price">
                <span className="currency">$</span>
                <span className="amount">{plan.price}</span>
                <span className="period">/{plan.duration}</span>
              </div>
              <ul className="plan-features">
                {plan.features.map((feature: string, idx: number) => (
                  <li key={idx}>
                    <span className="check">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>
              <button
                className="btn-primary btn-large"
                onClick={() => handleSubscribe(plan.id)}
                disabled={loading === plan.id}
              >
                {loading === plan.id ? 'Loading...' : 'Subscribe Now'}
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="faq-section">
        <div className="container">
          <h2>Frequently Asked Questions</h2>
          <div className="faq-list">
            <div className="faq-item">
              <h3>How do the predictions work?</h3>
              <p>
                Our advanced machine learning models analyze historical data, team performance,
                player statistics, and odds to identify value betting opportunities.
              </p>
            </div>
            <div className="faq-item">
              <h3>Can I cancel anytime?</h3>
              <p>
                Yes, you can cancel your subscription at any time. Your access will continue
                until the end of your billing period.
              </p>
            </div>
            <div className="faq-item">
              <h3>Do you guarantee wins?</h3>
              <p>
                No betting system can guarantee wins. However, our tips focus on value betting
                and long-term profitability based on statistical edge.
              </p>
            </div>
            <div className="faq-item">
              <h3>How do I receive tips?</h3>
              <p>
                You can access tips through our website dashboard or via our Telegram bot
                for instant notifications.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
