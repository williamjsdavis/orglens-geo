// src/pages/ContributorDetail.js
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useData } from '../context/DataContext';

export default function ContributorDetail() {
  const { contributorId } = useParams(); // Get contributorId from URL
  const { contributors, repositories, isLoading, error } = useData(); // Also get repositories to link work items

  if (isLoading) {
    return <div className="text-center py-10">Loading Contributor Details...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error loading contributor data: {error}</div>;
  }

  // Find the specific contributor
  // Ensure contributorId is treated as a number
  const contributor = contributors.find(c => c.id === parseInt(contributorId, 10));

  if (!contributor) {
    return (
       <div className="text-center py-10">
            <p>Contributor not found.</p>
            <Link to="/contributors" className="text-blue-600 hover:underline mt-4 inline-block">Back to Contributors</Link>
        </div>
    );
  }

  // Helper to find repo name by ID
  const getRepoName = (repoId) => {
    const repo = repositories.find(r => r.id === repoId);
    return repo ? repo.name : 'Unknown Repository';
  };

  return (
    <div>
      <div className="flex items-center mb-4 gap-x-4">
        <img src={contributor.avatar_url} alt={`${contributor.username} avatar`} className="size-16 rounded-full bg-gray-100" />
        <div>
          <h2 className="text-2xl font-semibold">{contributor.username}</h2>
           <a href={contributor.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{contributor.url}</a>
        </div>
      </div>

      <p className="text-gray-700 mb-6">{contributor.summary}</p>

      <h3 className="text-lg font-semibold mb-3 border-t pt-4">Work Contributions</h3>
      {contributor.works && contributor.works.length > 0 ? (
         contributor.works.map(work => (
            <div key={work.id} className="mb-4 p-3 border rounded bg-gray-50">
                <h4 className="font-semibold">
                    In Repository: {' '}
                    <Link to={`/repositories/${work.repository}`} className="text-blue-700 hover:underline">
                         {getRepoName(work.repository)}
                    </Link>
                </h4>
                <p className="text-sm text-gray-600 mt-1 mb-2">{work.summary}</p>
                {/* Optionally list issues/commits - keeping it simple for now */}
                {/* Example: <p className="text-xs">Issues: {work.issues.length}, Commits: {work.commits.length}</p> */}
            </div>
         ))
      ) : (
        <p>No specific work items listed for this contributor.</p>
      )}


      <div className="mt-6">
        <Link to="/contributors" className="text-blue-600 hover:underline">← Back to Contributors</Link>
      </div>
    </div>
  );
}