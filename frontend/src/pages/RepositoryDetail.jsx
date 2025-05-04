// src/pages/RepositoryDetail.js
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useData } from '../context/DataContext';

export default function RepositoryDetail() {
  const { repoId } = useParams(); // Get repoId from URL
  const { repositories, isLoading, error } = useData();

  if (isLoading) {
    return <div className="text-center py-10">Loading Repository Details...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error loading repository data: {error}</div>;
  }

  // Find the specific repository
  // Ensure repoId is treated as a number for comparison if IDs are numbers
  const repository = repositories.find(repo => repo.id === parseInt(repoId, 10));

  if (!repository) {
    return (
        <div className="text-center py-10">
            <p>Repository not found.</p>
            <Link to="/repositories" className="text-blue-600 hover:underline mt-4 inline-block">Back to Repositories</Link>
        </div>
    );
  }

  return (
    <div>
      <h2 className="text-xl font-semibold mb-2">{repository.name}</h2>
      <p className="text-gray-700 mb-4">{repository.summary}</p>
      <p><span className="font-semibold">URL:</span> <a href={repository.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{repository.url}</a></p>
      <p><span className="font-semibold">Created:</span> {new Date(repository.created_at).toLocaleDateString()}</p>
      <p><span className="font-semibold">Last Updated:</span> {new Date(repository.updated_at).toLocaleDateString()}</p>

      {/* Add more details (like contributors to this repo) later */}
      <div className="mt-6">
        <Link to="/repositories" className="text-blue-600 hover:underline">← Back to Repositories</Link>
      </div>
    </div>
  );
}