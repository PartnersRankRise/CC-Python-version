'use client';

// Created: Thursday Jul 23, 2026, 2:44 PM (UTC-6)
// Last edited: Thursday Jul 23, 2026, 2:44 PM (UTC-6)

import { useState, useEffect } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';

interface ContentSample {
  type: 'text' | 'url';
  content?: string;
  url?: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const clientId = params.clientId as string;
  const shouldRegenerate = searchParams.get('regenerate') === 'true';

  const [activeTab, setActiveTab] = useState<'text' | 'url'>('text');
  const [formData, setFormData] = useState({
    textContent: '',
    urlContent: '',
    serviceArea: '',
    offLimitTopics: '',
    regenerate: shouldRegenerate,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<'queued' | 'running' | 'complete' | 'failed' | null>(null);
  const [progress, setProgress] = useState<string>('');
  const [pollCount, setPollCount] = useState(0);

  // Poll job status
  useEffect(() => {
    if (!jobId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/jobs/${jobId}`);
        if (!response.ok) throw new Error('Failed to fetch job status');

        const data = await response.json();
        setJobStatus(data.status);
        setProgress(data.progress || '');

        if (data.status === 'complete') {
          // Redirect to client page with success
          router.push(`/clients/${clientId}?onboarding=success`);
          clearInterval(pollInterval);
        } else if (data.status === 'failed') {
          setError(data.error || 'Onboarding failed. Please try again.');
          setLoading(false);
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('Poll error:', err);
      }

      setPollCount(prev => prev + 1);
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [jobId, clientId, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Build content samples
      const contentSamples: ContentSample[] = [];

      if (activeTab === 'text' && formData.textContent.trim()) {
        contentSamples.push({
          type: 'text',
          content: formData.textContent,
        });
      } else if (activeTab === 'url' && formData.urlContent.trim()) {
        contentSamples.push({
          type: 'url',
          url: formData.urlContent,
        });
      }

      if (contentSamples.length === 0) {
        throw new Error('Please provide at least one content sample');
      }

      // POST /clients/{clientId}/onboard
      const response = await fetch(`/api/clients/${clientId}/onboard`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_samples: contentSamples,
          additional_context: {
            service_area: formData.serviceArea || undefined,
            off_limits_topics: formData.offLimitTopics
              ? formData.offLimitTopics.split(',').map(t => t.trim()).filter(Boolean)
              : [],
          },
          regenerate: formData.regenerate,
        }),
      });

      if (response.status === 409) {
        const data = await response.json();
        throw new Error(data.suggestion || 'Client is already fully onboarded');
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start onboarding');
      }

      const data = await response.json();
      setJobId(data.job_id);
      setJobStatus('queued');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  // Show polling UI
  if (jobId && jobStatus) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
        <div className="max-w-lg mx-auto">
          <div className="bg-slate-800 rounded-lg shadow-lg p-6 border border-slate-700 text-center">
            <h2 className="text-2xl font-bold text-white mb-6">Onboarding in Progress</h2>

            {/* Status Badge */}
            <div className="mb-6">
              <div className="inline-block px-4 py-2 rounded-full bg-blue-900/30 border border-blue-700 text-blue-300 text-sm font-medium">
                {jobStatus === 'queued' && '⏳ Queued'}
                {jobStatus === 'running' && '⚙️ Running'}
                {jobStatus === 'complete' && '✓ Complete'}
                {jobStatus === 'failed' && '✗ Failed'}
              </div>
            </div>

            {/* Progress */}
            {progress && (
              <div className="mb-4">
                <p className="text-slate-300">{progress}</p>
              </div>
            )}

            {/* Progress Bar */}
            <div className="w-full bg-slate-700 rounded-full h-2 mb-4">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{
                  width: jobStatus === 'complete' ? '100%' : jobStatus === 'running' ? '60%' : '20%',
                }}
              />
            </div>

            {/* Poll Count */}
            <p className="text-xs text-slate-500">Polls: {pollCount}</p>

            {/* Error Display */}
            {error && (
              <div className="mt-4 bg-red-900/20 border border-red-700 rounded p-3 text-red-300 text-sm">
                {error}
                <button
                  onClick={() => {
                    setJobId(null);
                    setJobStatus(null);
                    setError(null);
                    setLoading(false);
                  }}
                  className="mt-2 text-red-400 hover:text-red-300 underline"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Show form UI
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href={`/clients/${clientId}`} className="text-blue-400 hover:text-blue-300 text-sm mb-4 inline-block">
            ← Back to Client
          </Link>
          <h1 className="text-3xl font-bold text-white mb-2">Onboard Client</h1>
          <p className="text-slate-300">Provide content samples to generate reference materials.</p>
        </div>

        {/* Form */}
        <div className="bg-slate-800 rounded-lg shadow-lg p-6 border border-slate-700">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Error Alert */}
            {error && (
              <div className="bg-red-900/20 border border-red-700 rounded p-3 text-red-300 text-sm">
                {error}
              </div>
            )}

            {/* Content Samples Tabs */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">
                Content Samples <span className="text-red-400">*</span>
              </label>
              <div className="flex gap-2 mb-4">
                <button
                  type="button"
                  onClick={() => setActiveTab('text')}
                  className={`flex-1 py-2 px-3 rounded transition-colors text-sm font-medium ${
                    activeTab === 'text'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  Paste Text
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('url')}
                  className={`flex-1 py-2 px-3 rounded transition-colors text-sm font-medium ${
                    activeTab === 'url'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  Enter URL
                </button>
              </div>

              {/* Text Tab */}
              {activeTab === 'text' && (
                <textarea
                  value={formData.textContent}
                  onChange={e => setFormData(prev => ({ ...prev, textContent: e.target.value }))}
                  placeholder="Paste one or more blog posts or content samples..."
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono text-sm"
                  rows={8}
                />
              )}

              {/* URL Tab */}
              {activeTab === 'url' && (
                <input
                  type="url"
                  value={formData.urlContent}
                  onChange={e => setFormData(prev => ({ ...prev, urlContent: e.target.value }))}
                  placeholder="https://example.com/blog-post"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              )}
            </div>

            {/* Service Area Override */}
            <div>
              <label htmlFor="serviceArea" className="block text-sm font-medium text-slate-300 mb-2">
                Service Area (Override)
              </label>
              <input
                type="text"
                id="serviceArea"
                value={formData.serviceArea}
                onChange={e => setFormData(prev => ({ ...prev, serviceArea: e.target.value }))}
                placeholder="e.g., Denver Metro, Colorado"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Off-Limits Topics */}
            <div>
              <label htmlFor="offLimitTopics" className="block text-sm font-medium text-slate-300 mb-2">
                Off-Limits Topics (comma-separated)
              </label>
              <textarea
                id="offLimitTopics"
                value={formData.offLimitTopics}
                onChange={e => setFormData(prev => ({ ...prev, offLimitTopics: e.target.value }))}
                placeholder="e.g., competitors, lawsuits"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                rows={3}
              />
            </div>

            {/* Regenerate Checkbox */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="regenerate"
                checked={formData.regenerate}
                onChange={e => setFormData(prev => ({ ...prev, regenerate: e.target.checked }))}
                className="w-4 h-4 bg-slate-700 border-slate-600 rounded"
              />
              <label htmlFor="regenerate" className="ml-2 text-sm text-slate-300">
                Regenerate reference files (if already onboarded)
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-medium rounded transition-colors"
            >
              {loading ? 'Starting Onboarding...' : 'Start Onboarding'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
