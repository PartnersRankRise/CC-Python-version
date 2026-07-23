'use client';

// Created: Thursday Jul 23, 2026, 2:44 PM (UTC-6)
// Last edited: Thursday Jul 23, 2026, 2:44 PM (UTC-6)

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface ClientFormData {
  name: string;
  industry: string;
  website_url: string;
  service_area: string;
}

export default function NewClientPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<ClientFormData>({
    name: '',
    industry: '',
    website_url: '',
    service_area: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const industries = [
    'Home Services',
    'Health & Wellness',
    'Legal Services',
    'Financial Advisory',
    'Software Development',
  ];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // POST /clients
      const response = await fetch('/api/clients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          industry: formData.industry || undefined,
          website_url: formData.website_url || undefined,
          service_area: formData.service_area || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create client');
      }

      const client = await response.json();

      // Redirect to onboarding page
      router.push(`/clients/${client.id}/onboard`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-4">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/clients" className="text-blue-400 hover:text-blue-300 text-sm mb-4 inline-block">
            ← Back to Clients
          </Link>
          <h1 className="text-3xl font-bold text-white mb-2">Add New Client</h1>
          <p className="text-slate-300">Create a new client profile to get started.</p>
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

            {/* Client Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-2">
                Client Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="e.g., Acme HVAC Services"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Industry */}
            <div>
              <label htmlFor="industry" className="block text-sm font-medium text-slate-300 mb-2">
                Industry <span className="text-red-400">*</span>
              </label>
              <select
                id="industry"
                name="industry"
                value={formData.industry}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Select an industry...</option>
                {industries.map(industry => (
                  <option key={industry} value={industry}>
                    {industry}
                  </option>
                ))}
              </select>
            </div>

            {/* Website URL */}
            <div>
              <label htmlFor="website_url" className="block text-sm font-medium text-slate-300 mb-2">
                Website URL
              </label>
              <input
                type="url"
                id="website_url"
                name="website_url"
                value={formData.website_url}
                onChange={handleChange}
                placeholder="https://example.com"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Service Area */}
            <div>
              <label htmlFor="service_area" className="block text-sm font-medium text-slate-300 mb-2">
                Service Area
              </label>
              <input
                type="text"
                id="service_area"
                name="service_area"
                value={formData.service_area}
                onChange={handleChange}
                placeholder="e.g., Denver Metro, Colorado"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-medium rounded transition-colors"
            >
              {loading ? 'Creating...' : 'Create Client & Continue'}
            </button>
          </form>
        </div>

        {/* Help Text */}
        <div className="mt-6 text-slate-400 text-sm">
          <p>Required fields marked with <span className="text-red-400">*</span></p>
        </div>
      </div>
    </div>
  );
}
