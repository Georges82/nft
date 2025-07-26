import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPanel = () => {
  const [adminSecret, setAdminSecret] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [certificates, setCertificates] = useState([]);
  const [newCertificate, setNewCertificate] = useState({
    client_name: '',
    client_email: '',
    expires_days: 365
  });
  const [generatedCertificate, setGeneratedCertificate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const authenticateAdmin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Test admin authentication
      const response = await axios.get(`${API}/admin/certificates`, {
        headers: { Authorization: `Bearer ${adminSecret}` }
      });
      
      setIsAuthenticated(true);
      setCertificates(response.data.certificates);
    } catch (err) {
      setError('Invalid admin secret. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const generateCertificate = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API}/admin/generate-certificate`, newCertificate, {
        headers: { Authorization: `Bearer ${adminSecret}` }
      });

      setGeneratedCertificate(response.data);
      setNewCertificate({ client_name: '', client_email: '', expires_days: 365 });
      
      // Refresh certificates list
      const certsResponse = await axios.get(`${API}/admin/certificates`, {
        headers: { Authorization: `Bearer ${adminSecret}` }
      });
      setCertificates(certsResponse.data.certificates);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Error generating certificate');
    } finally {
      setLoading(false);
    }
  };

  const revokeCertificate = async (certificateId) => {
    if (!confirm('Are you sure you want to revoke this certificate?')) return;

    try {
      await axios.post(`${API}/admin/revoke-certificate?certificate_id=${certificateId}`, {}, {
        headers: { Authorization: `Bearer ${adminSecret}` }
      });

      // Refresh certificates list
      const response = await axios.get(`${API}/admin/certificates`, {
        headers: { Authorization: `Bearer ${adminSecret}` }
      });
      setCertificates(response.data.certificates);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Error revoking certificate');
    }
  };

  const copyCertificate = (certificate) => {
    navigator.clipboard.writeText(certificate);
    alert('Certificate copied to clipboard!');
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-indigo-600 rounded-lg flex items-center justify-center">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Admin Panel
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Certificate Management System
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <form onSubmit={authenticateAdmin}>
              <div>
                <label htmlFor="adminSecret" className="block text-sm font-medium text-gray-700">
                  Admin Secret
                </label>
                <div className="mt-1">
                  <input
                    id="adminSecret"
                    type="password"
                    value={adminSecret}
                    onChange={(e) => setAdminSecret(e.target.value)}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Enter admin secret"
                    required
                  />
                </div>
              </div>

              {error && (
                <div className="mt-4 rounded-md bg-red-50 p-4">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <div className="mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {loading ? 'Authenticating...' : 'Access Admin Panel'}
                </button>
              </div>
            </form>

            <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
              <p className="text-sm text-yellow-700">
                <strong>Default Admin Secret:</strong> joinery_admin_2024_secret_key
              </p>
              <p className="text-xs text-yellow-600 mt-1">
                Change this in your .env file for production use.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
              <p className="text-sm text-gray-600">Manage client certificates</p>
            </div>
            <button
              onClick={() => setIsAuthenticated(false)}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Generate Certificate Form */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Generate New Client Certificate</h2>
          
          <form onSubmit={generateCertificate} className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Client Name</label>
              <input
                type="text"
                value={newCertificate.client_name}
                onChange={(e) => setNewCertificate({...newCertificate, client_name: e.target.value})}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Client Email</label>
              <input
                type="email"
                value={newCertificate.client_email}
                onChange={(e) => setNewCertificate({...newCertificate, client_email: e.target.value})}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Expires In (Days)</label>
              <input
                type="number"
                value={newCertificate.expires_days}
                onChange={(e) => setNewCertificate({...newCertificate, expires_days: parseInt(e.target.value)})}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                min="1"
                max="3650"
              />
            </div>
            
            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-md font-medium transition-colors disabled:opacity-50"
              >
                {loading ? 'Generating...' : 'Generate Certificate'}
              </button>
            </div>
          </form>
        </div>

        {/* Generated Certificate Display */}
        {generatedCertificate && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-medium text-green-900 mb-4">Certificate Generated Successfully!</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-green-700"><strong>Client:</strong> {generatedCertificate.client_name}</p>
                <p className="text-sm text-green-700"><strong>Email:</strong> {generatedCertificate.client_email}</p>
                <p className="text-sm text-green-700"><strong>Expires:</strong> {new Date(generatedCertificate.expires_at).toLocaleDateString()}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-green-800 mb-2">Certificate (share this with your client):</label>
                <div className="relative">
                  <textarea
                    readOnly
                    value={generatedCertificate.certificate}
                    className="w-full h-32 p-3 border border-green-300 rounded-md bg-white font-mono text-xs"
                  />
                  <button
                    onClick={() => copyCertificate(generatedCertificate.certificate)}
                    className="absolute top-2 right-2 bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs"
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Certificates List */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Active Certificates</h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Client</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issued</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Expires</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {certificates.map((cert) => (
                  <tr key={cert.certificate_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {cert.client_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cert.client_email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(cert.issued_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(cert.expires_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        cert.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {cert.is_active ? 'Active' : 'Revoked'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {cert.is_active && (
                        <button
                          onClick={() => revokeCertificate(cert.certificate_id)}
                          className="text-red-600 hover:text-red-900 mr-4"
                        >
                          Revoke
                        </button>
                      )}
                      <button
                        onClick={() => copyCertificate(cert.signed_certificate)}
                        className="text-indigo-600 hover:text-indigo-900"
                      >
                        Copy Certificate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {certificates.length === 0 && (
              <div className="text-center py-12">
                <p className="text-sm text-gray-500">No certificates generated yet.</p>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;