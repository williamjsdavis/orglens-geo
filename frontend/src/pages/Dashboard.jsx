import React from 'react';
import { useData } from '../context/DataContext';
import OrganizationGraph from '../components/OrganizationGraph';

export default function Dashboard() {
  const { isLoading, error, contributors, repositories, } = useData(); 


  if (isLoading) {
    return <div className="text-center py-10">Loading Dashboard...</div>;
  }

  if (error) {
    return <div className="text-center py-10 text-red-600">Error loading data: {error}</div>;
  }

  return (
    <div className="px-4">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold">Organization Overview</h2>
        <div className="text-sm text-gray-500">
          {repositories?.length || 0} Repositories • 
          {contributors?.length || 0} Contributors
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-5 mb-6">
        <OrganizationGraph contributors={contributors} repositories={repositories} />
      </div>
      
    </div>
  );
}