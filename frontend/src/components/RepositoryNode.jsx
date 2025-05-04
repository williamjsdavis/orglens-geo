import React from 'react';
import { Handle, Position } from '@xyflow/react';
import CustomTooltipContent from './CustomTooltipContent';

const RepositoryNode = ({ data }) => {
  const nodeWidth = 220;
  const nodeHeight = 150;

  return (
    // The main div remains the group parent
    <div
      className="repository-node group relative bg-white border border-gray-300 rounded-lg shadow-md transition-all hover:shadow-lg flex flex-col h-full text-sm"
      style={{ width: nodeWidth, height: nodeHeight }}
    >
      {/* Node Content Wrapper */}
      <div className="p-4 flex flex-col flex-grow">
        {/* Handles with IDs */}
        <Handle type="target" position={Position.Bottom} className="!w-2 !h-2 !bg-gray-400 !rounded-full !border-none" />

        <h3 className="text-base font-semibold truncate mb-1.5" title={data.name}>{data.name}</h3>
        <p className="text-sm text-gray-700 flex-grow overflow-hidden line-clamp-4 mb-2">
          {data.summary || 'No description available.'}
        </p>
        <div className="flex justify-between items-center mt-auto pt-2 border-t border-gray-200">
          <div className="text-xs text-blue-700 font-medium">Repository</div>

        </div>
      </div>

    </div>
  );
};

export default RepositoryNode;