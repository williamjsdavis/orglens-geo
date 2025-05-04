/* eslint-disable no-unused-vars */
import React, { useCallback, useMemo, useState, useRef, useEffect } from 'react'; // Added useRef, useEffect
import  { ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Position,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css'
import RepositoryNode from './RepositoryNode';
import ContributorNode from './ContributorNode';
import CustomTooltip from './CustomTooltip';

// Define custom node types
const nodeTypes = {
  repository: RepositoryNode,
  contributor: ContributorNode,
};

const OrganizationGraph = ({ repositories, contributors }) => {
  const [hoveredElement, setHoveredElement] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const graphContainerRef = useRef(null); // Ref for the graph container

  const handleNodeHover = useCallback((node, event) => {
    if (node && event && graphContainerRef.current) {
      const containerRect = graphContainerRef.current.getBoundingClientRect();
      // Calculate position relative to the container
      const x = event.clientX - containerRect.left;
      const y = event.clientY - containerRect.top;
      setHoveredElement(node);
      setTooltipPosition({ x, y });
    } else {
      setHoveredElement(null);
    }
  }, []); // Removed graphContainerRef from dependencies as it's stable

  // Process data for React Flow
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes = [];
    const edges = [];
    const center = { x: 400, y: 300 }; // Define center point

    // Calculate positions for layout
    const repoRadius = 150; // Give repositories a radius to spread them
    const contributorRadius = 350; // Increase contributor radius slightly
    const repoCount = repositories.length;
    const contributorCount = contributors.length;

    // Add repository nodes in a smaller circle
    repositories.forEach((repo, index) => {
      const angle = (index / repoCount) * 2 * Math.PI;
      // Offset slightly if only one repo to avoid exact center
      const radius = repoCount > 1 ? repoRadius : 50;
      const x = center.x + radius * Math.cos(angle);
      const y = center.y + radius * Math.sin(angle);

      nodes.push({
        id: `repo-${repo.id}`,
        type: 'repository',
        data: {
          ...repo,
          onNodeHover: handleNodeHover,
        },
        position: { x, y },
        style: { width: 180, height: 120 }
      });
    });


    // Add contributor nodes around repos in a circular pattern
    contributors.forEach((contributor, index) => {
      const angle = (index / contributorCount) * 2 * Math.PI;
      const x = center.x + contributorRadius * Math.cos(angle);
      const y = center.y + contributorRadius * Math.sin(angle);

      nodes.push({
        id: `user-${contributor.id}`,
        type: 'contributor',
        data: {
          ...contributor,
          onNodeHover: handleNodeHover,
        },
        position: { x, y },
        style: { width: 150, height: 80 }
      });

      // Create edges between contributors and repositories
      contributor.works.forEach(work => {
        // Ensure the target repository exists before creating an edge
        if (repositories.some(repo => `repo-${repo.id}` === `repo-${work.repository}`)) {
            edges.push({
              id: `edge-${contributor.id}-${work.repository}`,
              source: `user-${contributor.id}`,
              target: `repo-${work.repository}`,
              // animated: true, // Remove or keep based on preference
              type: 'smoothstep', // Use smoothstep edges
              style: { stroke: '#9ca3af', strokeWidth: 1.5 }, // Adjusted style
              markerEnd: {
                type: MarkerType.ArrowClosed,
                width: 15, // Adjusted size
                height: 15,
                color: '#6b7280', // Adjusted color
              },
              data: {
                commits: work.commits?.length || 0,
                issues: work.issues?.length || 0,
              },
            });
        }
      });
    });

    return { initialNodes: nodes, initialEdges: edges };
  }, [repositories, contributors, handleNodeHover]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);


  // Recalculate nodes and edges if props change
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);


  const onInit = useCallback((reactFlowInstance) => {
    // Fit view on initial load
     setTimeout(() => reactFlowInstance.fitView({ padding: 0.1, duration: 300 }), 50);
  }, []);

  return (
    // Added ref to the container div
    <div ref={graphContainerRef} className="graph-container relative w-full h-[600px] rounded-lg bg-gradient-to-br from-slate-50 to-blue-50 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onInit={onInit}
        fitView
        fitViewOptions={{ padding: 0.1 }} // Add padding on fitView
        minZoom={0.1} // Allow zooming out further
        maxZoom={2}
        // defaultZoom={0.8} // Remove defaultZoom to rely on fitView
        attributionPosition="bottom-right"
      >
        <Background color="#e0e0e0" gap={20} size={1.5} />
        <Controls />
        <MiniMap
          nodeStrokeWidth={3}
          zoomable
          pannable
          nodeColor={(node) => {
            if (node.type === 'repository') return '#60a5fa'; // Lighter blue
            return '#34d399'; // Lighter green
          }}
          style={{ backgroundColor: 'rgba(241, 245, 249, 0.8)' }} // Slightly transparent background
          maskColor="rgba(203, 213, 225, 0.6)" // Softer mask color
        />
      </ReactFlow>
      {hoveredElement && (
        <CustomTooltip
          content={hoveredElement}
          position={tooltipPosition}
          // onClose is not defined in CustomTooltip props, removed for now
        />
      )}
    </div>
  );
};

export default OrganizationGraph;