// Created: Thursday Jul 23, 2026, 12:00 PM (UTC-6)
// Last edited: Thursday Jul 23, 2026, 12:00 PM (UTC-6)

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Content Pipeline</h1>
          <div className="flex items-center gap-3">
            <span className="inline-block px-3 py-1 bg-blue-500 text-white text-sm font-semibold rounded-full">
              Phase 1 — Foundation
            </span>
            <p className="text-gray-600">Multi-client blog production platform</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Clients Section */}
          <div className="md:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Clients</h2>
            <div className="flex items-center justify-center min-h-[200px]">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-3"></div>
                <p className="text-gray-500">Loading...</p>
              </div>
            </div>
          </div>

          {/* Status Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Status</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-500 mb-1">Phase</p>
                <p className="text-base font-medium text-gray-900">Phase 1 — Foundation</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Backend</p>
                <p className="text-base font-medium text-green-600">✓ Ready</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Frontend</p>
                <p className="text-base font-medium text-green-600">✓ Ready</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">0</p>
            <p className="text-sm text-gray-500 mt-1">Clients</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">0</p>
            <p className="text-sm text-gray-500 mt-1">Runs</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">0</p>
            <p className="text-sm text-gray-500 mt-1">Articles</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">—</p>
            <p className="text-sm text-gray-500 mt-1">Status</p>
          </div>
        </div>
      </div>
    </div>
  );
}
