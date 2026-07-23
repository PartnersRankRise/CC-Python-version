'use client';

// Created: Thursday Jul 23, 2026, 2:54 PM (UTC-6)
// Last edited: Thursday Jul 23, 2026, 2:54 PM (UTC-6)

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

interface ClientData {
  id: string;
  name: string;
  website_url: string | null;
  industry: string | null;
  service_area: string | null;
  onboarding_state: string;
  created_at: string;
}

interface OnboardingStatus {
  client_id: string;
  client_state: string;
  validation_status: {
    style_reference_card: { exists: boolean; all_present: boolean };
    audience_profile: { exists: boolean; all_present: boolean };
    brand_notes: { exists: boolean };
    brand_colors: { extracted: boolean; count: number; all_11_valid: boolean };
  };
  last_updated: string;
}

export default function ClientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const clientId = params.clientId as string;
  const showSuccessToast = searchParams.get('onboarding') === 'success';

  const [client, setClient] = useState<ClientData | null>(null);
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showRegenerateDialog, setShowRegenerateDialog] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch client details
        const clientResponse = await fetch(`/api/clients/${clientId}`);
        if (!clientResponse.ok) throw new Error('Failed to fetch client');
        const clientData = await clientResponse.json();
        setClient(clientData);

        // Fetch onboarding status
        const statusResponse = await fetch(`/api/clients/${clientId}/onboarding/status`);
        if (!statusResponse.ok) throw new Error('Failed to fetch status');
        const statusData = await statusResponse.json();
        setStatus(statusData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [clientId]);

  const getStateLabel = (state: string) => {
    switch (state) {
      case 'new':
        return 'New';
      case 'partial':
        return 'Partially Onboarded';
      case 'fully_onboarded':
        return 'Ready';
      default:
        return state;
    }
  };

  const getStateBadgeColor = (state: string) => {
    switch (state) {
      case 'new':
        return 'bg-slate-900/30 border-slate-700 text-slate-300';
      case 'partial':
        return 'bg-yellow-900/30 border-yellow-700 text-yellow-300';
      case 'fully_onboarded':
        return 'bg-green-900/30 border-green-700 text-green-300';
      default:
        return 'bg-slate-900/30 border-slate-700 text-slate-300';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center text-slate-400">Loading...</div>
        </div>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-900/20 border border-red-700 rounded p-4 text-red-300">
            {error || 'Client not found'}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Success Toast */}
        {showSuccessToast && (
          <div className="mb-4 bg-green-900/30 border border-green-700 rounded p-4 text-green-300 flex items-center justify-between">
            <span>Onboarding completed successfully!</span>
            <button
              onClick={() => window.history.replaceState({}, '', `/clients/${clientId}`)}
              className="text-green-400 hover:text-green-300"
            >
              ×
            </button>
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <Link href="/clients" className="text-blue-400 hover:text-blue-300 text-sm mb-4 inline-block">
            ← Back to Clients
          </Link>
          <h1 className="text-3xl font-bold text-white mb-2">{client.name}</h1>
          <p className="text-slate-400">Client ID: {clientId}</p>
        </div>

        {/* Client Info Card */}
        <div className="bg-slate-800 rounded-lg shadow-lg p-6 border border-slate-700 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Industry</label>
              <p className="text-white">{client.industry || '—'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1">Service Area</label>
              <p className="text-white">{client.service_area || '—'}</p>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-400 mb-1">Website</label>
              {client.website_url ? (
                <a
                  href={client.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 underline"
                >
                  {client.website_url}
                </a>
              ) : (
                <p className="text-slate-500">—</p>
              )}
            </div>
          </div>
        </div>

        {/* Onboarding Status Card */}
        {status && (
          <div className="bg-slate-800 rounded-lg shadow-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Onboarding Status</h2>
              <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getStateBadgeColor(status.client_state)}`}>
                {getStateLabel(status.client_state)}
              </div>
            </div>

            {/* Progress Indicators */}
            <div className="space-y-4 mb-6">
              {/* Style Reference Card */}
              <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded">
                <div>
                  <p className="font-medium text-white">Style Reference Card</p>
                  <p className="text-xs text-slate-400 mt-1">Brand voice, visual guidelines</p>
                </div>
                <div className="flex items-center gap-2">
                  {status.validation_status.style_reference_card.exists ? (
                    <span className="text-green-400">✓</span>
                  ) : (
                    <span className="text-slate-500">○</span>
                  )}
                  <span className={status.validation_status.style_reference_card.exists ? 'text-green-400' : 'text-slate-500'}>
                    {status.validation_status.style_reference_card.exists ? 'Ready' : 'Pending'}
                  </span>
                </div>
              </div>

              {/* Audience Profile */}
              <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded">
                <div>
                  <p className="font-medium text-white">Audience Profile</p>
                  <p className="text-xs text-slate-400 mt-1">Demographics, expertise, pain points</p>
                </div>
                <div className="flex items-center gap-2">
                  {status.validation_status.audience_profile.exists ? (
                    <span className="text-green-400">✓</span>
                  ) : (
                    <span className="text-slate-500">○</span>
                  )}
                  <span className={status.validation_status.audience_profile.exists ? 'text-green-400' : 'text-slate-500'}>
                    {status.validation_status.audience_profile.exists ? 'Ready' : 'Pending'}
                  </span>
                </div>
              </div>

              {/* Brand Notes */}
              <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded">
                <div>
                  <p className="font-medium text-white">Brand Notes</p>
                  <p className="text-xs text-slate-400 mt-1">Publishing specs, authority signals</p>
                </div>
                <div className="flex items-center gap-2">
                  {status.validation_status.brand_notes.exists ? (
                    <span className="text-green-400">✓</span>
                  ) : (
                    <span className="text-slate-500">○</span>
                  )}
                  <span className={status.validation_status.brand_notes.exists ? 'text-green-400' : 'text-slate-500'}>
                    {status.validation_status.brand_notes.exists ? 'Ready' : 'Pending'}
                  </span>
                </div>
              </div>

              {/* Brand Colors */}
              {status.validation_status.brand_colors.extracted && (
                <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded">
                  <div>
                    <p className="font-medium text-white">Brand Colors</p>
                    <p className="text-xs text-slate-400 mt-1">
                      {status.validation_status.brand_colors.count}/11 colors extracted
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {status.validation_status.brand_colors.all_11_valid ? (
                      <span className="text-green-400">✓</span>
                    ) : (
                      <span className="text-yellow-400">⚠</span>
                    )}
                    <span className={status.validation_status.brand_colors.all_11_valid ? 'text-green-400' : 'text-yellow-400'}>
                      {status.validation_status.brand_colors.all_11_valid ? 'Valid' : 'Partial'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t border-slate-600">
              {status.client_state === 'new' || status.client_state === 'partial' ? (
                <Link
                  href={`/clients/${clientId}/onboard`}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition-colors text-center"
                >
                  Continue Onboarding
                </Link>
              ) : (
                <button
                  onClick={() => setShowRegenerateDialog(true)}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded transition-colors"
                >
                  Regenerate Reference Files
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Regenerate Dialog */}
      {showRegenerateDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-lg shadow-xl border border-slate-700 max-w-md w-full p-6">
            <h3 className="text-lg font-bold text-white mb-4">Regenerate Reference Files?</h3>
            <p className="text-slate-300 mb-6">
              This will overwrite existing reference files (Style Reference Card, Audience Profile, Brand Notes) with new versions.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowRegenerateDialog(false)}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded transition-colors"
              >
                Cancel
              </button>
              <Link
                href={`/clients/${clientId}/onboard?regenerate=true`}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition-colors text-center"
              >
                Regenerate
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
