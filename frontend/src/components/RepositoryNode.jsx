import React from 'react';
import { Handle, Position } from '@xyflow/react';

// ... languageColors definition ...
const languageColors = {
  JavaScript: '#f1e05a',
  TypeScript: '#3178c6',
  Python: '#3572A5',
  Java: '#b07219',
  Go: '#00ADD8',
  Ruby: '#701516',
  PHP: '#4F5D95',
  C: '#555555',
  'C++': '#f34b7d',
  'C#': '#178600',
  HTML: '#e34c26',
  CSS: '#563d7c',
  Shell: '#89e051',
  default: '#6c757d'
};


const RepositoryNode = ({ data }) => {
  const handleMouseOver = (event) => {
    if (data.onNodeHover) {
      data.onNodeHover({
        id: data.id,
        name: data.name,
        url: data.url,
        summary: data.summary,
        language: data.language,
        type: 'repository'
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
      className="repository-node bg-white border border-gray-300 rounded-lg shadow-md p-3 transition-all hover:shadow-lg flex flex-col h-full text-sm" // Adjusted padding and base text size
      onMouseOver={handleMouseOver}
      onMouseLeave={handleMouseLeave} // Use the new handler
      style={{ width: 180, height: 120 }} // Ensure style matches graph definition
    >
      {/* Use invisible handles for better connection points */}
      <Handle type="target" position={Position.Left} className="!w-1 !h-full !rounded-none !bg-transparent !border-none" />
      <Handle type="source" position={Position.Right} className="!w-1 !h-full !rounded-none !bg-transparent !border-none" />

      <div className="flex items-center mb-1.5"> {/* Adjusted margin */}
        <div
          className="w-2.5 h-2.5 rounded-full mr-1.5 flex-shrink-0" // Adjusted size/margin
          style={{ backgroundColor: languageColors[data.language] || languageColors.default }}
        />
        <span className="text-xs text-gray-600 truncate">{data.language || 'N/A'}</span>
      </div>

      <h3 className="text-sm font-semibold truncate mb-1" title={data.name}>{data.name}</h3> {/* Use title for full name */}

      <p className="text-xs text-gray-700 flex-grow overflow-hidden line-clamp-3 mb-1.5"> {/* Allow 3 lines, adjusted margin */}
        {data.summary || 'No description available.'}
      </p>

      <div className="flex justify-between items-center mt-auto pt-1.5 border-t border-gray-200"> {/* Adjusted padding/border */}
        <div className="text-xs text-blue-700 font-medium">Repository</div>
        {/* Optional: Add an icon or indicator if needed */}
      </div>
    </div>
  );
};

export default RepositoryNode;