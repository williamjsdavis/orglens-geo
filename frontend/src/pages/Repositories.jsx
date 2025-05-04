// src/pages/Repositories.js
import React from 'react';
import { Link } from 'react-router-dom';
import { useData } from '../context/DataContext';

export default function Repositories() {
  const { repositories, isLoading, error } = useData();

  if (isLoading) {
    return <div className="text-center py-10">Loading Repositories...</div>;
  }

   if (error) {
    return <div className="text-center py-10 text-red-600">Error loading repositories: {error}</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Repositories</h2>
      {repositories.length === 0 ? (
        <p>No repositories found.</p>
      ) : (
        <ul>
          {repositories.map(repo => (
            <li key={repo.id} className="border-b py-2">
              <Link to={`/repositories/${repo.id}`} className="text-blue-600 hover:underline">
                {repo.name}
              </Link>
              <p className="text-sm text-gray-600">{repo.summary}</p>
              <span className="text-xs text-gray-500">{repo.language}</span>
            </li>
          ))}
        </ul>
      )}
      {/* Add list display logic later (e.g., using the second example UI you provided) */}
    </div>
  );
}