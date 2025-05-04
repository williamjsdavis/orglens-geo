import React from 'react';
import { Handle, Position } from '@xyflow/react';

const ContributorNode = ({ data }) => {
  const handleMouseOver = (event) => {
    if (data.onNodeHover) {
      // Calculate issue and commit counts
      let issueCount = 0;
      let commitCount = 0;

      if (data.works) {
        data.works.forEach(work => {
          issueCount += work.issues?.length || 0;
          commitCount += work.commits?.length || 0;
        });
      }

      data.onNodeHover({
        id: data.id,
        name: data.username,
        url: data.url,
        avatar: data.avatar_url,
        summary: data.summary,
        works: data.works,
        type: 'contributor',
        issueCount,
        commitCount
      }, event); // Pass the event object
    }
  };

   const handleMouseLeave = () => {
     if (data.onNodeHover) {
        data.onNodeHover(null); // Clear hover state
     }
  };

  return (
    <div
      className="contributor-node bg-gradient-to-r from-green-50 to-blue-50 border border-gray-200 rounded-lg shadow-sm p-3 transition-all hover:shadow-md flex items-center" // Ensure padding and flex
      onMouseOver={handleMouseOver}
      onMouseLeave={handleMouseLeave} // Use the new handler
      style={{ width: 150, height: 60 }} // Adjusted height to better fit content
    >
      {/* Use invisible handles for better connection points */}
       <Handle type="target" position={Position.Left} className="!w-1 !h-full !rounded-none !bg-transparent !border-none" />
       <Handle type="source" position={Position.Right} className="!w-1 !h-full !rounded-none !bg-transparent !border-none" />


      {data.avatar_url ? (
        <img
          src={data.avatar_url}
          alt={data.username}
          className="w-9 h-9 rounded-full border border-gray-300 shadow-sm flex-shrink-0" // Slightly smaller, adjusted border
        />
      ) : (
        <div className="w-9 h-9 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-medium text-sm flex-shrink-0"> {/* Adjusted styles */}
          {data.username ? data.username.substring(0, 1).toUpperCase() : '?'}
        </div>
      )}

      <div className="ml-2.5 overflow-hidden"> {/* Adjusted margin, added overflow hidden */}
        <h4 className="text-sm font-medium truncate" title={data.username}>{data.username}</h4> {/* Use title for full name */}
        <p className="text-xs text-emerald-700">Contributor</p> {/* Darker text */}
      </div>
    </div>
  );
};

export default ContributorNode;